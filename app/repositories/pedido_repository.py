from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.detalle_pedido import DetallePedido
from app.models.pedido import Pedido


class PedidoRepositorio:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def crear(
        self,
        usuario_id: int,
        direccion_id: Optional[int],
        direccion_snapshot: Optional[str],
        estado_codigo: str,
        forma_pago_codigo: str,
        subtotal: Decimal,
        descuento: Decimal,
        costo_envio: Decimal,
        total: Decimal,
        notas: Optional[str],
        items_snapshot: list,
    ) -> Pedido:
        pedido = Pedido(
            usuario_id=usuario_id,
            direccion_id=direccion_id,
            direccion_snapshot=direccion_snapshot,
            estado_codigo=estado_codigo,
            forma_pago_codigo=forma_pago_codigo,
            subtotal=subtotal,
            descuento=descuento,
            costo_envio=costo_envio,
            total=total,
            notas=notas,
        )
        self.sesion.add(pedido)
        self.sesion.flush()

        for item in items_snapshot:
            self.sesion.add(DetallePedido(
                pedido_id=pedido.id,
                producto_id=item["producto_id"],
                cantidad=item["cantidad"],
                nombre_snapshot=item["nombre_snapshot"],
                precio_snapshot=item["precio_snapshot"],
                subtotal_snap=item["subtotal_snap"],
                personalizacion=item.get("personalizacion") or None,
            ))

        self.sesion.flush()
        self.sesion.refresh(pedido)
        return pedido

    def obtener_por_id(self, id: int) -> Optional[Pedido]:
        pedido = self.sesion.get(Pedido, id)
        if pedido and pedido.deleted_at is not None:
            return None
        return pedido

    def obtener_por_usuario(
        self, usuario_id: int, skip: int = 0, limit: int = 10
    ) -> List[Pedido]:
        consulta = (
            select(Pedido)
            .where(Pedido.usuario_id == usuario_id)
            .where(Pedido.deleted_at == None)  # noqa: E711
            .offset(skip)
            .limit(limit)
        )
        return list(self.sesion.exec(consulta).all())

    def obtener_todos(
        self, skip: int = 0, limit: int = 10, estado: Optional[str] = None
    ) -> List[Pedido]:
        consulta = select(Pedido).where(Pedido.deleted_at == None)  # noqa: E711
        if estado:
            consulta = consulta.where(Pedido.estado_codigo == estado)
        consulta = consulta.offset(skip).limit(limit)
        return list(self.sesion.exec(consulta).all())

    def actualizar_estado(self, pedido: Pedido, estado_codigo: str) -> Pedido:
        pedido.estado_codigo = estado_codigo
        self.sesion.add(pedido)
        self.sesion.flush()
        self.sesion.refresh(pedido)
        return pedido

    def obtener_metricas(self):
        from app.schemas.pedido import MetricasResumen

        total_pedidos = self.sesion.execute(
            select(func.count(Pedido.id)).where(Pedido.deleted_at == None)  # noqa: E711
        ).scalar() or 0

        facturacion = self.sesion.execute(
            select(func.sum(Pedido.total)).where(Pedido.deleted_at == None)  # noqa: E711
        ).scalar()
        facturacion_total = Decimal(str(facturacion)) if facturacion is not None else Decimal("0.00")

        estados_rows = self.sesion.execute(
            select(Pedido.estado_codigo, func.count(Pedido.id))
            .where(Pedido.deleted_at == None)  # noqa: E711
            .group_by(Pedido.estado_codigo)
        ).all()
        pedidos_por_estado = {estado: count for estado, count in estados_rows}

        return MetricasResumen(
            total_pedidos=total_pedidos,
            facturacion_total=facturacion_total,
            pedidos_por_estado=pedidos_por_estado,
        )
