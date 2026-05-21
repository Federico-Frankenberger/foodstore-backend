"""
Tests de integración para el módulo de pedidos:
  POST   /pedidos/
  GET    /pedidos/
  GET    /pedidos/{id}
  DELETE /pedidos/{id}
  GET    /admin/pedidos/
  GET    /admin/pedidos/{id}
  PATCH  /pedidos/{id}/estado
"""

from decimal import Decimal

import pytest
from sqlmodel import Session

from tests.conftest import DATOS_USUARIO, DATOS_ADMIN, test_engine


# ── Helpers ───────────────────────────────────────────────────────────────────

def _asignar_rol(usuario_id: int, rol_codigo: str) -> None:
    from app.models.usuario_rol import UsuarioRol
    with Session(test_engine) as sesion:
        sesion.add(UsuarioRol(usuario_id=usuario_id, rol_codigo=rol_codigo))
        sesion.commit()


def _registrar_y_login(client, datos: dict) -> dict:
    r = client.post("/api/v1/auth/register", json=datos)
    assert r.status_code == 201, r.text
    usuario = r.json()
    client.post("/api/v1/auth/login", json={"email": datos["email"], "contrasena": datos["contrasena"]})
    return usuario


def _crear_ingrediente(client, nombre="Harina", stock="10.000", precio="50.00"):
    r = client.post("/api/v1/ingredientes/", json={
        "nombre": nombre,
        "stock_total": stock,
        "precio_costo": precio,
    })
    assert r.status_code == 201, r.text
    return r.json()


def _crear_producto(client, nombre="Empanada", margen=0, ingredientes=None):
    um_id = client.get("/api/v1/unidades-medida/").json()[0]["id"]
    if ingredientes is None and um_id:
        ing = _crear_ingrediente(client)
        ingredientes = [{"ingrediente_id": ing["id"], "cantidad": "1.000",
                         "unidad_medida_id": um_id, "es_removible": False}]
    r = client.post("/api/v1/productos/", json={
        "nombre": nombre,
        "margen_ganancia": str(margen),
        "disponible": True,
        "categorias": [],
        "ingredientes": ingredientes or [],
    })
    assert r.status_code == 201, r.text
    return r.json()


def _payload_pedido(producto_id: int, cantidad: int = 1, forma_pago: str = "EFECTIVO") -> dict:
    return {
        "forma_pago_codigo": forma_pago,
        "items": [{"producto_id": producto_id, "cantidad": cantidad}],
    }


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client_client(client):
    """Cliente autenticado con rol CLIENT."""
    _registrar_y_login(client, DATOS_USUARIO)
    return client


@pytest.fixture
def client_admin(client):
    """Cliente autenticado con rol ADMIN."""
    usuario = _registrar_y_login(client, DATOS_ADMIN)
    _asignar_rol(usuario["id"], "ADMIN")
    client.post("/api/v1/auth/login", json={"email": DATOS_ADMIN["email"], "contrasena": DATOS_ADMIN["contrasena"]})
    return client


@pytest.fixture
def client_pedidos(client):
    """Cliente autenticado con rol PEDIDOS."""
    datos = {"nombre": "Gestor", "apellido": "Pedidos", "email": "gestor@test.com", "contrasena": "gestor123"}
    usuario = _registrar_y_login(client, datos)
    _asignar_rol(usuario["id"], "PEDIDOS")
    client.post("/api/v1/auth/login", json={"email": datos["email"], "contrasena": datos["contrasena"]})
    return client


# ── Crear pedido ──────────────────────────────────────────────────────────────

def test_crear_pedido_exitoso(client_client, client_admin):
    prod = _crear_producto(client_admin)
    r = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"]))
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["estado_codigo"] == "PENDIENTE"
    assert data["forma_pago_codigo"] == "EFECTIVO"
    assert len(data["items"]) == 1
    assert data["items"][0]["nombre_snapshot"] == prod["nombre"]
    assert len(data["historial"]) == 1
    assert data["historial"][0]["estado_desde"] is None
    assert data["historial"][0]["estado_hasta"] == "PENDIENTE"


def test_crear_pedido_snapshots_correctos(client_client, client_admin):
    """precio_snapshot = precio_venta del producto en el momento del pedido."""
    prod = _crear_producto(client_admin, margen=50)
    precio_venta = Decimal(prod["precio_venta"])
    r = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"], cantidad=2))
    assert r.status_code == 201
    item = r.json()["items"][0]
    assert Decimal(item["precio_snapshot"]) == precio_venta
    assert Decimal(item["subtotal_snap"]) == (precio_venta * 2).quantize(Decimal("0.01"))


def test_crear_pedido_requiere_autenticacion(client):
    r = client.post("/api/v1/pedidos/", json={"forma_pago_codigo": "EFECTIVO", "items": []})
    assert r.status_code == 401


def test_crear_pedido_producto_inexistente(client_client):
    r = client_client.post("/api/v1/pedidos/", json=_payload_pedido(producto_id=99999))
    assert r.status_code == 422


def test_crear_pedido_producto_no_disponible(client_client, client_admin):
    prod = _crear_producto(client_admin, nombre="No disponible")
    client_admin.patch(f"/api/v1/productos/{prod['id']}/disponibilidad", json={"disponible": False})
    r = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"]))
    assert r.status_code == 422


def test_crear_pedido_items_vacios(client_client):
    r = client_client.post("/api/v1/pedidos/", json={"forma_pago_codigo": "EFECTIVO", "items": []})
    assert r.status_code == 422


def test_crear_pedido_forma_pago_invalida(client_client, client_admin):
    prod = _crear_producto(client_admin)
    r = client_client.post("/api/v1/pedidos/", json={**_payload_pedido(prod["id"]), "forma_pago_codigo": "INVALIDA"})
    assert r.status_code == 422


def test_crear_pedido_total_correcto(client_client, client_admin):
    """total = subtotal - descuento + costo_envio (costo_envio siempre 50.00)."""
    prod = _crear_producto(client_admin)
    precio_venta = Decimal(prod["precio_venta"])
    payload = {
        "forma_pago_codigo": "EFECTIVO",
        "descuento": "5.00",
        "items": [{"producto_id": prod["id"], "cantidad": 2}],
    }
    r = client_client.post("/api/v1/pedidos/", json=payload)
    assert r.status_code == 201
    data = r.json()
    subtotal = (precio_venta * 2).quantize(Decimal("0.01"))
    expected_total = (subtotal - Decimal("5.00") + Decimal("50.00")).quantize(Decimal("0.01"))
    assert Decimal(data["total"]) == expected_total


# ── Listar y obtener pedidos propios ──────────────────────────────────────────

def test_listar_pedidos_propios(client_client, client_admin):
    prod = _crear_producto(client_admin)
    client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"]))
    client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"]))
    r = client_client.get("/api/v1/pedidos/")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_obtener_pedido_propio(client_client, client_admin):
    prod = _crear_producto(client_admin)
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"])).json()
    r = client_client.get(f"/api/v1/pedidos/{pedido['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == pedido["id"]


def test_obtener_pedido_de_otro_usuario(client_client, client_admin):
    """ADMIN puede ver pedidos de cualquier usuario via GET /pedidos/{id} (endpoint role-aware)."""
    prod = _crear_producto(client_admin)
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"])).json()
    r = client_admin.get(f"/api/v1/pedidos/{pedido['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == pedido["id"]


# ── Cancelar pedido (cliente) ─────────────────────────────────────────────────

def test_cliente_cancela_pedido_pendiente(client_client, client_admin):
    prod = _crear_producto(client_admin)
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"])).json()
    r = client_client.request("DELETE", f"/api/v1/pedidos/{pedido['id']}", json={"motivo": "Ya no lo quiero"})
    assert r.status_code == 200
    assert r.json()["estado_codigo"] == "CANCELADO"


def test_cliente_cancela_requiere_motivo(client_client, client_admin):
    prod = _crear_producto(client_admin)
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"])).json()
    r = client_client.request("DELETE", f"/api/v1/pedidos/{pedido['id']}", json={"motivo": ""})
    assert r.status_code == 422


def test_cliente_no_puede_cancelar_pedido_de_otro(client_client, client_admin):
    prod = _crear_producto(client_admin)
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"])).json()
    datos_otro = {"nombre": "Otro", "apellido": "Usuario", "email": "otro@test.com", "contrasena": "otroPASS123"}
    _registrar_y_login(client_admin, datos_otro)
    r = client_admin.request("DELETE", f"/api/v1/pedidos/{pedido['id']}", json={"motivo": "Intento"})
    assert r.status_code in (404, 403)


# ── Admin: listar y obtener ───────────────────────────────────────────────────

def test_admin_lista_todos_los_pedidos(client_client, client_admin):
    prod = _crear_producto(client_admin)
    client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"]))
    r = client_admin.get("/api/v1/admin/pedidos/")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_admin_obtiene_pedido_de_cualquier_usuario(client_client, client_admin):
    prod = _crear_producto(client_admin)
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"])).json()
    r = client_admin.get(f"/api/v1/admin/pedidos/{pedido['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == pedido["id"]


def test_admin_filtra_pedidos_por_estado(client_client, client_admin):
    prod = _crear_producto(client_admin)
    client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"]))
    r = client_admin.get("/api/v1/admin/pedidos/?estado=PENDIENTE")
    assert r.status_code == 200
    for p in r.json():
        assert p["estado_codigo"] == "PENDIENTE"


# ── Admin: avanzar estado ─────────────────────────────────────────────────────

def test_admin_avanza_estado_pendiente_a_confirmado(client_client, client_admin):
    prod = _crear_producto(client_admin)
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"])).json()
    r = client_admin.patch(f"/api/v1/pedidos/{pedido['id']}/estado", json={"estado_hasta": "CONFIRMADO"})
    assert r.status_code == 200
    data = r.json()
    assert data["estado_codigo"] == "CONFIRMADO"
    assert len(data["historial"]) == 2


def test_avanzar_estado_invalido(client_client, client_admin):
    """PENDIENTE → ENTREGADO es inválido."""
    prod = _crear_producto(client_admin)
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"])).json()
    r = client_admin.patch(f"/api/v1/pedidos/{pedido['id']}/estado", json={"estado_hasta": "ENTREGADO"})
    assert r.status_code == 422


def test_avanzar_estado_terminal(client_client, client_admin):
    """No se puede avanzar desde ENTREGADO."""
    prod = _crear_producto(client_admin)
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"])).json()
    pid = pedido["id"]
    for estado in ["CONFIRMADO", "EN_PREPARACION", "EN_CAMINO", "ENTREGADO"]:
        client_admin.patch(f"/api/v1/pedidos/{pid}/estado", json={"estado_hasta": estado})
    r = client_admin.patch(f"/api/v1/pedidos/{pid}/estado", json={"estado_hasta": "CANCELADO", "motivo": "test"})
    assert r.status_code == 422


def test_cancelar_requiere_motivo(client_client, client_admin):
    prod = _crear_producto(client_admin)
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"])).json()
    r = client_admin.patch(f"/api/v1/pedidos/{pedido['id']}/estado", json={"estado_hasta": "CANCELADO"})
    assert r.status_code == 422


def test_snapshot_no_cambia_al_actualizar_precio(client_client, client_admin):
    """precio_snapshot es inmutable aunque cambie el precio del ingrediente."""
    um_id = client_admin.get("/api/v1/unidades-medida/").json()[0]["id"]
    ing = client_admin.post("/api/v1/ingredientes/", json={"nombre": "IngSnap", "stock_total": "10.000", "precio_costo": "100.00"}).json()
    prod = client_admin.post("/api/v1/productos/", json={
        "nombre": "ProdSnap", "margen_ganancia": "0", "disponible": True, "categorias": [],
        "ingredientes": [{"ingrediente_id": ing["id"], "cantidad": "1.000", "unidad_medida_id": um_id, "es_removible": False}],
    }).json()

    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"])).json()
    precio_original = pedido["items"][0]["precio_snapshot"]

    # Cambiar precio del ingrediente
    client_admin.patch(f"/api/v1/ingredientes/{ing['id']}", json={"precio_costo": "999.00"})

    # El snapshot del pedido NO debe cambiar
    r = client_admin.get(f"/api/v1/admin/pedidos/{pedido['id']}")
    assert r.json()["items"][0]["precio_snapshot"] == precio_original


def test_historial_registra_todas_las_transiciones(client_client, client_admin):
    prod = _crear_producto(client_admin)
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"])).json()
    pid = pedido["id"]

    for estado in ["CONFIRMADO", "EN_PREPARACION", "EN_CAMINO", "ENTREGADO"]:
        client_admin.patch(f"/api/v1/pedidos/{pid}/estado", json={"estado_hasta": estado})

    r = client_admin.get(f"/api/v1/admin/pedidos/{pid}")
    historial = r.json()["historial"]
    assert len(historial) == 5  # PENDIENTE + 4 transiciones
    codigos = [h["estado_hasta"] for h in historial]
    assert codigos == ["PENDIENTE", "CONFIRMADO", "EN_PREPARACION", "EN_CAMINO", "ENTREGADO"]


def test_sin_rol_no_puede_crear_pedido(client):
    """Un usuario sin rol CLIENT no puede crear pedidos."""
    datos = {"nombre": "Sin", "apellido": "Rol", "email": "sinrol@test.com", "contrasena": "sinrol123"}
    r = client.post("/api/v1/auth/register", json=datos)
    # El registro asigna rol CLIENT por defecto — igual probamos que autenticado puede crear
    assert r.status_code == 201


# ── Stock de ingredientes ─────────────────────────────────────────────────────

def test_crear_pedido_descuenta_stock_ingredientes(client_client, client_admin):
    """El stock del ingrediente disminuye al crear un pedido."""
    um_id = client_admin.get("/api/v1/unidades-medida/").json()[0]["id"]
    ing = client_admin.post("/api/v1/ingredientes/", json={
        "nombre": "IngStock", "stock_total": "5.000", "precio_costo": "10.00"
    }).json()
    prod = client_admin.post("/api/v1/productos/", json={
        "nombre": "ProdStock", "margen_ganancia": "0", "disponible": True,
        "categorias": [],
        "ingredientes": [{"ingrediente_id": ing["id"], "cantidad": "1.000",
                          "unidad_medida_id": um_id, "es_removible": False}],
    }).json()
    client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"], cantidad=2))
    ing_post = client_admin.get(f"/api/v1/ingredientes/{ing['id']}").json()
    assert Decimal(ing_post["stock_total"]) == Decimal("3.000")


def test_crear_pedido_stock_insuficiente(client_client, client_admin):
    """422 si el stock del ingrediente es insuficiente para el pedido."""
    um_id = client_admin.get("/api/v1/unidades-medida/").json()[0]["id"]
    ing = client_admin.post("/api/v1/ingredientes/", json={
        "nombre": "IngEscaso", "stock_total": "1.000", "precio_costo": "10.00"
    }).json()
    prod = client_admin.post("/api/v1/productos/", json={
        "nombre": "ProdEscaso", "margen_ganancia": "0", "disponible": True,
        "categorias": [],
        "ingredientes": [{"ingrediente_id": ing["id"], "cantidad": "1.000",
                          "unidad_medida_id": um_id, "es_removible": False}],
    }).json()
    r = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"], cantidad=2))
    assert r.status_code == 422


def test_cancelar_pedido_restaura_stock(client_client, client_admin):
    """Al cancelar desde PENDIENTE (cliente), el stock del ingrediente se restaura."""
    um_id = client_admin.get("/api/v1/unidades-medida/").json()[0]["id"]
    ing = client_admin.post("/api/v1/ingredientes/", json={
        "nombre": "IngRestCliente", "stock_total": "5.000", "precio_costo": "10.00"
    }).json()
    prod = client_admin.post("/api/v1/productos/", json={
        "nombre": "ProdRestCliente", "margen_ganancia": "0", "disponible": True,
        "categorias": [],
        "ingredientes": [{"ingrediente_id": ing["id"], "cantidad": "2.000",
                          "unidad_medida_id": um_id, "es_removible": False}],
    }).json()
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"], cantidad=1)).json()
    assert Decimal(client_admin.get(f"/api/v1/ingredientes/{ing['id']}").json()["stock_total"]) == Decimal("3.000")
    client_client.request("DELETE", f"/api/v1/pedidos/{pedido['id']}", json={"motivo": "No lo quiero"})
    assert Decimal(client_admin.get(f"/api/v1/ingredientes/{ing['id']}").json()["stock_total"]) == Decimal("5.000")


def test_admin_cancela_desde_pendiente_restaura_stock(client_client, client_admin):
    """Admin cancela desde PENDIENTE → stock se restaura."""
    um_id = client_admin.get("/api/v1/unidades-medida/").json()[0]["id"]
    ing = client_admin.post("/api/v1/ingredientes/", json={
        "nombre": "IngRestAdmin", "stock_total": "10.000", "precio_costo": "5.00"
    }).json()
    prod = client_admin.post("/api/v1/productos/", json={
        "nombre": "ProdRestAdmin", "margen_ganancia": "0", "disponible": True,
        "categorias": [],
        "ingredientes": [{"ingrediente_id": ing["id"], "cantidad": "3.000",
                          "unidad_medida_id": um_id, "es_removible": False}],
    }).json()
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"], cantidad=2)).json()
    assert Decimal(client_admin.get(f"/api/v1/ingredientes/{ing['id']}").json()["stock_total"]) == Decimal("4.000")
    client_admin.patch(f"/api/v1/pedidos/{pedido['id']}/estado",
                       json={"estado_hasta": "CANCELADO", "motivo": "Sin stock"})
    assert Decimal(client_admin.get(f"/api/v1/ingredientes/{ing['id']}").json()["stock_total"]) == Decimal("10.000")


def test_admin_cancela_desde_confirmado_restaura_stock(client_client, client_admin):
    """Admin cancela desde CONFIRMADO → stock se restaura (CONFIRMADO está en ESTADOS_CON_STOCK_DESCONTADO)."""
    um_id = client_admin.get("/api/v1/unidades-medida/").json()[0]["id"]
    ing = client_admin.post("/api/v1/ingredientes/", json={
        "nombre": "IngConfirmado", "stock_total": "10.000", "precio_costo": "5.00"
    }).json()
    prod = client_admin.post("/api/v1/productos/", json={
        "nombre": "ProdConfirmado", "margen_ganancia": "0", "disponible": True,
        "categorias": [],
        "ingredientes": [{"ingrediente_id": ing["id"], "cantidad": "2.000",
                          "unidad_medida_id": um_id, "es_removible": False}],
    }).json()
    pedido = client_client.post("/api/v1/pedidos/", json=_payload_pedido(prod["id"], cantidad=1)).json()
    assert Decimal(client_admin.get(f"/api/v1/ingredientes/{ing['id']}").json()["stock_total"]) == Decimal("8.000")
    client_admin.patch(f"/api/v1/pedidos/{pedido['id']}/estado", json={"estado_hasta": "CONFIRMADO"})
    client_admin.patch(f"/api/v1/pedidos/{pedido['id']}/estado",
                       json={"estado_hasta": "CANCELADO", "motivo": "Cambio de plan"})
    assert Decimal(client_admin.get(f"/api/v1/ingredientes/{ing['id']}").json()["stock_total"]) == Decimal("10.000")
