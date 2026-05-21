from typing import Optional

from sqlmodel import Field, SQLModel


class Rol(SQLModel, table=True):
    __tablename__ = "rol"

    codigo: str = Field(max_length=20, primary_key=True)
    nombre: str = Field(max_length=50, unique=True)
    descripcion: Optional[str] = Field(default=None)
