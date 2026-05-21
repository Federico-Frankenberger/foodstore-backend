import math
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.exc import IntegrityError

from app.models.producto import Producto
from app.schemas.producto import (
    CategoriaResumen,
    IngredienteResumen,
    ProductoCategoriaCreate,
    ProductoCreate,
    ProductoIngredienteCreate,
    ProductoRead,
    ProductoUpdate,
    StockDirectoUpdate,
)
from app.uow.uow import UnidadDeTrabajo


def _calcular_metricas(
    ingredientes_link: list,
    margen_ganancia: Decimal,
) -> tuple[int, Decimal, Decimal]:
    """
    Devuelve (stock_calculado, precio_costo_calculado, precio_venta).

    stock_calculado:
        min( floor(stock_total / cantidad) ) para cada ingrediente.
        Si no hay ingredientes → 0.

    precio_costo_calculado:
        sum( precio_costo × cantidad ) redondeado a 2 decimales.

    precio_venta:
        precio_costo_calculado × (1 + margen_ganancia / 100) redondeado a 2 decimales.
    """
    if not ingredientes_link:
        return 0, Decimal("0.00"), Decimal("0.00")

    stocks: list[int] = []
    costo = Decimal("0")

    for link in ingredientes_link:
        if link.cantidad > 0:
            stocks.append(int(math.floor(link.ingrediente.stock_total / link.cantidad)))
        costo += link.ingrediente.precio_costo * link.cantidad

    stock_calculado = min(stocks) if stocks else 0
    precio_costo = costo.quantize(Decimal("0.01"))
    precio_venta = (precio_costo * (1 + margen_ganancia / 100)).quantize(Decimal("0.01"))

    return stock_calculado, precio_costo, precio_venta


def _construir_producto_read(producto: Producto, uow) -> ProductoRead:
    categorias = [
        CategoriaResumen(
            id=link.categoria_id,
            nombre=link.categoria.nombre,
            es_principal=link.es_principal,
        )
        for link in producto.categorias_link
    ]
    ingredientes = []
    for link in producto.ingredientes_link:
        unidad = uow.unidades_medida.obtener_por_id(link.unidad_medida_id)
        ingredientes.append(IngredienteResumen(
            id=link.ingrediente_id,
            nombre=link.ingrediente.nombre,
            cantidad=link.cantidad,
            simbolo_unidad=unidad.simbolo if unidad else "",
            es_removible=link.es_removible,
            es_alergeno=link.ingrediente.es_alergeno,
        ))

    tiene_ingredientes = bool(producto.ingredientes_link)

    if tiene_ingredientes:
        stock_calculado, precio_costo_calculado, precio_venta = _calcular_metricas(
            producto.ingredientes_link,
            producto.margen_ganancia,
        )
    else:
        stock_calculado = producto.stock_directo if producto.stock_directo is not None else 0
        precio_base_val = producto.precio_base if producto.precio_base is not None else Decimal("0.00")
        precio_costo_calculado = precio_base_val
        precio_venta = (precio_base_val * (1 + producto.margen_ganancia / 100)).quantize(Decimal("0.01"))

    return ProductoRead(
        id=producto.id,
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        margen_ganancia=producto.margen_ganancia,
        imagenes_url=producto.imagenes_url,
        stock_calculado=stock_calculado,
        precio_costo_calculado=precio_costo_calculado,
        precio_venta=precio_venta,
        disponible=producto.disponible,
        unidad_venta_id=producto.unidad_venta_id,
        tiene_ingredientes=tiene_ingredientes,
        stock_directo=producto.stock_directo,
        precio_base=producto.precio_base,
        created_at=producto.created_at,
        updated_at=producto.updated_at,
        categorias=categorias,
        ingredientes=ingredientes,
    )


def crear_producto(datos: ProductoCreate) -> ProductoRead:
    with UnidadDeTrabajo() as uow:
        for asignacion in datos.categorias:
            if not uow.categorias.obtener_por_id(asignacion.categoria_id):
                raise ValueError(f"Categoría con id={asignacion.categoria_id} no encontrada")
        for asignacion in datos.ingredientes:
            if not uow.ingredientes.obtener_por_id(asignacion.ingrediente_id):
                raise ValueError(f"Ingrediente con id={asignacion.ingrediente_id} no encontrado")
            if not uow.unidades_medida.obtener_por_id(asignacion.unidad_medida_id):
                raise ValueError(f"Unidad de medida con id={asignacion.unidad_medida_id} no encontrada")
        if datos.unidad_venta_id and not uow.unidades_medida.obtener_por_id(datos.unidad_venta_id):
            raise ValueError(f"Unidad de venta con id={datos.unidad_venta_id} no encontrada")
        producto = uow.productos.crear(datos)
        return _construir_producto_read(producto, uow)


def obtener_productos(
    skip: int = 0,
    limit: int = 10,
    nombre: Optional[str] = None,
    disponible: Optional[bool] = None,
    categoria_id: Optional[int] = None,
) -> List[ProductoRead]:
    with UnidadDeTrabajo() as uow:
        productos = uow.productos.obtener_todos(skip, limit, nombre, disponible, categoria_id)
        return [_construir_producto_read(p, uow) for p in productos]


def obtener_producto(id: int) -> Optional[ProductoRead]:
    with UnidadDeTrabajo() as uow:
        producto = uow.productos.obtener_por_id(id)
        if not producto:
            return None
        return _construir_producto_read(producto, uow)


def actualizar_producto(id: int, datos: ProductoUpdate) -> Optional[ProductoRead]:
    with UnidadDeTrabajo() as uow:
        producto = uow.productos.obtener_por_id(id)
        if not producto:
            return None
        campos = datos.model_dump(exclude_unset=True)
        if "unidad_venta_id" in campos and campos["unidad_venta_id"] is not None:
            if not uow.unidades_medida.obtener_por_id(campos["unidad_venta_id"]):
                raise ValueError(f"Unidad de venta con id={campos['unidad_venta_id']} no encontrada")
        producto = uow.productos.actualizar(producto, campos)
        return _construir_producto_read(producto, uow)


def actualizar_stock_directo(id: int, datos: StockDirectoUpdate) -> Optional[ProductoRead]:
    with UnidadDeTrabajo() as uow:
        producto = uow.productos.obtener_por_id(id)
        if not producto:
            return None
        if bool(producto.ingredientes_link):
            raise ValueError("Este producto tiene ingredientes; su stock se gestiona automáticamente")
        campos: dict = {"stock_directo": datos.stock_directo}
        if datos.precio_base is not None:
            campos["precio_base"] = datos.precio_base
        producto = uow.productos.actualizar(producto, campos)
        return _construir_producto_read(producto, uow)


def actualizar_disponibilidad(id: int, disponible: bool) -> Optional[ProductoRead]:
    with UnidadDeTrabajo() as uow:
        producto = uow.productos.obtener_por_id(id)
        if not producto:
            return None
        producto = uow.productos.actualizar(producto, {"disponible": disponible})
        return _construir_producto_read(producto, uow)


def eliminar_producto(id: int) -> bool:
    with UnidadDeTrabajo() as uow:
        producto = uow.productos.obtener_por_id(id)
        if not producto:
            return False
        uow.productos.eliminar(producto)
        return True


def agregar_categoria(id_producto: int, datos: ProductoCategoriaCreate) -> Optional[ProductoRead]:
    try:
        with UnidadDeTrabajo() as uow:
            if not uow.productos.obtener_por_id(id_producto):
                return None
            if not uow.categorias.obtener_por_id(datos.categoria_id):
                return None
            producto = uow.productos.agregar_categoria(id_producto, datos.categoria_id, datos.es_principal)
            return _construir_producto_read(producto, uow)
    except IntegrityError:
        raise ValueError("La categoría ya está asignada al producto")


def quitar_categoria(id_producto: int, id_categoria: int) -> bool:
    with UnidadDeTrabajo() as uow:
        return uow.productos.quitar_categoria(id_producto, id_categoria)


def agregar_ingrediente(
    id_producto: int, datos: ProductoIngredienteCreate
) -> Optional[ProductoRead]:
    try:
        with UnidadDeTrabajo() as uow:
            if not uow.productos.obtener_por_id(id_producto):
                return None
            if not uow.ingredientes.obtener_por_id(datos.ingrediente_id):
                return None
            if not uow.unidades_medida.obtener_por_id(datos.unidad_medida_id):
                raise ValueError(f"Unidad de medida con id={datos.unidad_medida_id} no encontrada")
            producto = uow.productos.agregar_ingrediente(
                id_producto,
                datos.ingrediente_id,
                datos.cantidad,
                datos.unidad_medida_id,
                datos.es_removible,
            )
            return _construir_producto_read(producto, uow)
    except IntegrityError:
        raise ValueError("El ingrediente ya está asignado al producto")


def quitar_ingrediente(id_producto: int, id_ingrediente: int) -> bool:
    with UnidadDeTrabajo() as uow:
        return uow.productos.quitar_ingrediente(id_producto, id_ingrediente)
