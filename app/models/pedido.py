from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .detalle_pedido import DetallePedido
    from .historial_estado_pedido import HistorialEstadoPedido
    from .usuario import Usuario
    from .direccion_entrega import DireccionEntrega


class Pedido(SQLModel, table=True):
    __tablename__ = "pedido"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_pedido_total_positivo"),
        CheckConstraint("subtotal >= 0", name="ck_pedido_subtotal_positivo"),
        CheckConstraint("descuento >= 0", name="ck_pedido_descuento_positivo"),
        CheckConstraint("costo_envio >= 0", name="ck_pedido_costo_envio_positivo"),
    )

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), primary_key=True, autoincrement=True),
    )
    usuario_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("usuario.id"), nullable=False)
    )
    direccion_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), ForeignKey("direccion_entrega.id", ondelete="SET NULL"), nullable=True),
    )
    estado_codigo: str = Field(
        sa_column=Column(String(20), ForeignKey("estado_pedido.codigo"), nullable=False)
    )
    forma_pago_codigo: str = Field(
        sa_column=Column(String(20), ForeignKey("forma_pago.codigo"), nullable=False)
    )
    subtotal: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    descuento: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0"),
    )
    costo_envio: Decimal = Field(
        default=Decimal("50.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="50"),
    )
    total: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    notas: Optional[str] = Field(default=None, sa_column=Column(Text(), nullable=True))
    direccion_snapshot: Optional[str] = Field(default=None, sa_column=Column(Text(), nullable=True))
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True, onupdate=func.now()),
    )
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    detalles: List["DetallePedido"] = Relationship(back_populates="pedido")
    historial: List["HistorialEstadoPedido"] = Relationship(back_populates="pedido")
    usuario: Optional["Usuario"] = Relationship(back_populates="pedidos")
    direccion: Optional["DireccionEntrega"] = Relationship(back_populates="pedidos")
