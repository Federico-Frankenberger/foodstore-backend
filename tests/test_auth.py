"""
Tests de integración para los endpoints de autenticación:
  POST /auth/register
  POST /auth/login
  POST /auth/refresh
  POST /auth/logout
  GET  /auth/me
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import DATOS_USUARIO, DATOS_OTRO_USUARIO


# ── Registro ──────────────────────────────────────────────────────────────────

def test_registro_exitoso(client):
    r = client.post("/api/v1/auth/register", json=DATOS_USUARIO)
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == DATOS_USUARIO["email"]
    assert data["nombre"] == DATOS_USUARIO["nombre"]
    assert data["apellido"] == DATOS_USUARIO["apellido"]
    assert data["roles"] == ["CLIENT"]


def test_registro_no_expone_hash(client):
    r = client.post("/api/v1/auth/register", json=DATOS_USUARIO)
    assert "password_hash" not in r.json()
    assert "contrasena" not in r.json()


def test_registro_email_duplicado(client, usuario_creado):
    r = client.post("/api/v1/auth/register", json={**DATOS_OTRO_USUARIO, "email": DATOS_USUARIO["email"]})
    assert r.status_code == 409


def test_registro_contrasena_muy_corta(client):
    r = client.post("/api/v1/auth/register", json={**DATOS_USUARIO, "contrasena": "corta"})
    assert r.status_code == 422


def test_registro_email_invalido(client):
    r = client.post("/api/v1/auth/register", json={**DATOS_USUARIO, "email": "no-es-un-email"})
    assert r.status_code == 422


def test_registro_nombre_muy_corto(client):
    r = client.post("/api/v1/auth/register", json={**DATOS_USUARIO, "nombre": "X"})
    assert r.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_exitoso_setea_cookies(client, usuario_creado):
    r = client.post("/api/v1/auth/login", json={
        "email": DATOS_USUARIO["email"],
        "contrasena": DATOS_USUARIO["contrasena"],
    })
    assert r.status_code == 200
    assert "access_token" in r.cookies
    assert "refresh_token" in r.cookies


def test_login_email_inexistente(client):
    r = client.post("/api/v1/auth/login", json={
        "email": "noexiste@test.com",
        "contrasena": "password123",
    })
    assert r.status_code == 401


def test_login_contrasena_incorrecta(client, usuario_creado):
    r = client.post("/api/v1/auth/login", json={
        "email": DATOS_USUARIO["email"],
        "contrasena": "contrasena_incorrecta",
    })
    assert r.status_code == 401


# ── Perfil propio ─────────────────────────────────────────────────────────────

def test_yo_con_cookie_valida(client_autenticado):
    r = client_autenticado.get("/api/v1/auth/me")
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == DATOS_USUARIO["email"]
    assert "CLIENT" in data["roles"]


def test_yo_sin_autenticacion(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_yo_no_expone_hash(client_autenticado):
    r = client_autenticado.get("/api/v1/auth/me")
    assert "password_hash" not in r.json()


# ── Refresh token ─────────────────────────────────────────────────────────────

def test_refresh_emite_nuevo_access_token(client, usuario_creado):
    client.post("/api/v1/auth/login", json={
        "email": DATOS_USUARIO["email"],
        "contrasena": DATOS_USUARIO["contrasena"],
    })
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 200
    # Después del refresh, el cliente sigue autenticado
    r2 = client.get("/api/v1/auth/me")
    assert r2.status_code == 200


def test_refresh_sin_cookie_falla(client):
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 401


def test_refresh_con_token_invalido_falla(client, usuario_creado):
    client.post("/api/v1/auth/login", json={
        "email": DATOS_USUARIO["email"],
        "contrasena": DATOS_USUARIO["contrasena"],
    })
    # Reemplazar refresh_token por uno inválido
    client.cookies.set("refresh_token", "token-completamente-inventado")
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────

def test_logout_borra_cookies_y_cierra_sesion(client_autenticado):
    # Antes del logout, /me funciona
    assert client_autenticado.get("/api/v1/auth/me").status_code == 200
    # Logout
    r = client_autenticado.post("/api/v1/auth/logout")
    assert r.status_code == 200
    # Después del logout, /me debe rechazar (cookie eliminada)
    assert client_autenticado.get("/api/v1/auth/me").status_code == 401


def test_refresh_token_revocado_despues_de_logout(client, usuario_creado):
    """El refresh token queda invalidado en BD después del logout."""
    # Login y guardar refresh token
    client.post("/api/v1/auth/login", json={
        "email": DATOS_USUARIO["email"],
        "contrasena": DATOS_USUARIO["contrasena"],
    })
    refresh_raw = client.cookies.get("refresh_token")
    assert refresh_raw is not None

    # Logout (revoca el token en BD y borra cookies)
    client.post("/api/v1/auth/logout")

    # Re-inyectar el refresh token manualmente y pedir refresh
    client.cookies.set("refresh_token", refresh_raw)
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 401  # revocado en BD
