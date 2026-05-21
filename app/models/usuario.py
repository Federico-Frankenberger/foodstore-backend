from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import BigInteger, Column, DateTime, String
from sqlalchemy.sql import func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .pedido import Pedido
    from .historial_estado_pedido import HistorialEstadoPedido


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), primary_key=True, autoincrement=True),
    )
    nombre: str = Field(max_length=80)
    apellido: str = Field(max_length=80)
    email: str = Field(max_length=254, index=True, unique=True)
    celular: Optional[str] = Field(default=None, max_length=20)
    password_hash: str = Field(sa_column=Column(String(60), nullable=False))

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

    pedidos: List["Pedido"] = Relationship(back_populates="usuario")
    historial_pedidos: List["HistorialEstadoPedido"] = Relationship(back_populates="usuario")
