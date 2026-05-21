"""
Tests unitarios de app/core/security.py.
No tocan la base de datos.
"""

from datetime import timedelta

import pytest
import jwt as jose_jwt

from app.core.config import configuracion
from app.core.security import (
    crear_token_acceso,
    decodificar_token_acceso,
    generar_refresh_token,
    hashear_contrasena,
    hashear_token,
    verificar_contrasena,
)


# ── Hash de contraseñas ───────────────────────────────────────────────────────

def test_hash_y_verificacion_correcta():
    hashed = hashear_contrasena("mipassword")
    assert verificar_contrasena("mipassword", hashed)


def test_contrasena_incorrecta_no_verifica():
    hashed = hashear_contrasena("correcta")
    assert not verificar_contrasena("incorrecta", hashed)


def test_misma_contrasena_genera_hashes_distintos():
    """bcrypt incluye salt aleatoria — nunca dos hashes iguales."""
    h1 = hashear_contrasena("password")
    h2 = hashear_contrasena("password")
    assert h1 != h2


def test_hash_es_verificable_con_passlib():
    """El hash producido siempre es verificable independientemente del salt."""
    for plain in ["abc12345", "Segur@1!", "x" * 72]:
        hashed = hashear_contrasena(plain)
        assert verificar_contrasena(plain, hashed)


# ── JWT — access token ────────────────────────────────────────────────────────

def test_crear_y_decodificar_token():
    token = crear_token_acceso(usuario_id=42, roles=["CLIENT"])
    payload = decodificar_token_acceso(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["roles"] == ["CLIENT"]
    assert payload["type"] == "access"


def test_token_con_multiples_roles():
    token = crear_token_acceso(usuario_id=1, roles=["ADMIN", "CLIENT"])
    payload = decodificar_token_acceso(token)
    assert set(payload["roles"]) == {"ADMIN", "CLIENT"}


def test_token_expirado_devuelve_none():
    token = crear_token_acceso(usuario_id=1, roles=["CLIENT"], delta=timedelta(seconds=-1))
    assert decodificar_token_acceso(token) is None


def test_token_con_firma_incorrecta_devuelve_none():
    token = crear_token_acceso(usuario_id=1, roles=["CLIENT"])
    partes = token.split(".")
    # Corromper la firma (última parte)
    token_corrupto = partes[0] + "." + partes[1] + ".firmaInvalida"
    assert decodificar_token_acceso(token_corrupto) is None


def test_token_tipo_incorrecto_devuelve_none():
    """Un token de tipo 'refresh' no debe ser aceptado como access."""
    payload = {"sub": "1", "roles": ["CLIENT"], "type": "refresh"}
    token = jose_jwt.encode(payload, configuracion.SECRET_KEY, algorithm=configuracion.ALGORITMO)
    assert decodificar_token_acceso(token) is None


def test_token_sin_sub_devuelve_payload():
    """decodificar_token_acceso solo valida firma y tipo — sub lo valida deps.py."""
    payload = {"roles": ["CLIENT"], "type": "access"}
    token = jose_jwt.encode(payload, configuracion.SECRET_KEY, algorithm=configuracion.ALGORITMO)
    resultado = decodificar_token_acceso(token)
    assert resultado is not None
    assert resultado.get("sub") is None


# ── Refresh token ─────────────────────────────────────────────────────────────

def test_generar_refresh_token_devuelve_par():
    raw, hash_ = generar_refresh_token()
    assert isinstance(raw, str) and len(raw) > 32
    assert isinstance(hash_, str) and len(hash_) == 64  # SHA-256 en hex


def test_hashear_token_es_determinista():
    raw, _ = generar_refresh_token()
    assert hashear_token(raw) == hashear_token(raw)


def test_hash_coincide_con_el_generado():
    raw, hash_generado = generar_refresh_token()
    assert hashear_token(raw) == hash_generado


def test_dos_tokens_distintos_tienen_hashes_distintos():
    raw1, h1 = generar_refresh_token()
    raw2, h2 = generar_refresh_token()
    assert raw1 != raw2
    assert h1 != h2


def test_raw_y_hash_son_diferentes():
    raw, hash_ = generar_refresh_token()
    assert raw != hash_
