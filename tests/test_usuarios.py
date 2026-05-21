"""
Tests de integración para gestión de usuarios y roles (endpoints admin).
  GET    /auth/admin/usuarios
  POST   /auth/admin/usuarios/{id}/deshabilitar
  POST   /auth/admin/usuarios/{id}/habilitar
  POST   /auth/admin/usuarios/{id}/roles/{rol}
  DELETE /auth/admin/usuarios/{id}/roles/{rol}
  GET    /auth/admin/roles
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import DATOS_USUARIO, DATOS_ADMIN, DATOS_OTRO_USUARIO


# ── Control de acceso ─────────────────────────────────────────────────────────

def test_usuario_normal_no_puede_listar(client_autenticado):
    r = client_autenticado.get("/api/v1/auth/admin/usuarios")
    assert r.status_code == 403


def test_sin_autenticar_no_puede_listar(client):
    r = client.get("/api/v1/auth/admin/usuarios")
    assert r.status_code == 401


# ── Listar usuarios ───────────────────────────────────────────────────────────

def test_admin_lista_todos_los_usuarios(client_admin, usuario_creado):
    r = client_admin.get("/api/v1/auth/admin/usuarios")
    assert r.status_code == 200
    emails = [u["email"] for u in r.json()]
    assert DATOS_ADMIN["email"] in emails
    assert DATOS_USUARIO["email"] in emails


def test_admin_lista_roles_del_catalogo(client_admin):
    r = client_admin.get("/api/v1/auth/admin/roles")
    assert r.status_code == 200
    codigos = {rol["codigo"] for rol in r.json()}
    assert codigos == {"ADMIN", "STOCK", "PEDIDOS", "CLIENT"}


# ── Deshabilitar / habilitar ──────────────────────────────────────────────────

def test_admin_deshabilita_usuario(client_admin, usuario_creado):
    uid = usuario_creado["id"]
    r = client_admin.post(f"/api/v1/auth/admin/usuarios/{uid}/deshabilitar")
    assert r.status_code == 200


def test_usuario_deshabilitado_no_puede_hacer_login(client, client_admin, usuario_creado):
    uid = usuario_creado["id"]
    client_admin.post(f"/api/v1/auth/admin/usuarios/{uid}/deshabilitar")
    r = client.post("/api/v1/auth/login", json={
        "email": DATOS_USUARIO["email"],
        "contrasena": DATOS_USUARIO["contrasena"],
    })
    assert r.status_code == 400


def test_admin_habilita_usuario_deshabilitado(client, client_admin, usuario_creado):
    uid = usuario_creado["id"]
    client_admin.post(f"/api/v1/auth/admin/usuarios/{uid}/deshabilitar")
    client_admin.post(f"/api/v1/auth/admin/usuarios/{uid}/habilitar")
    r = client.post("/api/v1/auth/login", json={
        "email": DATOS_USUARIO["email"],
        "contrasena": DATOS_USUARIO["contrasena"],
    })
    assert r.status_code == 200


def test_deshabilitar_usuario_inexistente(client_admin):
    r = client_admin.post("/api/v1/auth/admin/usuarios/99999/deshabilitar")
    assert r.status_code == 404


# ── Asignación de roles ───────────────────────────────────────────────────────

def test_admin_asigna_rol_existente(client_admin, usuario_creado):
    uid = usuario_creado["id"]
    r = client_admin.post(f"/api/v1/auth/admin/usuarios/{uid}/roles/STOCK")
    assert r.status_code == 200
    roles = r.json()["roles"]
    assert "STOCK" in roles
    assert "CLIENT" in roles  # rol original se mantiene


def test_admin_quita_rol(client_admin, usuario_creado):
    uid = usuario_creado["id"]
    client_admin.post(f"/api/v1/auth/admin/usuarios/{uid}/roles/STOCK")
    r = client_admin.delete(f"/api/v1/auth/admin/usuarios/{uid}/roles/STOCK")
    assert r.status_code == 200
    assert "STOCK" not in r.json()["roles"]


def test_asignar_rol_que_no_existe(client_admin, usuario_creado):
    uid = usuario_creado["id"]
    r = client_admin.post(f"/api/v1/auth/admin/usuarios/{uid}/roles/INEXISTENTE")
    assert r.status_code == 404


def test_asignar_rol_duplicado(client_admin, usuario_creado):
    uid = usuario_creado["id"]
    client_admin.post(f"/api/v1/auth/admin/usuarios/{uid}/roles/STOCK")
    r = client_admin.post(f"/api/v1/auth/admin/usuarios/{uid}/roles/STOCK")
    assert r.status_code == 409


def test_quitar_rol_que_no_tiene(client_admin, usuario_creado):
    uid = usuario_creado["id"]
    r = client_admin.delete(f"/api/v1/auth/admin/usuarios/{uid}/roles/PEDIDOS")
    assert r.status_code == 404


# ── Roles reflejados en JWT ───────────────────────────────────────────────────

def test_roles_actualizados_en_siguiente_login(client, client_admin, usuario_creado):
    """Después de asignar un rol, el siguiente login lo incluye en el JWT."""
    uid = usuario_creado["id"]
    client_admin.post(f"/api/v1/auth/admin/usuarios/{uid}/roles/STOCK")

    # El usuario vuelve a hacer login
    client.post("/api/v1/auth/login", json={
        "email": DATOS_USUARIO["email"],
        "contrasena": DATOS_USUARIO["contrasena"],
    })
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 200
    roles = r.json()["roles"]
    assert "STOCK" in roles
    assert "CLIENT" in roles
