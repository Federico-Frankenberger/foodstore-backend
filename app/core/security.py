import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import configuracion

contexto_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hashear_contrasena(plain: str) -> str:
    return contexto_pwd.hash(plain)


def verificar_contrasena(plain: str, hashed: str) -> bool:
    return contexto_pwd.verify(plain, hashed)


def crear_token_acceso(usuario_id: int, roles: list[str], delta: timedelta | None = None) -> str:
    expira = datetime.now(timezone.utc) + (
        delta or timedelta(minutes=configuracion.MINUTOS_EXPIRACION_TOKEN)
    )
    payload = {
        "sub": str(usuario_id),
        "roles": roles,
        "type": "access",
        "exp": expira,
    }
    return jwt.encode(payload, configuracion.SECRET_KEY, algorithm=configuracion.ALGORITMO)


def decodificar_token_acceso(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            configuracion.SECRET_KEY,
            algorithms=[configuracion.ALGORITMO],
        )
        if payload.get("type") != "access":
            return None
        return payload
    except jwt.PyJWTError:
        return None


def generar_refresh_token() -> tuple[str, str]:
    """Devuelve (token_raw, token_hash). Solo el hash se persiste en BD."""
    token_raw = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token_raw.encode()).hexdigest()
    return token_raw, token_hash


def hashear_token(token_raw: str) -> str:
    return hashlib.sha256(token_raw.encode()).hexdigest()
