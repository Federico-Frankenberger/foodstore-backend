from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .producto_categoria import ProductoCategoria
    from .producto_ingrediente import ProductoIngrediente
    from .detalle_pedido import DetallePedido


class Producto(SQLModel, table=True):
    __tablename__ = "producto"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), primary_key=True, autoincrement=True),
    )
    unidad_venta_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), ForeignKey("unidad_medida.id"), nullable=True),
    )
    nombre: str = Field(max_length=150)
    descripcion: Optional[str] = Field(default=None)
    margen_ganancia: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(5, 2), nullable=False, server_default="0"),
    )
    imagenes_url: Optional[List[str]] = Field(
        default=None,
        sa_column=Column(ARRAY(String), nullable=True),
    )
    disponible: bool = Field(
        sa_column=Column(Boolean(), nullable=False, server_default="true")
    )
    stock_directo: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), nullable=True),
    )
    precio_base: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(10, 2), nullable=True),
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
    deleted_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    categorias_link: List["ProductoCategoria"] = Relationship(
        back_populates="producto",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    ingredientes_link: List["ProductoIngrediente"] = Relationship(
        back_populates="producto",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    detalles: List["DetallePedido"] = Relationship(back_populates="producto")
