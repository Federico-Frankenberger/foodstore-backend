from typing import Generic, Optional, Type, TypeVar

from sqlmodel import Session, SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], sesion: Session):
        self.model = model
        self.sesion = sesion

    def obtener_por_id(self, id: int) -> Optional[ModelType]:
        return self.sesion.get(self.model, id)

    def crear(self, obj: ModelType) -> ModelType:
        self.sesion.add(obj)
        self.sesion.flush()
        self.sesion.refresh(obj)
        return obj

    def actualizar(self, obj: ModelType) -> ModelType:
        self.sesion.add(obj)
        self.sesion.flush()
        self.sesion.refresh(obj)
        return obj

    def eliminar(self, obj: ModelType) -> None:
        self.sesion.delete(obj)
        self.sesion.flush()
