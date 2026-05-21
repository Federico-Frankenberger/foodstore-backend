from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class IngredienteBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, examples=["Queso cheddar"])
    descripcion: Optional[str] = Field(default=None, examples=["Queso cheddar fundido"])
    es_alergeno: bool = Field(default=False)
    unidad_medida_id: Optional[int] = Field(default=None, gt=0, examples=[1])
    stock_total: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=3, examples=["5.000"])
    precio_costo: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2, examples=["300.00"])


class IngredienteCreate(IngredienteBase):
    pass


class IngredienteUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=100)
    descripcion: Optional[str] = None
    es_alergeno: Optional[bool] = None
    unidad_medida_id: Optional[int] = Field(default=None, gt=0)
    stock_total: Optional[Decimal] = Field(default=None, ge=0, decimal_places=3)
    precio_costo: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)


class StockUpdate(BaseModel):
    stock_total: Decimal = Field(..., ge=0, decimal_places=3)


class IngredienteRead(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    es_alergeno: bool
    unidad_medida_id: Optional[int] = None
    stock_total: Decimal
    precio_costo: Decimal
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
