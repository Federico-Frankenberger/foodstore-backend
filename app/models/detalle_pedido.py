from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .pedido import Pedido
    from .producto import Producto


class DetallePedido(SQLModel, table=True):
    __tablename__ = "detalle_pedido"
    __table_args__ = (
        CheckConstraint("cantidad >= 1", name="ck_detalle_cantidad_positiva"),
        CheckConstraint("precio_snapshot >= 0", name="ck_detalle_precio_positivo"),
        CheckConstraint("subtotal_snap >= 0", name="ck_detalle_subtotal_positivo"),
    )

    pedido_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("pedido.id", ondelete="CASCADE"), primary_key=True),
    )
    producto_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("producto.id"), primary_key=True),
    )
    cantidad: int = Field(sa_column=Column(SmallInteger(), nullable=False))
    nombre_snapshot: str = Field(sa_column=Column(String(200), nullable=False))
    precio_snapshot: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    subtotal_snap: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    personalizacion: Optional[List[int]] = Field(
        default=None,
        sa_column=Column(ARRAY(INTEGER()), nullable=True),
    )
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )

    pedido: Optional["Pedido"] = Relationship(back_populates="detalles")
    producto: Optional["Producto"] = Relationship(back_populates="detalles")
