from pydantic import BaseModel

from app.uow.uow import UnidadDeTrabajo


class RolRead(BaseModel):
    codigo: str
    nombre: str
    descripcion: str | None = None

    model_config = {"from_attributes": True}


def listar_roles() -> list[RolRead]:
    with UnidadDeTrabajo() as uow:
        return [RolRead.model_validate(r) for r in uow.roles.obtener_todos()]
