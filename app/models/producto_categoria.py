from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .producto import Producto
    from .categoria import Categoria


class ProductoCategoria(SQLModel, table=True):
    __tablename__ = "producto_categoria"

    producto_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("producto.id"), primary_key=True, nullable=False),
    )
    categoria_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("categoria.id"), primary_key=True, nullable=False),
    )
    es_principal: bool = Field(default=False)

    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )

    producto: Optional["Producto"] = Relationship(back_populates="categorias_link")
    categoria: Optional["Categoria"] = Relationship(back_populates="productos_link")
