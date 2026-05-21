from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CategoriaBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, examples=["Hamburguesas"])
    descripcion: Optional[str] = Field(default=None, examples=["Hamburguesas con pan brioche"])
    imagen_url: Optional[str] = Field(default=None, examples=["https://ejemplo.com/imagen.jpg"])
    parent_id: Optional[int] = Field(default=None, gt=0, examples=[1])


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=100)
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    parent_id: Optional[int] = Field(default=None, gt=0)


class CategoriaRead(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    parent_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CategoriaNodo(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    parent_id: Optional[int] = None
    hijos: List[CategoriaNodo] = []

    model_config = {"from_attributes": True}


CategoriaNodo.model_rebuild()
