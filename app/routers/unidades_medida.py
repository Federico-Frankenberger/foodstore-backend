from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.deps import requerir_rol
from app.schemas.unidad_medida import UnidadMedidaActualizar, UnidadMedidaCrear, UnidadMedidaPublica
from app.services import unidad_medida_service

router = APIRouter(prefix="/unidades-medida", tags=["Unidades de Medida"])

IdUnidad = Annotated[int, Path(gt=0, description="ID de la unidad de medida")]


@router.post("/", response_model=UnidadMedidaPublica, status_code=status.HTTP_201_CREATED)
def crear_unidad_medida(
    datos: UnidadMedidaCrear,
    _: Annotated[object, Depends(requerir_rol(["ADMIN"]))],
):
    try:
        return unidad_medida_service.crear_unidad_medida(datos)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/", response_model=List[UnidadMedidaPublica])
def listar_unidades_medida(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    tipo: Annotated[Optional[str], Query(description="Filtrar por tipo: masa, volumen, unidad, área")] = None,
):
    return unidad_medida_service.obtener_unidades_medida(skip, limit, tipo)


@router.get("/{id}", response_model=UnidadMedidaPublica)
def detalle_unidad_medida(id: IdUnidad):
    unidad = unidad_medida_service.obtener_unidad_medida(id)
    if not unidad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidad de medida no encontrada")
    return unidad


@router.patch("/{id}", response_model=UnidadMedidaPublica)
def actualizar_unidad_medida(
    id: IdUnidad,
    datos: UnidadMedidaActualizar,
    _: Annotated[object, Depends(requerir_rol(["ADMIN"]))],
):
    try:
        unidad = unidad_medida_service.actualizar_unidad_medida(id, datos)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not unidad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidad de medida no encontrada")
    return unidad


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_unidad_medida(
    id: IdUnidad,
    _: Annotated[object, Depends(requerir_rol(["ADMIN"]))],
):
    encontrada = unidad_medida_service.eliminar_unidad_medida(id)
    if not encontrada:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidad de medida no encontrada")
