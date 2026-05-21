from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .producto_ingrediente import ProductoIngrediente


class Ingrediente(SQLModel, table=True):
    __tablename__ = "ingrediente"
    __table_args__ = (
        CheckConstraint("stock_total >= 0",  name="ck_ingrediente_stock_total_positivo"),
        CheckConstraint("precio_costo >= 0", name="ck_ingrediente_precio_costo_positivo"),
    )

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), primary_key=True, autoincrement=True),
    )
    nombre: str = Field(max_length=100, unique=True)
    descripcion: Optional[str] = Field(default=None)
    es_alergeno: bool = Field(default=False)
    unidad_medida_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), ForeignKey("unidad_medida.id"), nullable=True),
    )
    stock_total: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(10, 3), nullable=False, server_default="0"),
    )
    precio_costo: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0"),
    )

    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        ),
    )

    productos_link: List["ProductoIngrediente"] = Relationship(back_populates="ingrediente")
