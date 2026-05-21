from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ItemPedidoCrear(BaseModel):
    producto_id: int = Field(..., gt=0)
    cantidad: int = Field(..., ge=1)
    personalizacion: List[int] = Field(default_factory=list)


class PedidoCrear(BaseModel):
    direccion_id: Optional[int] = Field(default=None, gt=0)
    forma_pago_codigo: str
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0)
    notas: Optional[str] = None
    items: List[ItemPedidoCrear] = Field(..., min_length=1)


class AvanzarEstadoBody(BaseModel):
    estado_hasta: str
    motivo: Optional[str] = Field(default=None, max_length=500)


class CancelarPedidoBody(BaseModel):
    motivo: str = Field(..., min_length=1, max_length=500)


class DetallePedidoPublico(BaseModel):
    producto_id: int
    nombre_snapshot: str
    precio_snapshot: Decimal
    cantidad: int
    subtotal_snap: Decimal
    personalizacion: List[int] = []

    model_config = {"from_attributes": True}


class HistorialEstadoPublico(BaseModel):
    estado_desde: Optional[str]
    estado_hasta: str
    usuario_id: int
    motivo: Optional[str]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}


class PedidoPublico(BaseModel):
    id: int
    usuario_id: int
    direccion_id: Optional[int]
    direccion_snapshot: Optional[str] = None
    estado_codigo: str
    forma_pago_codigo: str
    subtotal: Decimal
    descuento: Decimal
    costo_envio: Decimal
    total: Decimal
    notas: Optional[str]
    created_at: Optional[datetime]
    items: List[DetallePedidoPublico] = []
    historial: List[HistorialEstadoPublico] = []

    model_config = {"from_attributes": True}


class MetricasResumen(BaseModel):
    total_pedidos: int
    facturacion_total: Decimal
    pedidos_por_estado: Dict[str, int]
