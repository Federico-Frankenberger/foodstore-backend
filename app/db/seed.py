from app.core.security import hashear_contrasena
from app.models.estado_pedido import EstadoPedido
from app.models.forma_pago import FormaPago
from app.models.rol import Rol
from app.models.unidad_medida import UnidadMedida
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol
from app.uow.uow import UnidadDeTrabajo

ROLES_INICIALES = [
    Rol(codigo="ADMIN",   nombre="Administrador",  descripcion="Acceso total sin restricciones"),
    Rol(codigo="STOCK",   nombre="Encargado Stock", descripcion="Actualiza stock y disponible"),
    Rol(codigo="PEDIDOS", nombre="Gestor Pedidos",  descripcion="Avanza estados CONFIRMADO → ENTREGADO"),
    Rol(codigo="CLIENT",  nombre="Cliente",         descripcion="Opera solo sus propios datos"),
]

ESTADOS_PEDIDO_INICIALES = [
    EstadoPedido(codigo="PENDIENTE",  descripcion="Pedido recibido, pendiente de confirmación", orden=1, es_terminal=False),
    EstadoPedido(codigo="CONFIRMADO", descripcion="Pedido confirmado, en preparación pendiente",  orden=2, es_terminal=False),
    EstadoPedido(codigo="EN_PREPARACION",    descripcion="En preparación",                               orden=3, es_terminal=False),
    EstadoPedido(codigo="EN_CAMINO",  descripcion="Enviado al cliente",                           orden=4, es_terminal=False),
    EstadoPedido(codigo="ENTREGADO",  descripcion="Entregado al cliente",                         orden=5, es_terminal=True),
    EstadoPedido(codigo="CANCELADO",  descripcion="Cancelado",                                    orden=6, es_terminal=True),
]

FORMAS_PAGO_INICIALES = [
    FormaPago(codigo="MERCADOPAGO",   descripcion="Checkout API MercadoPago",  habilitado=True),
    FormaPago(codigo="EFECTIVO",      descripcion="Pago en efectivo (pickup)", habilitado=True),
    FormaPago(codigo="TRANSFERENCIA", descripcion="Transferencia bancaria",    habilitado=True),
]

UNIDADES_INICIALES = [
    UnidadMedida(nombre="kilogramo",      simbolo="kg",  tipo="masa"),
    UnidadMedida(nombre="gramo",          simbolo="g",   tipo="masa"),
    UnidadMedida(nombre="litro",          simbolo="L",   tipo="volumen"),
    UnidadMedida(nombre="mililitro",      simbolo="mL",  tipo="volumen"),
    UnidadMedida(nombre="pieza",          simbolo="u",   tipo="unidad"),
    UnidadMedida(nombre="docena",         simbolo="doc", tipo="unidad"),
    UnidadMedida(nombre="metro cuadrado", simbolo="m²",  tipo="área"),
]

ADMIN_EMAIL = "admin@foodstore.com"
ADMIN_PASSWORD = "Admin1234!"


def ejecutar_seed() -> None:
    with UnidadDeTrabajo() as uow:
        for rol in ROLES_INICIALES:
            if not uow.roles.obtener_por_codigo(rol.codigo):
                uow.roles.crear(rol)
        for estado in ESTADOS_PEDIDO_INICIALES:
            if not uow.estados_pedido.obtener_por_codigo(estado.codigo):
                uow.estados_pedido.crear(estado)
        for forma in FORMAS_PAGO_INICIALES:
            if not uow.formas_pago.obtener_por_codigo(forma.codigo):
                uow.formas_pago.crear(forma)
        for unidad in UNIDADES_INICIALES:
            existentes = uow.unidades_medida.obtener_todos(tipo=unidad.tipo)
            simbolos = {u.simbolo for u in existentes}
            if unidad.simbolo not in simbolos:
                from app.schemas.unidad_medida import UnidadMedidaCrear
                uow.unidades_medida.crear(
                    UnidadMedidaCrear(
                        nombre=unidad.nombre,
                        simbolo=unidad.simbolo,
                        tipo=unidad.tipo,
                    )
                )

        if not uow.usuarios.obtener_por_email(ADMIN_EMAIL):
            admin = Usuario(
                nombre="Admin",
                apellido="Sistema",
                email=ADMIN_EMAIL,
                celular="0000000000",
                password_hash=hashear_contrasena(ADMIN_PASSWORD),
            )
            admin = uow.usuarios.crear(admin)
            uow.usuario_roles.asignar(
                UsuarioRol(usuario_id=admin.id, rol_codigo="ADMIN")
            )
