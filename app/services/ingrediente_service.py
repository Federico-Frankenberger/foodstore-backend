from typing import List, Optional

from sqlalchemy.exc import IntegrityError

from app.schemas.ingrediente import IngredienteCreate, IngredienteRead, IngredienteUpdate
from app.uow.uow import UnidadDeTrabajo


def crear_ingrediente(datos: IngredienteCreate) -> IngredienteRead:
    try:
        with UnidadDeTrabajo() as uow:
            ingrediente = uow.ingredientes.crear(datos)
            return IngredienteRead.model_validate(ingrediente)
    except IntegrityError:
        raise ValueError(f"Ya existe un ingrediente con el nombre '{datos.nombre}'")


def obtener_ingredientes(
    skip: int = 0,
    limit: int = 10,
    nombre: Optional[str] = None,
) -> List[IngredienteRead]:
    with UnidadDeTrabajo() as uow:
        ingredientes = uow.ingredientes.obtener_todos(skip, limit, nombre)
        return [IngredienteRead.model_validate(i) for i in ingredientes]


def obtener_ingrediente(id: int) -> Optional[IngredienteRead]:
    with UnidadDeTrabajo() as uow:
        ingrediente = uow.ingredientes.obtener_por_id(id)
        if not ingrediente:
            return None
        return IngredienteRead.model_validate(ingrediente)


def actualizar_ingrediente(id: int, datos: IngredienteUpdate) -> Optional[IngredienteRead]:
    with UnidadDeTrabajo() as uow:
        ingrediente = uow.ingredientes.obtener_por_id(id)
        if not ingrediente:
            return None
        ingrediente = uow.ingredientes.actualizar(ingrediente, datos.model_dump(exclude_unset=True))
        return IngredienteRead.model_validate(ingrediente)


def eliminar_ingrediente(id: int) -> bool:
    with UnidadDeTrabajo() as uow:
        ingrediente = uow.ingredientes.obtener_por_id(id)
        if not ingrediente:
            return False
        if uow.ingredientes.tiene_productos_activos(id):
            raise ValueError("No se puede eliminar: el ingrediente tiene productos activos")
        uow.ingredientes.eliminar(ingrediente)
        return True
