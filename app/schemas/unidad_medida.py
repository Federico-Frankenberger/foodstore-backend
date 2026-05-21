from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UnidadMedidaCrear(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50, examples=["kilogramo"])
    simbolo: str = Field(..., min_length=1, max_length=10, examples=["kg"])
    tipo: str = Field(..., min_length=2, max_length=20, examples=["masa"])


class UnidadMedidaActualizar(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=50)
    simbolo: Optional[str] = Field(default=None, min_length=1, max_length=10)
    tipo: Optional[str] = Field(default=None, min_length=2, max_length=20)


class UnidadMedidaPublica(BaseModel):
    id: int
    nombre: str
    simbolo: str
    tipo: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
