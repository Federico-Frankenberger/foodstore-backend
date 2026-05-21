from app.database import get_session
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.direccion_entrega_repository import DireccionEntregaRepositorio
from app.repositories.estado_pedido_repository import EstadoPedidoRepositorio
from app.repositories.forma_pago_repository import FormaPagoRepositorio
from app.repositories.historial_estado_pedido_repository import HistorialEstadoPedidoRepositorio
from app.repositories.ingrediente_repository import IngredienteRepository
from app.repositories.pedido_repository import PedidoRepositorio
from app.repositories.producto_repository import ProductoRepository
from app.repositories.refresh_token_repository import RefreshTokenRepositorio
from app.repositories.rol_repository import RolRepositorio
from app.repositories.unidad_medida_repository import UnidadMedidaRepositorio
from app.repositories.usuario_repository import UsuarioRepositorio
from app.repositories.usuario_rol_repository import UsuarioRolRepositorio


class UnidadDeTrabajo:
    def __init__(self, session_factory=None):
        self.session_factory = session_factory or get_session

    def __enter__(self) -> "UnidadDeTrabajo":
        self.sesion = self.session_factory()
        self.categorias = CategoriaRepository(self.sesion)
        self.ingredientes = IngredienteRepository(self.sesion)
        self.productos = ProductoRepository(self.sesion)
        self.unidades_medida = UnidadMedidaRepositorio(self.sesion)
        self.usuarios = UsuarioRepositorio(self.sesion)
        self.roles = RolRepositorio(self.sesion)
        self.usuario_roles = UsuarioRolRepositorio(self.sesion)
        self.direcciones_entrega = DireccionEntregaRepositorio(self.sesion)
        self.refresh_tokens = RefreshTokenRepositorio(self.sesion)
        self.estados_pedido = EstadoPedidoRepositorio(self.sesion)
        self.formas_pago = FormaPagoRepositorio(self.sesion)
        self.pedidos = PedidoRepositorio(self.sesion)
        self.historial_pedidos = HistorialEstadoPedidoRepositorio(self.sesion)
        return self

    def __exit__(self, tipo_exc, valor_exc, traza_exc):
        try:
            if tipo_exc:
                self.sesion.rollback()
            else:
                try:
                    self.sesion.commit()
                except Exception:
                    self.sesion.rollback()
                    raise
        finally:
            self.sesion.close()
