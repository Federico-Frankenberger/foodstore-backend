from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from app.models.direccion_entrega import DireccionEntrega
from app.uow.uow import UnidadDeTrabajo


class DireccionCrear(BaseModel):
    alias: Optional[str] = Field(default=None, max_length=50)
    linea1: str
    linea2: Optional[str] = None
    ciudad: str = Field(max_length=100)
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = Field(default=None, max_length=10)
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    es_principal: bool = False


class DireccionActualizar(BaseModel):
    alias: Optional[str] = Field(default=None, max_length=50)
    linea1: Optional[str] = None
    linea2: Optional[str] = None
    ciudad: Optional[str] = Field(default=None, max_length=100)
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = Field(default=None, max_length=10)
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    es_principal: Optional[bool] = None


class DireccionRead(BaseModel):
    id: int
    usuario_id: int
    alias: Optional[str] = None
    linea1: str
    linea2: Optional[str] = None
    ciudad: str
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = None
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    es_principal: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


def listar_direcciones(usuario_id: int) -> list[DireccionRead]:
    with UnidadDeTrabajo() as uow:
        return [
            DireccionRead.model_validate(d)
            for d in uow.direcciones_entrega.obtener_por_usuario(usuario_id)
        ]


def crear_direccion(usuario_id: int, datos: DireccionCrear) -> DireccionRead:
    with UnidadDeTrabajo() as uow:
        # Si es_principal, quitar el flag de las demás antes de insertar
        if datos.es_principal:
            uow.direcciones_entrega.marcar_principal(usuario_id, -1)
        direccion = DireccionEntrega(
            usuario_id=usuario_id,
            **datos.model_dump(),
        )
        direccion = uow.direcciones_entrega.crear(direccion)
        return DireccionRead.model_validate(direccion)


def obtener_direccion(usuario_id: int, direccion_id: int) -> DireccionRead:
    with UnidadDeTrabajo() as uow:
        direccion = uow.direcciones_entrega.obtener_por_id(direccion_id)
        if not direccion or direccion.usuario_id != usuario_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dirección no encontrada")
        return DireccionRead.model_validate(direccion)


def actualizar_direccion(usuario_id: int, direccion_id: int, datos: DireccionActualizar) -> DireccionRead:
    with UnidadDeTrabajo() as uow:
        direccion = uow.direcciones_entrega.obtener_por_id(direccion_id)
        if not direccion or direccion.usuario_id != usuario_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dirección no encontrada")
        campos = datos.model_dump(exclude_unset=True)
        if campos.get("es_principal"):
            uow.direcciones_entrega.marcar_principal(usuario_id, direccion_id)
            campos.pop("es_principal")
        direccion = uow.direcciones_entrega.actualizar(direccion, campos)
        return DireccionRead.model_validate(direccion)


def eliminar_direccion(usuario_id: int, direccion_id: int) -> None:
    with UnidadDeTrabajo() as uow:
        direccion = uow.direcciones_entrega.obtener_por_id(direccion_id)
        if not direccion or direccion.usuario_id != usuario_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dirección no encontrada")
        uow.direcciones_entrega.eliminar(direccion)


def marcar_como_principal(usuario_id: int, direccion_id: int) -> DireccionRead:
    with UnidadDeTrabajo() as uow:
        direccion = uow.direcciones_entrega.obtener_por_id(direccion_id)
        if not direccion or direccion.usuario_id != usuario_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dirección no encontrada")
        uow.direcciones_entrega.marcar_principal(usuario_id, direccion_id)
        direccion = uow.direcciones_entrega.obtener_por_id(direccion_id)
        return DireccionRead.model_validate(direccion)
