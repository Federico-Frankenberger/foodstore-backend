from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class CategoriaResumen(BaseModel):
    id: int
    nombre: str
    es_principal: bool

    model_config = {"from_attributes": True}


class IngredienteResumen(BaseModel):
    id: int
    nombre: str
    cantidad: Decimal
    simbolo_unidad: str
    es_removible: bool
    es_alergeno: bool

    model_config = {"from_attributes": True}


class CategoriaAsignacion(BaseModel):
    categoria_id: int = Field(..., gt=0)
    es_principal: bool = Field(default=False)


class IngredienteAsignacion(BaseModel):
    ingrediente_id: int = Field(..., gt=0)
    cantidad: Decimal = Field(..., gt=0, decimal_places=3)
    unidad_medida_id: int = Field(..., gt=0)
    es_removible: bool = Field(default=False)


class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150, examples=["Hamburguesa clásica"])
    descripcion: Optional[str] = Field(default=None, examples=["Pan brioche, carne 200g, lechuga"])
    margen_ganancia: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2, examples=["50.00"])
    imagenes_url: Optional[List[str]] = Field(default=None, examples=[["https://ejemplo.com/img1.jpg"]])
    disponible: bool = Field(default=True)
    unidad_venta_id: Optional[int] = Field(default=None, gt=0, examples=[1])


class ProductoCreate(ProductoBase):
    categorias: List[CategoriaAsignacion] = Field(default_factory=list)
    ingredientes: List[IngredienteAsignacion] = Field(default_factory=list)
    stock_directo: Optional[int] = Field(default=None, ge=0)
    precio_base: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=150)
    descripcion: Optional[str] = None
    margen_ganancia: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)
    imagenes_url: Optional[List[str]] = None
    disponible: Optional[bool] = None
    unidad_venta_id: Optional[int] = Field(default=None, gt=0)
    stock_directo: Optional[int] = Field(default=None, ge=0)
    precio_base: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)


class ProductoRead(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    margen_ganancia: Decimal
    imagenes_url: Optional[List[str]] = None
    stock_calculado: int
    precio_costo_calculado: Decimal
    precio_venta: Decimal
    disponible: bool
    unidad_venta_id: Optional[int] = None
    tiene_ingredientes: bool
    stock_directo: Optional[int] = None
    precio_base: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    categorias: List[CategoriaResumen] = []
    ingredientes: List[IngredienteResumen] = []

    model_config = {"from_attributes": True}


class DisponibilidadUpdate(BaseModel):
    disponible: bool


class StockDirectoUpdate(BaseModel):
    stock_directo: int = Field(..., ge=0)
    precio_base: Optional[Decimal] = Field(default=None, ge=0, decimal_places=2)


class ProductoCategoriaCreate(BaseModel):
    categoria_id: int = Field(..., gt=0)
    es_principal: bool = Field(default=False)


class ProductoIngredienteCreate(BaseModel):
    ingrediente_id: int = Field(..., gt=0)
    cantidad: Decimal = Field(..., gt=0, decimal_places=3)
    unidad_medida_id: int = Field(..., gt=0)
    es_removible: bool = Field(default=False)
