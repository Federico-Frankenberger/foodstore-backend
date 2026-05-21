from typing import List, Optional

from sqlmodel import Session, select

from app.models.forma_pago import FormaPago


class FormaPagoRepositorio:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener_por_codigo(self, codigo: str) -> Optional[FormaPago]:
        return self.sesion.get(FormaPago, codigo)

    def obtener_todos(self, solo_habilitadas: bool = True) -> List[FormaPago]:
        consulta = select(FormaPago)
        if solo_habilitadas:
            consulta = consulta.where(FormaPago.habilitado == True)
        return list(self.sesion.exec(consulta).all())

    def crear(self, forma_pago: FormaPago) -> FormaPago:
        self.sesion.add(forma_pago)
        self.sesion.flush()
        self.sesion.refresh(forma_pago)
        return forma_pago
