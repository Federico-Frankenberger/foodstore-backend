from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .pedido import Pedido


class DireccionEntrega(SQLModel, table=True):
    __tablename__ = "direccion_entrega"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), primary_key=True, autoincrement=True),
    )
    usuario_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("usuario.id"), nullable=False),
    )
    alias: Optional[str] = Field(
        default=None,
        sa_column=Column(String(50), nullable=True),
    )
    linea1: str = Field(sa_column=Column(Text(), nullable=False))
    linea2: Optional[str] = Field(default=None, sa_column=Column(Text(), nullable=True))
    ciudad: str = Field(sa_column=Column(String(100), nullable=False))
    provincia: Optional[str] = Field(default=None, sa_column=Column(Text(), nullable=True))
    codigo_postal: Optional[str] = Field(
        default=None,
        sa_column=Column(String(10), nullable=True),
    )
    latitud: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(9, 6), nullable=True),
    )
    longitud: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(9, 6), nullable=True),
    )
    es_principal: bool = Field(
        sa_column=Column(Boolean(), nullable=False, server_default="false"),
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

    pedidos: List["Pedido"] = Relationship(back_populates="direccion")
