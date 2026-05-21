from typing import List, Optional

from sqlalchemy.exc import IntegrityError

from app.schemas.unidad_medida import UnidadMedidaActualizar, UnidadMedidaCrear, UnidadMedidaPublica
from app.uow.uow import UnidadDeTrabajo


def crear_unidad_medida(datos: UnidadMedidaCrear) -> UnidadMedidaPublica:
    try:
        with UnidadDeTrabajo() as uow:
            unidad = uow.unidades_medida.crear(datos)
            return UnidadMedidaPublica.model_validate(unidad)
    except IntegrityError:
        raise ValueError(f"Ya existe una unidad con ese nombre o símbolo")


def obtener_unidades_medida(
    skip: int = 0,
    limit: int = 50,
    tipo: Optional[str] = None,
) -> List[UnidadMedidaPublica]:
    with UnidadDeTrabajo() as uow:
        unidades = uow.unidades_medida.obtener_todos(skip, limit, tipo)
        return [UnidadMedidaPublica.model_validate(u) for u in unidades]


def obtener_unidad_medida(id: int) -> Optional[UnidadMedidaPublica]:
    with UnidadDeTrabajo() as uow:
        unidad = uow.unidades_medida.obtener_por_id(id)
        if not unidad:
            return None
        return UnidadMedidaPublica.model_validate(unidad)


def actualizar_unidad_medida(id: int, datos: UnidadMedidaActualizar) -> Optional[UnidadMedidaPublica]:
    try:
        with UnidadDeTrabajo() as uow:
            unidad = uow.unidades_medida.obtener_por_id(id)
            if not unidad:
                return None
            unidad = uow.unidades_medida.actualizar(unidad, datos.model_dump(exclude_unset=True))
            return UnidadMedidaPublica.model_validate(unidad)
    except IntegrityError:
        raise ValueError("Ya existe una unidad con ese nombre o símbolo")


def eliminar_unidad_medida(id: int) -> bool:
    with UnidadDeTrabajo() as uow:
        unidad = uow.unidades_medida.obtener_por_id(id)
        if not unidad:
            return False
        uow.unidades_medida.eliminar(unidad)
        return True
