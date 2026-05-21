from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.config import configuracion
from app.core.security import (
    crear_token_acceso,
    generar_refresh_token,
    hashear_contrasena,
    hashear_token,
    verificar_contrasena,
)
from app.models.refresh_token import RefreshToken
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol
from app.schemas.usuario import Token, UsuarioAdminUpdate, UsuarioCrear, UsuarioPublico
from app.uow.uow import UnidadDeTrabajo


def _roles_de_usuario(uow: UnidadDeTrabajo, usuario_id: int) -> list[str]:
    return [ur.rol_codigo for ur in uow.usuario_roles.obtener_roles_de_usuario(usuario_id)]


def _construir_usuario_publico(usuario: Usuario, roles: list[str]) -> UsuarioPublico:
    return UsuarioPublico(
        id=usuario.id,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        celular=usuario.celular,
        roles=roles,
        created_at=usuario.created_at,
    )


def registrar_usuario(datos: UsuarioCrear) -> UsuarioPublico:
    with UnidadDeTrabajo() as uow:
        if uow.usuarios.obtener_por_email(datos.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está registrado",
            )
        usuario = Usuario(
            nombre=datos.nombre,
            apellido=datos.apellido,
            email=datos.email,
            celular=datos.celular,
            password_hash=hashear_contrasena(datos.contrasena),
        )
        usuario = uow.usuarios.crear(usuario)
        # Asignar rol CLIENT por defecto
        uow.usuario_roles.asignar(UsuarioRol(usuario_id=usuario.id, rol_codigo="CLIENT"))
        return _construir_usuario_publico(usuario, ["CLIENT"])


def autenticar_usuario(email: str, contrasena: str) -> tuple[Token, str, str]:
    """Devuelve (Token, access_token_raw, refresh_token_raw)."""
    from datetime import timedelta

    with UnidadDeTrabajo() as uow:
        usuario = uow.usuarios.obtener_por_email(email)
        if not usuario or not verificar_contrasena(contrasena, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if usuario.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cuenta de usuario deshabilitada",
            )
        roles = _roles_de_usuario(uow, usuario.id)
        access_token = crear_token_acceso(usuario.id, roles)

        token_raw, token_hash = generar_refresh_token()
        expira = datetime.now(timezone.utc) + timedelta(
            days=configuracion.DIAS_EXPIRACION_REFRESH_TOKEN
        )
        uow.refresh_tokens.crear(
            RefreshToken(
                usuario_id=usuario.id,
                token_hash=token_hash,
                expires_at=expira,
            )
        )
        token_schema = Token(
            access_token=access_token,
            refresh_token=token_raw,
            token_type="bearer",
            expira_en=configuracion.MINUTOS_EXPIRACION_TOKEN * 60,
        )
        return token_schema, access_token, token_raw


def refrescar_token(token_raw: str) -> tuple[Token, str, str]:
    """Valida el refresh token, lo rota y emite nuevos tokens. Devuelve (Token, access_token_raw, nuevo_refresh_token_raw)."""
    from datetime import timedelta

    ahora = datetime.now(timezone.utc)
    token_hash = hashear_token(token_raw)

    with UnidadDeTrabajo() as uow:
        rt = uow.refresh_tokens.obtener_por_hash(token_hash)
        if rt is None or rt.expires_at <= ahora:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if rt.revoked_at is not None:
            uow.refresh_tokens.revocar_todos_del_usuario(rt.usuario_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revocado reutilizado — todas las sesiones han sido invalidadas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        usuario = uow.usuarios.obtener_por_id(rt.usuario_id)
        if not usuario or usuario.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o deshabilitado",
            )

        uow.refresh_tokens.revocar(rt)

        nuevo_token_raw, nuevo_token_hash = generar_refresh_token()
        expira = datetime.now(timezone.utc) + timedelta(
            days=configuracion.DIAS_EXPIRACION_REFRESH_TOKEN
        )
        uow.refresh_tokens.crear(
            RefreshToken(
                usuario_id=usuario.id,
                token_hash=nuevo_token_hash,
                expires_at=expira,
            )
        )

        roles = _roles_de_usuario(uow, usuario.id)
        access_token = crear_token_acceso(usuario.id, roles)
        token_schema = Token(
            access_token=access_token,
            refresh_token=nuevo_token_raw,
            token_type="bearer",
            expira_en=configuracion.MINUTOS_EXPIRACION_TOKEN * 60,
        )
        return token_schema, access_token, nuevo_token_raw


def revocar_refresh_token(token_raw: str) -> None:
    token_hash = hashear_token(token_raw)
    with UnidadDeTrabajo() as uow:
        rt = uow.refresh_tokens.obtener_por_hash(token_hash)
        if rt and rt.revoked_at is None:
            uow.refresh_tokens.revocar(rt)


def listar_usuarios(rol: str | None = None, skip: int = 0, limit: int = 10) -> list[UsuarioPublico]:
    with UnidadDeTrabajo() as uow:
        usuarios = uow.usuarios.obtener_todos(rol=rol, skip=skip, limit=limit)
        resultado = []
        for u in usuarios:
            roles = _roles_de_usuario(uow, u.id)
            resultado.append(_construir_usuario_publico(u, roles))
        return resultado


def deshabilitar_usuario(usuario_id: int) -> UsuarioPublico:
    with UnidadDeTrabajo() as uow:
        usuario = uow.usuarios.obtener_por_id(usuario_id)
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        if usuario.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El usuario ya está deshabilitado")
        usuario.deleted_at = datetime.now(timezone.utc)
        usuario = uow.usuarios.actualizar(usuario)
        roles = _roles_de_usuario(uow, usuario.id)
        return _construir_usuario_publico(usuario, roles)


def habilitar_usuario(usuario_id: int) -> UsuarioPublico:
    with UnidadDeTrabajo() as uow:
        usuario = uow.usuarios.obtener_por_id(usuario_id)
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        usuario.deleted_at = None
        usuario = uow.usuarios.actualizar(usuario)
        roles = _roles_de_usuario(uow, usuario.id)
        return _construir_usuario_publico(usuario, roles)


def asignar_rol(usuario_id: int, rol_codigo: str, asignado_por_id: int) -> UsuarioPublico:
    with UnidadDeTrabajo() as uow:
        usuario = uow.usuarios.obtener_por_id(usuario_id)
        if not usuario or usuario.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        if not uow.roles.obtener_por_codigo(rol_codigo):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rol '{rol_codigo}' no existe")
        if uow.usuario_roles.obtener(usuario_id, rol_codigo):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El usuario ya tiene ese rol")
        uow.usuario_roles.asignar(
            UsuarioRol(usuario_id=usuario_id, rol_codigo=rol_codigo, asignado_por_id=asignado_por_id)
        )
        roles = _roles_de_usuario(uow, usuario_id)
        return _construir_usuario_publico(usuario, roles)


def quitar_rol(usuario_id: int, rol_codigo: str) -> UsuarioPublico:
    with UnidadDeTrabajo() as uow:
        usuario = uow.usuarios.obtener_por_id(usuario_id)
        if not usuario or usuario.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        if not uow.usuario_roles.revocar(usuario_id, rol_codigo):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El usuario no tiene ese rol")
        roles = _roles_de_usuario(uow, usuario_id)
        return _construir_usuario_publico(usuario, roles)


def actualizar_usuario_admin(usuario_id: int, datos: UsuarioAdminUpdate, admin_id: int) -> UsuarioPublico:
    with UnidadDeTrabajo() as uow:
        usuario = uow.usuarios.obtener_por_id(usuario_id)
        if not usuario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

        if datos.activo is not None:
            usuario.deleted_at = None if datos.activo else datetime.now(timezone.utc)
            usuario = uow.usuarios.actualizar(usuario)

        if datos.roles is not None:
            for rol_codigo in datos.roles:
                if not uow.roles.obtener_por_codigo(rol_codigo):
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Rol '{rol_codigo}' no existe",
                    )
            roles_actuales = [ur.rol_codigo for ur in uow.usuario_roles.obtener_roles_de_usuario(usuario_id)]
            if "ADMIN" in roles_actuales and "ADMIN" not in datos.roles:
                todos_admins = uow.usuarios.obtener_todos(rol="ADMIN", skip=0, limit=1000)
                if len(todos_admins) <= 1:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="No se puede quitar el rol ADMIN al último administrador",
                    )
            uow.usuario_roles.revocar_todos(usuario_id)
            for rol_codigo in datos.roles:
                uow.usuario_roles.asignar(
                    UsuarioRol(usuario_id=usuario_id, rol_codigo=rol_codigo, asignado_por_id=admin_id)
                )

        uow.refresh_tokens.revocar_todos_del_usuario(usuario_id)

        roles = _roles_de_usuario(uow, usuario_id)
        return _construir_usuario_publico(usuario, roles)
