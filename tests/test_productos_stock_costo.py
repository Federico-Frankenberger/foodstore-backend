"""
Tests de integración para stock_calculado, precio_costo_calculado y precio_venta.
Verifican que los valores se calculan dinámicamente desde los ingredientes.
"""

from decimal import Decimal
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _unidad_id(client) -> int:
    """Devuelve el id de la primera unidad de medida del seed."""
    return client.get("/api/v1/unidades-medida/").json()[0]["id"]


def _crear_ingrediente(client, nombre, stock_total="0.000", precio_costo="0.00", unidad_medida_id=None):
    payload = {
        "nombre": nombre,
        "stock_total": stock_total,
        "precio_costo": precio_costo,
    }
    if unidad_medida_id:
        payload["unidad_medida_id"] = unidad_medida_id
    r = client.post("/api/v1/ingredientes/", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


def _crear_producto(client, nombre, margen=0, ingredientes=None):
    r = client.post("/api/v1/productos/", json={
        "nombre": nombre,
        "margen_ganancia": str(margen),
        "disponible": True,
        "categorias": [],
        "ingredientes": ingredientes or [],
    })
    assert r.status_code == 201, r.text
    return r.json()


# ── Tests de métricas sin ingredientes ───────────────────────────────────────

def test_metricas_sin_ingredientes(client_admin):
    """Producto sin ingredientes → stock=0, costo=0.00, venta=0.00."""
    prod = _crear_producto(client_admin, "Producto vacío", margen=50)
    assert prod["stock_calculado"] == 0
    assert Decimal(prod["precio_costo_calculado"]) == Decimal("0.00")
    assert Decimal(prod["precio_venta"]) == Decimal("0.00")


# ── Tests de stock_calculado ──────────────────────────────────────────────────

def test_stock_calculado_un_ingrediente(client_admin):
    """
    stock_total=10.000, cantidad=2.500
    → floor(10.000 / 2.500) = 4
    costo = 50.00 × 2.500 = 125.00
    venta (margen=0) = 125.00
    """
    um = _unidad_id(client_admin)
    ing = _crear_ingrediente(client_admin, "Carne", stock_total="10.000", precio_costo="50.00")
    prod = _crear_producto(client_admin, "Hamburguesa simple", margen=0, ingredientes=[{
        "ingrediente_id": ing["id"],
        "cantidad": "2.500",
        "unidad_medida_id": um,
        "es_removible": False,
    }])
    assert prod["stock_calculado"] == 4
    assert Decimal(prod["precio_costo_calculado"]) == Decimal("125.00")
    assert Decimal(prod["precio_venta"]) == Decimal("125.00")


def test_stock_calculado_minimo_entre_ingredientes(client_admin):
    """
    Ingrediente A: stock=10, cantidad=2 → floor(10/2) = 5
    Ingrediente B: stock=3,  cantidad=1 → floor(3/1)  = 3
    → stock_calculado = min(5, 3) = 3
    costo = 20×2 + 5×1 = 45.00
    """
    um = _unidad_id(client_admin)
    ing_a = _crear_ingrediente(client_admin, "Pan", stock_total="10.000", precio_costo="20.00")
    ing_b = _crear_ingrediente(client_admin, "Lechuga", stock_total="3.000", precio_costo="5.00")
    prod = _crear_producto(client_admin, "Sándwich", margen=0, ingredientes=[
        {"ingrediente_id": ing_a["id"], "cantidad": "2.000", "unidad_medida_id": um, "es_removible": False},
        {"ingrediente_id": ing_b["id"], "cantidad": "1.000", "unidad_medida_id": um, "es_removible": False},
    ])
    assert prod["stock_calculado"] == 3
    assert Decimal(prod["precio_costo_calculado"]) == Decimal("45.00")


def test_stock_fraccionario(client_admin):
    """
    stock=7.000, cantidad=3.000
    → floor(7/3) = floor(2.333) = 2
    """
    um = _unidad_id(client_admin)
    ing = _crear_ingrediente(client_admin, "Queso", stock_total="7.000", precio_costo="30.00")
    prod = _crear_producto(client_admin, "Pizza", ingredientes=[{
        "ingrediente_id": ing["id"], "cantidad": "3.000",
        "unidad_medida_id": um, "es_removible": False,
    }])
    assert prod["stock_calculado"] == 2


def test_stock_cero_bloquea_produccion(client_admin):
    """
    Ingrediente A: stock=10, cantidad=1 → 10
    Ingrediente B: stock=0,  cantidad=1 → 0
    → stock_calculado = min(10, 0) = 0
    """
    um = _unidad_id(client_admin)
    ing_a = _crear_ingrediente(client_admin, "Tomate", stock_total="10.000", precio_costo="8.00")
    ing_b = _crear_ingrediente(client_admin, "Sal", stock_total="0.000", precio_costo="1.00")
    prod = _crear_producto(client_admin, "Ensalada", ingredientes=[
        {"ingrediente_id": ing_a["id"], "cantidad": "1.000", "unidad_medida_id": um, "es_removible": False},
        {"ingrediente_id": ing_b["id"], "cantidad": "1.000", "unidad_medida_id": um, "es_removible": False},
    ])
    assert prod["stock_calculado"] == 0


# ── Tests de precio_venta con margen ─────────────────────────────────────────

def test_precio_venta_con_margen_50(client_admin):
    """
    costo = 100.00, margen = 50 %
    → precio_venta = 100.00 × 1.50 = 150.00
    """
    um = _unidad_id(client_admin)
    ing = _crear_ingrediente(client_admin, "Masa", stock_total="20.000", precio_costo="100.00")
    prod = _crear_producto(client_admin, "Empanada", margen=50, ingredientes=[{
        "ingrediente_id": ing["id"], "cantidad": "1.000",
        "unidad_medida_id": um, "es_removible": False,
    }])
    assert Decimal(prod["precio_costo_calculado"]) == Decimal("100.00")
    assert Decimal(prod["precio_venta"]) == Decimal("150.00")


def test_precio_venta_se_actualiza_al_cambiar_costo_ingrediente(client_admin):
    """
    Si se actualiza el precio_costo de un ingrediente, el siguiente GET
    refleja automáticamente el nuevo precio_venta.
    """
    um = _unidad_id(client_admin)
    ing = _crear_ingrediente(client_admin, "Harina", stock_total="10.000", precio_costo="50.00")
    prod = _crear_producto(client_admin, "Pan casero", margen=0, ingredientes=[{
        "ingrediente_id": ing["id"], "cantidad": "1.000",
        "unidad_medida_id": um, "es_removible": False,
    }])
    assert Decimal(prod["precio_venta"]) == Decimal("50.00")

    # Actualizar precio del ingrediente
    client_admin.patch(f"/api/v1/ingredientes/{ing['id']}", json={"precio_costo": "80.00"})

    # El producto reflejará el nuevo precio en la siguiente consulta
    r = client_admin.get(f"/api/v1/productos/{prod['id']}")
    assert r.status_code == 200
    assert Decimal(r.json()["precio_venta"]) == Decimal("80.00")


def test_stock_recalcula_al_agregar_ingrediente(client_admin):
    """
    Stock disminuye al agregar ingrediente con poco stock.
    """
    um = _unidad_id(client_admin)
    ing_a = _crear_ingrediente(client_admin, "Relleno A", stock_total="20.000", precio_costo="10.00")
    ing_b = _crear_ingrediente(client_admin, "Relleno B", stock_total="2.000", precio_costo="15.00")

    prod = _crear_producto(client_admin, "Tarta", ingredientes=[{
        "ingrediente_id": ing_a["id"], "cantidad": "2.000",
        "unidad_medida_id": um, "es_removible": False,
    }])
    assert prod["stock_calculado"] == 10  # floor(20/2)

    r = client_admin.post(f"/api/v1/productos/{prod['id']}/ingredientes", json={
        "ingrediente_id": ing_b["id"],
        "cantidad": "1.000",
        "unidad_medida_id": um,
        "es_removible": True,
    })
    assert r.status_code == 201
    assert r.json()["stock_calculado"] == 2  # min(10, floor(2/1)=2)


# ── Test de IngredienteRead con nuevos campos ─────────────────────────────────

def test_ingrediente_read_expone_campos_nuevos(client_admin):
    """IngredienteRead expone stock_total, precio_costo y unidad_medida_id."""
    um = _unidad_id(client_admin)
    ing = _crear_ingrediente(client_admin, "Manteca", stock_total="5.000",
                              precio_costo="120.50", unidad_medida_id=um)
    r = client_admin.get(f"/api/v1/ingredientes/{ing['id']}")
    assert r.status_code == 200
    data = r.json()
    assert Decimal(data["stock_total"]) == Decimal("5.000")
    assert Decimal(data["precio_costo"]) == Decimal("120.50")
    assert data["unidad_medida_id"] == um
