from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepositorio(BaseRepository[RefreshToken]):
    def __init__(self, sesion: Session):
        super().__init__(RefreshToken, sesion)

    def crear(self, refresh_token: RefreshToken) -> RefreshToken:
        self.sesion.add(refresh_token)
        self.sesion.flush()
        self.sesion.refresh(refresh_token)
        return refresh_token

    def obtener_por_hash(self, token_hash: str) -> Optional[RefreshToken]:
        return self.sesion.exec(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        ).first()

    def revocar(self, refresh_token: RefreshToken) -> None:
        refresh_token.revoked_at = datetime.now(timezone.utc)
        self.sesion.add(refresh_token)
        self.sesion.flush()

    def revocar_todos_del_usuario(self, usuario_id: int) -> int:
        ahora = datetime.now(timezone.utc)
        activos = list(
            self.sesion.exec(
                select(RefreshToken)
                .where(RefreshToken.usuario_id == usuario_id)
                .where(RefreshToken.revoked_at == None)  # noqa: E711
            ).all()
        )
        for rt in activos:
            rt.revoked_at = ahora
            self.sesion.add(rt)
        self.sesion.flush()
        return len(activos)

    def limpiar_expirados(self) -> int:
        ahora = datetime.now(timezone.utc)
        expirados = list(
            self.sesion.exec(
                select(RefreshToken).where(RefreshToken.expires_at < ahora)
            ).all()
        )
        for rt in expirados:
            self.sesion.delete(rt)
        self.sesion.flush()
        return len(expirados)
