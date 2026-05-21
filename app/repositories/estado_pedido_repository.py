from typing import List, Optional

from sqlmodel import Session, select

from app.models.estado_pedido import EstadoPedido


class EstadoPedidoRepositorio:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener_por_codigo(self, codigo: str) -> Optional[EstadoPedido]:
        return self.sesion.get(EstadoPedido, codigo)

    def obtener_todos(self) -> List[EstadoPedido]:
        return list(self.sesion.exec(select(EstadoPedido).order_by(EstadoPedido.orden)).all())

    def crear(self, estado: EstadoPedido) -> EstadoPedido:
        self.sesion.add(estado)
        self.sesion.flush()
        self.sesion.refresh(estado)
        return estado
