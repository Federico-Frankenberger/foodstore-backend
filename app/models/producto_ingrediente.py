from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .producto import Producto
    from .ingrediente import Ingrediente


class ProductoIngrediente(SQLModel, table=True):
    __tablename__ = "producto_ingrediente"

    producto_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("producto.id"), primary_key=True, nullable=False),
    )
    ingrediente_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("ingrediente.id"), primary_key=True, nullable=False),
    )
    cantidad: Decimal = Field(
        sa_column=Column(Numeric(10, 3), nullable=False)
    )
    unidad_medida_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("unidad_medida.id"), nullable=False),
    )
    es_removible: bool = Field(
        sa_column=Column(Boolean(), nullable=False, server_default="false")
    )

    producto: Optional["Producto"] = Relationship(back_populates="ingredientes_link")
    ingrediente: Optional["Ingrediente"] = Relationship(back_populates="productos_link")
