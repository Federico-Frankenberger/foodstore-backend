from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decodificar_token_acceso


class OAuth2BearerConCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str | None:
        token = request.cookies.get("access_token")
        if not token:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No autenticado",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
        return token


esquema_oauth2 = OAuth2BearerConCookie(tokenUrl="/api/v1/auth/login")


async def obtener_usuario_actual(
    token: Annotated[str, Depends(esquema_oauth2)],
):
    # Importación local para evitar ciclo circular de imports
    from app.schemas.usuario import UsuarioPublico
    from app.uow.uow import UnidadDeTrabajo

    excepcion = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decodificar_token_acceso(token)
    if payload is None:
        raise excepcion

    usuario_id_str: str | None = payload.get("sub")
    if usuario_id_str is None:
        raise excepcion
    try:
        usuario_id = int(usuario_id_str)
    except ValueError:
        raise excepcion

    with UnidadDeTrabajo() as uow:
        usuario = uow.usuarios.obtener_por_id(usuario_id)
        if usuario is None or usuario.deleted_at is not None:
            raise excepcion
        roles: list[str] = payload.get("roles", [])
        return UsuarioPublico(
            id=usuario.id,
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            email=usuario.email,
            celular=usuario.celular,
            roles=roles,
            created_at=usuario.created_at,
        )


async def obtener_usuario_activo(
    usuario_actual=Depends(obtener_usuario_actual),
):
    # Con soft delete, si llegó hasta acá el usuario ya tiene deleted_at IS NULL
    # (verificado en obtener_usuario_actual). Nada más que chequear.
    return usuario_actual


def requerir_rol(roles_permitidos: list[str]):
    async def verificar_rol(
        usuario_actual=Depends(obtener_usuario_activo),
    ):
        tiene_rol = any(r in usuario_actual.roles for r in roles_permitidos)
        if not tiene_rol:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Permisos insuficientes. Tus roles son {usuario_actual.roles}. "
                    f"Se requiere uno de: {roles_permitidos}"
                ),
            )
        return usuario_actual

    return verificar_rol
