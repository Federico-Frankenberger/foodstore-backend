from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.deps import obtener_usuario_activo
from app.schemas.usuario import UsuarioPublico
from app.services import direccion_entrega_service as svc
from app.services.direccion_entrega_service import DireccionCrear, DireccionActualizar, DireccionRead

router = APIRouter(prefix="/direcciones", tags=["Mis Direcciones"])


@router.get("/", response_model=list[DireccionRead])
def listar(
    usuario_actual: Annotated[UsuarioPublico, Depends(obtener_usuario_activo)],
):
    return svc.listar_direcciones(usuario_actual.id)


@router.post("/", response_model=DireccionRead, status_code=status.HTTP_201_CREATED)
def crear(
    datos: DireccionCrear,
    usuario_actual: Annotated[UsuarioPublico, Depends(obtener_usuario_activo)],
):
    return svc.crear_direccion(usuario_actual.id, datos)


@router.get("/{direccion_id}", response_model=DireccionRead)
def detalle(
    direccion_id: int,
    usuario_actual: Annotated[UsuarioPublico, Depends(obtener_usuario_activo)],
):
    return svc.obtener_direccion(usuario_actual.id, direccion_id)


@router.patch("/{direccion_id}", response_model=DireccionRead)
def actualizar(
    direccion_id: int,
    datos: DireccionActualizar,
    usuario_actual: Annotated[UsuarioPublico, Depends(obtener_usuario_activo)],
):
    return svc.actualizar_direccion(usuario_actual.id, direccion_id, datos)


@router.delete("/{direccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    direccion_id: int,
    usuario_actual: Annotated[UsuarioPublico, Depends(obtener_usuario_activo)],
):
    svc.eliminar_direccion(usuario_actual.id, direccion_id)


@router.patch("/{direccion_id}/principal", response_model=DireccionRead)
def marcar_principal(
    direccion_id: int,
    usuario_actual: Annotated[UsuarioPublico, Depends(obtener_usuario_activo)],
):
    return svc.marcar_como_principal(usuario_actual.id, direccion_id)
