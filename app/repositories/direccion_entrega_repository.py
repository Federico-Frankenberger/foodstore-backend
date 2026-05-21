from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from app.models.direccion_entrega import DireccionEntrega


class DireccionEntregaRepositorio:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener_por_usuario(self, usuario_id: int) -> list[DireccionEntrega]:
        return list(
            self.sesion.exec(
                select(DireccionEntrega).where(
                    DireccionEntrega.usuario_id == usuario_id,
                    DireccionEntrega.deleted_at == None,
                )
            ).all()
        )

    def obtener_por_id(self, id: int) -> Optional[DireccionEntrega]:
        direccion = self.sesion.get(DireccionEntrega, id)
        if direccion and direccion.deleted_at is not None:
            return None
        return direccion

    def crear(self, direccion: DireccionEntrega) -> DireccionEntrega:
        self.sesion.add(direccion)
        self.sesion.flush()
        self.sesion.refresh(direccion)
        return direccion

    def actualizar(self, direccion: DireccionEntrega, campos: dict) -> DireccionEntrega:
        for campo, valor in campos.items():
            setattr(direccion, campo, valor)
        self.sesion.add(direccion)
        self.sesion.flush()
        self.sesion.refresh(direccion)
        return direccion

    def marcar_principal(self, usuario_id: int, direccion_id: int) -> None:
        # Quitar es_principal de todas las direcciones del usuario
        direcciones = self.obtener_por_usuario(usuario_id)
        for d in direcciones:
            d.es_principal = d.id == direccion_id
            self.sesion.add(d)
        self.sesion.flush()

    def eliminar(self, direccion: DireccionEntrega) -> None:
        direccion.deleted_at = datetime.now(timezone.utc)
        self.sesion.add(direccion)
        self.sesion.flush()
