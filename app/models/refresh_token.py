from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_token"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger(), primary_key=True, autoincrement=True),
    )
    usuario_id: int = Field(
        sa_column=Column(BigInteger(), ForeignKey("usuario.id"), nullable=False),
    )
    # SHA-256 del token raw que se entrega al cliente (nunca se persiste el token en texto plano)
    token_hash: str = Field(
        sa_column=Column(String(64), unique=True, nullable=False),
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    revoked_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
