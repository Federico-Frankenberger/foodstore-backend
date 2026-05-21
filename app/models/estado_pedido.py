from typing import Optional

from sqlalchemy import Boolean, Column, SmallInteger, String
from sqlmodel import Field, SQLModel


class EstadoPedido(SQLModel, table=True):
    __tablename__ = "estado_pedido"

    codigo: str = Field(sa_column=Column(String(20), primary_key=True))
    descripcion: str = Field(sa_column=Column(String(80), nullable=False))
    orden: int = Field(sa_column=Column(SmallInteger(), nullable=False))
    es_terminal: bool = Field(sa_column=Column(Boolean(), nullable=False, server_default="false"))
