from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.usuario_rol import UsuarioRol


class UsuarioRolRepositorio:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener_roles_de_usuario(self, usuario_id: int) -> list[UsuarioRol]:
        ahora = datetime.now(timezone.utc)
        return list(
            self.sesion.exec(
                select(UsuarioRol).where(
                    UsuarioRol.usuario_id == usuario_id,
                    (UsuarioRol.expires_at == None) | (UsuarioRol.expires_at > ahora),
                )
            ).all()
        )

    def obtener(self, usuario_id: int, rol_codigo: str) -> Optional[UsuarioRol]:
        return self.sesion.get(UsuarioRol, (usuario_id, rol_codigo))

    def asignar(self, usuario_rol: UsuarioRol) -> UsuarioRol:
        self.sesion.add(usuario_rol)
        self.sesion.flush()
        self.sesion.refresh(usuario_rol)
        return usuario_rol

    def revocar(self, usuario_id: int, rol_codigo: str) -> bool:
        registro = self.obtener(usuario_id, rol_codigo)
        if not registro:
            return False
        self.sesion.delete(registro)
        self.sesion.flush()
        return True

    def revocar_todos(self, usuario_id: int) -> int:
        roles = self.obtener_roles_de_usuario(usuario_id)
        for ur in roles:
            self.sesion.delete(ur)
        self.sesion.flush()
        return len(roles)
