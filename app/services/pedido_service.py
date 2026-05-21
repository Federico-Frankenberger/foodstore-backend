import json
from decimal import Decimal
from typing import List, Optional

from app.models.pedido import Pedido
from app.schemas.pedido import (
    AvanzarEstadoBody,
    DetallePedidoPublico,
    HistorialEstadoPublico,
    MetricasResumen,
    PedidoCrear,
    PedidoPublico,
)
from app.uow.uow import UnidadDeTrabajo

FSM_TRANSICIONES: dict[str, set[str]] = {
    "PENDIENTE":  {"CONFIRMADO", "CANCELADO"},
    "CONFIRMADO": {"EN_PREPARACION",    "CANCELADO"},
    "EN_PREPARACION":    {"EN_CAMINO",  "CANCELADO"},
    "EN_CAMINO":  {"ENTREGADO",  "CANCELADO"},
    "ENTREGADO":  set(),
    "CANCELADO":  set(),
}

CANCELAR_REQUIERE_PRIVILEGIO = {"CONFIRMADO", "EN_PREPARACION", "EN_CAMINO"}
ESTADOS_CON_STOCK_DESCONTADO = {"PENDIENTE", "CONFIRMADO", "EN_PREPARACION"}


def _obtener_precio_venta(producto) -> Decimal:
    if bool(producto.ingredientes_link):
        from app.services.producto_service import _calcular_metricas
        _, _, precio = _calcular_metricas(producto.ingredientes_link, producto.margen_ganancia)
        return precio
    precio_base = producto.precio_base if producto.precio_base is not None else Decimal("0.00")
    return (precio_base * (1 + producto.margen_ganancia / 100)).quantize(Decimal("0.01"))


def _restaurar_stock_pedido(pedido: Pedido, uow) -> None:
    for detalle in pedido.detalles:
        if not detalle.producto:
            continue
        producto = detalle.producto
        if bool(producto.ingredientes_link):
            for link in producto.ingredientes_link:
                uow.ingredientes.restaurar_stock(link.ingrediente_id, link.cantidad * detalle.cantidad)
        else:
            stock_actual = producto.stock_directo if producto.stock_directo is not None else 0
            uow.productos.actualizar(producto, {"stock_directo": stock_actual + detalle.cantidad})


def _serializar_direccion(direccion) -> str:
    return json.dumps({
        "alias": direccion.alias,
        "linea1": direccion.linea1,
        "linea2": direccion.linea2,
        "ciudad": direccion.ciudad,
        "provincia": direccion.provincia,
        "codigo_postal": direccion.codigo_postal,
    }, ensure_ascii=False)


def _construir_pedido_publico(pedido: Pedido, uow) -> PedidoPublico:
    items = [
        DetallePedidoPublico(
            producto_id=d.producto_id,
            nombre_snapshot=d.nombre_snapshot,
            precio_snapshot=d.precio_snapshot,
            cantidad=d.cantidad,
            subtotal_snap=d.subtotal_snap,
            personalizacion=d.personalizacion or [],
        )
        for d in pedido.detalles
    ]
    historial = [
        HistorialEstadoPublico(
            estado_desde=h.estado_desde,
            estado_hasta=h.estado_hasta,
            usuario_id=h.usuario_id,
            motivo=h.motivo,
            created_at=h.created_at,
        )
        for h in pedido.historial
    ]
    return PedidoPublico(
        id=pedido.id,
        usuario_id=pedido.usuario_id,
        direccion_id=pedido.direccion_id,
        direccion_snapshot=pedido.direccion_snapshot,
        estado_codigo=pedido.estado_codigo,
        forma_pago_codigo=pedido.forma_pago_codigo,
        subtotal=pedido.subtotal,
        descuento=pedido.descuento,
        costo_envio=pedido.costo_envio,
        total=pedido.total,
        notas=pedido.notas,
        created_at=pedido.created_at,
        items=items,
        historial=historial,
    )


def crear_pedido(datos: PedidoCrear, usuario_id: int) -> PedidoPublico:
    with UnidadDeTrabajo() as uow:
        forma_pago = uow.formas_pago.obtener_por_codigo(datos.forma_pago_codigo)
        if not forma_pago or not forma_pago.habilitado:
            raise ValueError(f"Forma de pago '{datos.forma_pago_codigo}' no válida o deshabilitada")

        direccion_snapshot = None
        if datos.direccion_id is not None:
            direccion = uow.direcciones_entrega.obtener_por_id(datos.direccion_id)
            if not direccion or direccion.usuario_id != usuario_id:
                raise ValueError(f"Dirección con id={datos.direccion_id} no encontrada")
            direccion_snapshot = _serializar_direccion(direccion)

        from app.services.producto_service import _calcular_metricas

        items_snapshot = []
        productos_cargados: dict = {}
        for item in datos.items:
            producto = uow.productos.obtener_por_id(item.producto_id)
            if not producto:
                raise ValueError(f"Producto con id={item.producto_id} no encontrado")
            if not producto.disponible:
                raise ValueError(f"Producto '{producto.nombre}' no está disponible")
            if not bool(producto.ingredientes_link) and producto.precio_base is None:
                raise ValueError(f"El producto '{producto.nombre}' no tiene precio base configurado")

            precio_snapshot = _obtener_precio_venta(producto)

            removibles = {link.ingrediente_id for link in producto.ingredientes_link if link.es_removible}
            for ing_id in item.personalizacion:
                if ing_id not in removibles:
                    raise ValueError(
                        f"El ingrediente id={ing_id} no es removible en el producto '{producto.nombre}'"
                    )

            subtotal_snap = (precio_snapshot * item.cantidad).quantize(Decimal("0.01"))
            items_snapshot.append({
                "producto_id": item.producto_id,
                "cantidad": item.cantidad,
                "nombre_snapshot": producto.nombre,
                "precio_snapshot": precio_snapshot,
                "subtotal_snap": subtotal_snap,
                "personalizacion": item.personalizacion,
            })
            productos_cargados[item.producto_id] = producto

        stock_req_ingredientes: dict[int, Decimal] = {}
        stock_req_directos: dict[int, int] = {}
        for item in datos.items:
            prod = productos_cargados[item.producto_id]
            if bool(prod.ingredientes_link):
                for link in prod.ingredientes_link:
                    key = link.ingrediente_id
                    stock_req_ingredientes[key] = stock_req_ingredientes.get(key, Decimal("0")) + link.cantidad * item.cantidad
            else:
                stock_req_directos[item.producto_id] = stock_req_directos.get(item.producto_id, 0) + item.cantidad

        for ing_id, needed in stock_req_ingredientes.items():
            ing = uow.ingredientes.obtener_por_id(ing_id)
            if not ing or ing.stock_total < needed:
                raise ValueError(f"Stock insuficiente para completar el pedido (ingrediente id={ing_id})")

        for prod_id, cant in stock_req_directos.items():
            prod = productos_cargados[prod_id]
            disponible = prod.stock_directo if prod.stock_directo is not None else 0
            if disponible < cant:
                raise ValueError(f"Stock insuficiente para '{prod.nombre}' (disponible: {disponible}, pedido: {cant})")

        for ing_id, needed in stock_req_ingredientes.items():
            uow.ingredientes.descontar_stock(ing_id, needed)

        for prod_id, cant in stock_req_directos.items():
            prod = productos_cargados[prod_id]
            uow.productos.actualizar(prod, {"stock_directo": (prod.stock_directo or 0) - cant})

        subtotal = sum(i["subtotal_snap"] for i in items_snapshot)
        total = (subtotal - datos.descuento + Decimal("50.00")).quantize(Decimal("0.01"))
        if total < 0:
            raise ValueError("El total no puede ser negativo")

        pedido = uow.pedidos.crear(
            usuario_id=usuario_id,
            direccion_id=datos.direccion_id,
            direccion_snapshot=direccion_snapshot,
            estado_codigo="PENDIENTE",
            forma_pago_codigo=datos.forma_pago_codigo,
            subtotal=subtotal,
            descuento=datos.descuento,
            costo_envio=Decimal("50.00"),
            total=total,
            notas=datos.notas,
            items_snapshot=items_snapshot,
        )

        uow.historial_pedidos.registrar(
            pedido_id=pedido.id,
            estado_desde=None,
            estado_hasta="PENDIENTE",
            usuario_id=usuario_id,
        )

        return _construir_pedido_publico(pedido, uow)


def avanzar_estado(
    pedido_id: int,
    datos: AvanzarEstadoBody,
    usuario_roles: list[str],
    usuario_id: int,
) -> Optional[PedidoPublico]:
    with UnidadDeTrabajo() as uow:
        pedido = uow.pedidos.obtener_por_id(pedido_id)
        if not pedido:
            return None

        estado_actual = pedido.estado_codigo
        estado_obj = uow.estados_pedido.obtener_por_codigo(estado_actual)

        if estado_obj and estado_obj.es_terminal:
            raise ValueError(f"El pedido está en estado terminal '{estado_actual}' y no puede avanzar")

        if datos.estado_hasta not in FSM_TRANSICIONES.get(estado_actual, set()):
            raise ValueError(f"Transición inválida: '{estado_actual}' → '{datos.estado_hasta}'")

        if datos.estado_hasta == "CANCELADO":
            if estado_actual in CANCELAR_REQUIERE_PRIVILEGIO:
                if not any(r in usuario_roles for r in ["ADMIN", "PEDIDOS"]):
                    raise PermissionError("Se requiere rol ADMIN o PEDIDOS para cancelar en este estado")
            if not datos.motivo or not datos.motivo.strip():
                raise ValueError("Se requiere un motivo para cancelar el pedido")
            if estado_actual in ESTADOS_CON_STOCK_DESCONTADO:
                _restaurar_stock_pedido(pedido, uow)

        pedido = uow.pedidos.actualizar_estado(pedido, datos.estado_hasta)
        uow.historial_pedidos.registrar(
            pedido_id=pedido.id,
            estado_desde=estado_actual,
            estado_hasta=datos.estado_hasta,
            usuario_id=usuario_id,
            motivo=datos.motivo,
        )

        return _construir_pedido_publico(pedido, uow)


def cancelar_pedido_cliente(
    pedido_id: int,
    motivo: str,
    usuario_id: int,
) -> Optional[PedidoPublico]:
    with UnidadDeTrabajo() as uow:
        pedido = uow.pedidos.obtener_por_id(pedido_id)
        if not pedido:
            return None
        if pedido.usuario_id != usuario_id:
            return None
        if pedido.estado_codigo not in {"PENDIENTE", "CONFIRMADO"}:
            raise ValueError("Solo se pueden cancelar pedidos en estado PENDIENTE o CONFIRMADO")
        if not motivo or not motivo.strip():
            raise ValueError("Se requiere un motivo para cancelar el pedido")

        estado_anterior = pedido.estado_codigo
        _restaurar_stock_pedido(pedido, uow)
        pedido = uow.pedidos.actualizar_estado(pedido, "CANCELADO")
        uow.historial_pedidos.registrar(
            pedido_id=pedido.id,
            estado_desde=estado_anterior,
            estado_hasta="CANCELADO",
            usuario_id=usuario_id,
            motivo=motivo,
        )

        return _construir_pedido_publico(pedido, uow)


def obtener_pedidos_usuario(
    usuario_id: int, skip: int = 0, limit: int = 10
) -> List[PedidoPublico]:
    with UnidadDeTrabajo() as uow:
        pedidos = uow.pedidos.obtener_por_usuario(usuario_id, skip, limit)
        return [_construir_pedido_publico(p, uow) for p in pedidos]


def obtener_pedido_usuario(
    pedido_id: int, usuario_id: int
) -> Optional[PedidoPublico]:
    with UnidadDeTrabajo() as uow:
        pedido = uow.pedidos.obtener_por_id(pedido_id)
        if not pedido or pedido.usuario_id != usuario_id:
            return None
        return _construir_pedido_publico(pedido, uow)


def obtener_pedidos_admin(
    skip: int = 0, limit: int = 10, estado: Optional[str] = None
) -> List[PedidoPublico]:
    with UnidadDeTrabajo() as uow:
        pedidos = uow.pedidos.obtener_todos(skip, limit, estado)
        return [_construir_pedido_publico(p, uow) for p in pedidos]


def obtener_pedido_admin(pedido_id: int) -> Optional[PedidoPublico]:
    with UnidadDeTrabajo() as uow:
        pedido = uow.pedidos.obtener_por_id(pedido_id)
        if not pedido:
            return None
        return _construir_pedido_publico(pedido, uow)


def obtener_historial_pedido(
    pedido_id: int, usuario_id: int, usuario_roles: list[str]
) -> Optional[List[HistorialEstadoPublico]]:
    with UnidadDeTrabajo() as uow:
        pedido = uow.pedidos.obtener_por_id(pedido_id)
        if not pedido:
            return None
        if not any(r in usuario_roles for r in ["ADMIN", "PEDIDOS"]):
            if pedido.usuario_id != usuario_id:
                return None
        return [
            HistorialEstadoPublico(
                estado_desde=h.estado_desde,
                estado_hasta=h.estado_hasta,
                usuario_id=h.usuario_id,
                motivo=h.motivo,
                created_at=h.created_at,
            )
            for h in pedido.historial
        ]


def obtener_metricas() -> MetricasResumen:
    with UnidadDeTrabajo() as uow:
        return uow.pedidos.obtener_metricas()
