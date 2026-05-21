from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class UsuarioRol(SQLModel, table=True):
    __tablename__ = "usuario_rol"

    usuario_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("usuario.id"), primary_key=True, nullable=False),
    )
    rol_codigo: str = Field(
        sa_column=Column(String(20), ForeignKey("rol.codigo"), primary_key=True, nullable=False),
    )
    asignado_por_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), ForeignKey("usuario.id"), nullable=True),
    )
    expires_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
