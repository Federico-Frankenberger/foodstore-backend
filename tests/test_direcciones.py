"""
Tests de integración para el CRUD de direcciones de entrega.
  GET    /direcciones/
  POST   /direcciones/
  GET    /direcciones/{id}
  PATCH  /direcciones/{id}
  DELETE /direcciones/{id}
  PATCH  /direcciones/{id}/principal
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import DATOS_USUARIO, DATOS_OTRO_USUARIO

_DIR_BASE = {
    "linea1": "Av. Corrientes 1234",
    "ciudad": "Buenos Aires",
    "provincia": "CABA",
    "es_principal": False,
}


# ── Autenticación requerida ───────────────────────────────────────────────────

def test_requiere_autenticacion_para_listar(client):
    assert client.get("/api/v1/direcciones/").status_code == 401


def test_requiere_autenticacion_para_crear(client):
    assert client.post("/api/v1/direcciones/", json=_DIR_BASE).status_code == 401


# ── Crear ─────────────────────────────────────────────────────────────────────

def test_crear_direccion_exitosa(client_autenticado):
    r = client_autenticado.post("/api/v1/direcciones/", json=_DIR_BASE)
    assert r.status_code == 201
    data = r.json()
    assert data["ciudad"] == "Buenos Aires"
    assert data["linea1"] == "Av. Corrientes 1234"
    assert data["es_principal"] is False


def test_crear_requiere_linea1(client_autenticado):
    r = client_autenticado.post("/api/v1/direcciones/", json={"ciudad": "BA", "es_principal": False})
    assert r.status_code == 422


def test_crear_requiere_ciudad(client_autenticado):
    r = client_autenticado.post("/api/v1/direcciones/", json={"linea1": "Calle 123", "es_principal": False})
    assert r.status_code == 422


def test_crear_con_todos_los_campos(client_autenticado):
    r = client_autenticado.post("/api/v1/direcciones/", json={
        "alias": "Casa",
        "linea1": "Av. Santa Fe 500",
        "linea2": "Piso 3 Depto B",
        "ciudad": "Buenos Aires",
        "provincia": "CABA",
        "codigo_postal": "1059",
        "latitud": "-34.596100",
        "longitud": "-58.374200",
        "es_principal": True,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["alias"] == "Casa"
    assert data["codigo_postal"] == "1059"


# ── Listar ────────────────────────────────────────────────────────────────────

def test_listar_direcciones_vacias(client_autenticado):
    r = client_autenticado.get("/api/v1/direcciones/")
    assert r.status_code == 200
    assert r.json() == []


def test_listar_devuelve_solo_las_del_usuario(client_autenticado):
    client_autenticado.post("/api/v1/direcciones/", json=_DIR_BASE)
    client_autenticado.post("/api/v1/direcciones/", json={**_DIR_BASE, "linea1": "Otra 456"})
    r = client_autenticado.get("/api/v1/direcciones/")
    assert r.status_code == 200
    assert len(r.json()) == 2


# ── Obtener por ID ────────────────────────────────────────────────────────────

def test_obtener_direccion_propia(client_autenticado):
    creada = client_autenticado.post("/api/v1/direcciones/", json=_DIR_BASE).json()
    r = client_autenticado.get(f"/api/v1/direcciones/{creada['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == creada["id"]


def test_obtener_direccion_inexistente(client_autenticado):
    r = client_autenticado.get("/api/v1/direcciones/99999")
    assert r.status_code == 404


# ── Actualizar ────────────────────────────────────────────────────────────────

def test_actualizar_ciudad(client_autenticado):
    creada = client_autenticado.post("/api/v1/direcciones/", json=_DIR_BASE).json()
    r = client_autenticado.patch(f"/api/v1/direcciones/{creada['id']}", json={"ciudad": "Rosario"})
    assert r.status_code == 200
    assert r.json()["ciudad"] == "Rosario"
    assert r.json()["linea1"] == _DIR_BASE["linea1"]  # campo no tocado se conserva


def test_actualizar_direccion_inexistente(client_autenticado):
    r = client_autenticado.patch("/api/v1/direcciones/99999", json={"ciudad": "X"})
    assert r.status_code == 404


# ── Eliminar (soft delete) ────────────────────────────────────────────────────

def test_eliminar_direccion(client_autenticado):
    creada = client_autenticado.post("/api/v1/direcciones/", json=_DIR_BASE).json()
    r = client_autenticado.delete(f"/api/v1/direcciones/{creada['id']}")
    assert r.status_code == 204


def test_direccion_eliminada_no_aparece_en_listado(client_autenticado):
    creada = client_autenticado.post("/api/v1/direcciones/", json=_DIR_BASE).json()
    client_autenticado.delete(f"/api/v1/direcciones/{creada['id']}")
    lista = client_autenticado.get("/api/v1/direcciones/").json()
    assert all(d["id"] != creada["id"] for d in lista)


def test_eliminar_direccion_inexistente(client_autenticado):
    r = client_autenticado.delete("/api/v1/direcciones/99999")
    assert r.status_code == 404


# ── Marcar como principal ─────────────────────────────────────────────────────

def test_marcar_principal_actualiza_el_flag(client_autenticado):
    d1 = client_autenticado.post("/api/v1/direcciones/", json=_DIR_BASE).json()
    d2 = client_autenticado.post("/api/v1/direcciones/", json={**_DIR_BASE, "linea1": "Otra"}).json()

    r = client_autenticado.patch(f"/api/v1/direcciones/{d2['id']}/principal")
    assert r.status_code == 200
    assert r.json()["es_principal"] is True

    lista = {d["id"]: d["es_principal"] for d in client_autenticado.get("/api/v1/direcciones/").json()}
    assert lista[d2["id"]] is True
    assert lista[d1["id"]] is False


def test_marcar_principal_inexistente(client_autenticado):
    r = client_autenticado.patch("/api/v1/direcciones/99999/principal")
    assert r.status_code == 404


# ── Aislamiento entre usuarios ────────────────────────────────────────────────

def test_no_accede_a_direccion_de_otro_usuario(client, monkeypatch):
    """Dos usuarios no pueden ver ni modificar las direcciones del otro."""
    from tests.conftest import get_test_session
    monkeypatch.setattr("app.uow.uow.get_session", get_test_session)

    # Usuario 1 crea su dirección
    client.post("/api/v1/auth/register", json=DATOS_USUARIO)
    client.post("/api/v1/auth/login", json={
        "email": DATOS_USUARIO["email"],
        "contrasena": DATOS_USUARIO["contrasena"],
    })
    dir_usuario1 = client.post("/api/v1/direcciones/", json=_DIR_BASE).json()
    client.post("/api/v1/auth/logout")

    # Usuario 2 intenta acceder
    client.post("/api/v1/auth/register", json=DATOS_OTRO_USUARIO)
    client.post("/api/v1/auth/login", json={
        "email": DATOS_OTRO_USUARIO["email"],
        "contrasena": DATOS_OTRO_USUARIO["contrasena"],
    })
    r = client.get(f"/api/v1/direcciones/{dir_usuario1['id']}")
    assert r.status_code == 404


def test_usuario2_no_puede_eliminar_direccion_del_usuario1(client, monkeypatch):
    from tests.conftest import get_test_session
    monkeypatch.setattr("app.uow.uow.get_session", get_test_session)

    # Usuario 1
    client.post("/api/v1/auth/register", json=DATOS_USUARIO)
    client.post("/api/v1/auth/login", json={
        "email": DATOS_USUARIO["email"],
        "contrasena": DATOS_USUARIO["contrasena"],
    })
    dir_u1 = client.post("/api/v1/direcciones/", json=_DIR_BASE).json()
    client.post("/api/v1/auth/logout")

    # Usuario 2
    client.post("/api/v1/auth/register", json=DATOS_OTRO_USUARIO)
    client.post("/api/v1/auth/login", json={
        "email": DATOS_OTRO_USUARIO["email"],
        "contrasena": DATOS_OTRO_USUARIO["contrasena"],
    })
    r = client.delete(f"/api/v1/direcciones/{dir_u1['id']}")
    assert r.status_code == 404
