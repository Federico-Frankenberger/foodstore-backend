from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .pedido import Pedido
    from .usuario import Usuario


class HistorialEstadoPedido(SQLModel, table=True):
    __tablename__ = "historial_estado_pedido"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), primary_key=True, autoincrement=True),
    )
    pedido_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("pedido.id", ondelete="CASCADE"), nullable=False)
    )
    estado_desde: Optional[str] = Field(
        default=None,
        sa_column=Column(String(20), ForeignKey("estado_pedido.codigo"), nullable=True),
    )
    estado_hasta: str = Field(
        sa_column=Column(String(20), ForeignKey("estado_pedido.codigo"), nullable=False)
    )
    usuario_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("usuario.id"), nullable=False)
    )
    motivo: Optional[str] = Field(default=None, sa_column=Column(Text(), nullable=True))
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )

    pedido: Optional["Pedido"] = Relationship(back_populates="historial")
    usuario: Optional["Usuario"] = Relationship(back_populates="historial_pedidos")
