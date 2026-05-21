from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Column, DateTime
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .producto_categoria import ProductoCategoria


class Categoria(SQLModel, table=True):
    __tablename__ = "categoria"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), primary_key=True, autoincrement=True),
    )
    parent_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), nullable=True),
    )
    nombre: str = Field(max_length=100, unique=True)
    descripcion: Optional[str] = Field(default=None)
    imagen_url: Optional[str] = Field(default=None)

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

    productos_link: List["ProductoCategoria"] = Relationship(back_populates="categoria")
