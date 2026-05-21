from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol
from app.repositories.base import BaseRepository


class UsuarioRepositorio(BaseRepository[Usuario]):
    def __init__(self, sesion: Session):
        super().__init__(Usuario, sesion)

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        return self.sesion.exec(
            select(Usuario).where(Usuario.email == email)
        ).first()

    def obtener_todos(self, rol: Optional[str] = None, skip: int = 0, limit: int = 10) -> list[Usuario]:
        consulta = select(Usuario).where(Usuario.deleted_at == None)
        if rol is not None:
            ahora = datetime.now(timezone.utc)
            consulta = (
                consulta
                .join(UsuarioRol, UsuarioRol.usuario_id == Usuario.id)
                .where(
                    UsuarioRol.rol_codigo == rol,
                    (UsuarioRol.expires_at == None) | (UsuarioRol.expires_at > ahora),
                )
                .distinct()
            )
        consulta = consulta.offset(skip).limit(limit)
        return list(self.sesion.exec(consulta).all())
