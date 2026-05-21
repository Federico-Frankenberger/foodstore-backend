from typing import List, Optional

from sqlmodel import Session, select

from app.models.historial_estado_pedido import HistorialEstadoPedido


class HistorialEstadoPedidoRepositorio:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def registrar(
        self,
        pedido_id: int,
        estado_desde: Optional[str],
        estado_hasta: str,
        usuario_id: int,
        motivo: Optional[str] = None,
    ) -> HistorialEstadoPedido:
        historial = HistorialEstadoPedido(
            pedido_id=pedido_id,
            estado_desde=estado_desde,
            estado_hasta=estado_hasta,
            usuario_id=usuario_id,
            motivo=motivo,
        )
        self.sesion.add(historial)
        self.sesion.flush()
        self.sesion.refresh(historial)
        return historial

    def obtener_por_pedido(self, pedido_id: int) -> List[HistorialEstadoPedido]:
        consulta = (
            select(HistorialEstadoPedido)
            .where(HistorialEstadoPedido.pedido_id == pedido_id)
            .order_by(HistorialEstadoPedido.created_at)
        )
        return list(self.sesion.exec(consulta).all())
