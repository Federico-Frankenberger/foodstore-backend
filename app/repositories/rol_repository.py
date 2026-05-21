from typing import Optional

from sqlmodel import Session, select

from app.models.rol import Rol


class RolRepositorio:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener_todos(self) -> list[Rol]:
        return list(self.sesion.exec(select(Rol)).all())

    def obtener_por_codigo(self, codigo: str) -> Optional[Rol]:
        return self.sesion.get(Rol, codigo)

    def crear(self, rol: Rol) -> Rol:
        self.sesion.add(rol)
        self.sesion.flush()
        self.sesion.refresh(rol)
        return rol
