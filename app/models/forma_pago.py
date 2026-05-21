from sqlalchemy import Boolean, Column, String
from sqlmodel import Field, SQLModel


class FormaPago(SQLModel, table=True):
    __tablename__ = "forma_pago"

    codigo: str = Field(sa_column=Column(String(20), primary_key=True))
    descripcion: str = Field(sa_column=Column(String(80), nullable=False))
    habilitado: bool = Field(sa_column=Column(Boolean(), nullable=False, server_default="true"))
