from typing import List, Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.models.unidad_medida import UnidadMedida
from app.schemas.unidad_medida import UnidadMedidaCrear, UnidadMedidaActualizar


class UnidadMedidaRepositorio:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def crear(self, datos: UnidadMedidaCrear) -> UnidadMedida:
        unidad = UnidadMedida(**datos.model_dump())
        self.sesion.add(unidad)
        self.sesion.flush()
        self.sesion.refresh(unidad)
        return unidad

    def obtener_por_id(self, id: int) -> Optional[UnidadMedida]:
        return self.sesion.get(UnidadMedida, id)

    def obtener_todos(
        self,
        skip: int = 0,
        limit: int = 50,
        tipo: Optional[str] = None,
    ) -> List[UnidadMedida]:
        consulta = select(UnidadMedida)
        if tipo:
            consulta = consulta.where(UnidadMedida.tipo == tipo)
        consulta = consulta.offset(skip).limit(limit)
        return list(self.sesion.exec(consulta).all())

    def actualizar(self, unidad: UnidadMedida, campos: dict) -> UnidadMedida:
        for campo, valor in campos.items():
            setattr(unidad, campo, valor)
        self.sesion.add(unidad)
        self.sesion.flush()
        self.sesion.refresh(unidad)
        return unidad

    def eliminar(self, unidad: UnidadMedida) -> None:
        self.sesion.delete(unidad)
        self.sesion.flush()
