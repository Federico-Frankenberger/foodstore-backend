from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, DateTime, String
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class UnidadMedida(SQLModel, table=True):
    __tablename__ = "unidad_medida"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), primary_key=True, autoincrement=True),
    )
    nombre: str = Field(sa_column=Column(String(50), unique=True, nullable=False))
    simbolo: str = Field(sa_column=Column(String(10), unique=True, nullable=False))
    tipo: str = Field(sa_column=Column(String(20), nullable=False))

    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
