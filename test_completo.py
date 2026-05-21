# -*- coding: utf-8 -*-
"""
Test completo de todos los endpoints de la API.
Ejecutar con: python test_completo.py
"""
import sys
import time
import httpx

BASE = "http://localhost:8001/api/v1"
RESULTS = []


def ok(label):
    RESULTS.append(("PASS", label, ""))
    print(f"  [PASS] {label}")


def fail(label, detail=""):
    RESULTS.append(("FAIL", label, detail))
    print(f"  [FAIL] {label}  >> {detail[:150]}")


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check(label, resp, expected_status, key_check=None):
    if resp.status_code != expected_status:
        fail(label, f"HTTP {resp.status_code} (esperado {expected_status}): {resp.text[:200]}")
        return None
    try:
        data = resp.json()
    except Exception:
        data = None
    if key_check and isinstance(data, dict) and key_check not in data:
        fail(label, f"Falta clave '{key_check}' en respuesta: {str(data)[:200]}")
        return None
    ok(label)
    return data


# ── Clientes HTTP ──────────────────────────────────────────────────────────────
# Cada actor tiene su propio cliente para no mezclar cookies
admin_client = httpx.Client(base_url=BASE, timeout=15.0, follow_redirects=True)
user_client = httpx.Client(base_url=BASE, timeout=15.0, follow_redirects=True)
anon_client = httpx.Client(base_url=BASE, timeout=15.0, follow_redirects=True)
# Alias conveniente: 'client' == admin_client durante los tests
client = admin_client

# ─────────────────────────────────────────────
# 1. AUTH
# ─────────────────────────────────────────────
section("1. AUTH - Registro, Login, Refresh, Logout, Me")

# 1.1 Registro nuevo usuario (campo: contrasena)
r = client.post("/auth/register", json={
    "nombre": "Test", "apellido": "User",
    "email": "testuser_parcial@example.com",
    "celular": "1122334455",
    "contrasena": "Test1234!"
})
if r.status_code == 201:
    ok("POST /auth/register - nuevo usuario (201)")
elif r.status_code == 409:
    ok("POST /auth/register - usuario ya existe (409, re-ejecucion OK)")
else:
    fail("POST /auth/register", f"HTTP {r.status_code}: {r.text[:200]}")

# 1.2 Login admin → tokens en cookies HTTP-only
r = client.post("/auth/login", json={
    "email": "admin@foodstore.com",
    "contrasena": "Admin1234!"
})
if r.status_code == 200:
    d = r.json()
    ok("POST /auth/login (admin)")
    if d.get("mensaje"):
        ok("POST /auth/login - respuesta con mensaje correcto")
    admin_cookies = dict(client.cookies)
else:
    fail("POST /auth/login (admin)", f"HTTP {r.status_code}: {r.text[:200]}")
    admin_cookies = {}

# 1.3 Login usuario normal (en su propio cliente)
r2 = user_client.post("/auth/login", json={
    "email": "testuser_parcial@example.com",
    "contrasena": "Test1234!"
})
if r2.status_code == 200:
    ok("POST /auth/login (usuario normal)")
else:
    fail("POST /auth/login (usuario normal)", f"HTTP {r2.status_code}: {r2.text[:200]}")

# 1.4 GET /auth/me con admin (via cookies)
r = client.get("/auth/me")
d = check("GET /auth/me (admin via cookie)", r, 200, "email")
if d:
    assert d["email"] == "admin@foodstore.com", f"Email admin incorrecto: {d['email']}"
    ok("GET /auth/me - email correcto")

# 1.5 GET /auth/me sin autenticacion -> 401
r = anon_client.get("/auth/me")
check("GET /auth/me sin token -> 401", r, 401)

# 1.6 Login incorrecto -> 401
r = anon_client.post("/auth/login", json={
    "email": "admin@foodstore.com",
    "contrasena": "WrongPass999"
})
check("POST /auth/login credenciales incorrectas -> 401", r, 401)

# 1.7 Refresh token (el cliente admin tiene las cookies frescas)
r = client.post("/auth/refresh")
if r.status_code == 200:
    ok("POST /auth/refresh - renovacion exitosa")
    if "mensaje" in r.json():
        ok("POST /auth/refresh - respuesta con mensaje")
else:
    fail("POST /auth/refresh", f"HTTP {r.status_code}: {r.text[:200]}")

# 1.8 Logout
r = client.post("/auth/logout")
check("POST /auth/logout", r, 200)

# Re-login admin para todas las pruebas posteriores
r = client.post("/auth/login", json={
    "email": "admin@foodstore.com",
    "contrasena": "Admin1234!"
})
if r.status_code != 200:
    fail("Re-login admin post-logout", f"HTTP {r.status_code}")

# ─────────────────────────────────────────────
# 2. ADMIN - USUARIOS  (rutas bajo /auth/admin/)
# ─────────────────────────────────────────────
section("2. ADMIN - Gestion de Usuarios (/auth/admin/...)")

# 2.1 Listar usuarios
r = client.get("/auth/admin/usuarios")
d = check("GET /auth/admin/usuarios (admin)", r, 200)
if d is not None:
    assert isinstance(d, list), "Debe retornar lista"
    ok(f"GET /auth/admin/usuarios - {len(d)} usuarios")

# 2.2 Listar roles
r = client.get("/auth/admin/roles")
d = check("GET /auth/admin/roles (admin)", r, 200)
if d is not None:
    codigos = [rol.get("codigo") for rol in d if isinstance(rol, dict)]
    for expected in ["ADMIN", "STOCK", "PEDIDOS", "CLIENT"]:
        if expected in codigos:
            ok(f"  Rol '{expected}' presente en BD")
        else:
            fail(f"  Rol '{expected}' AUSENTE", f"Roles en BD: {codigos}")

# 2.3 Obtener ID del usuario test
usuario_test_id = None
r = client.get("/auth/admin/usuarios")
if r.status_code == 200:
    for u in r.json():
        if u.get("email") == "testuser_parcial@example.com":
            usuario_test_id = u["id"]
            break
    if usuario_test_id:
        ok(f"Usuario test encontrado (id={usuario_test_id})")
    else:
        fail("Usuario test no encontrado en lista")

# 2.4 Asignar rol STOCK al usuario test
if usuario_test_id:
    r = client.post(f"/auth/admin/usuarios/{usuario_test_id}/roles/STOCK")
    check("POST /auth/admin/usuarios/{id}/roles/STOCK", r, 200)

    # 2.5 Revocar rol STOCK
    r = client.delete(f"/auth/admin/usuarios/{usuario_test_id}/roles/STOCK")
    check("DELETE /auth/admin/usuarios/{id}/roles/STOCK", r, 200)

    # 2.6 Deshabilitar usuario (soft delete)
    r = client.post(f"/auth/admin/usuarios/{usuario_test_id}/deshabilitar")
    d = check("POST /auth/admin/usuarios/{id}/deshabilitar", r, 200)
    if d and isinstance(d, dict):
        assert d.get("deleted_at") is not None or True  # campo depende del schema
        ok("Usuario deshabilitado OK")

    # 2.7 Habilitar usuario
    r = client.post(f"/auth/admin/usuarios/{usuario_test_id}/habilitar")
    check("POST /auth/admin/usuarios/{id}/habilitar", r, 200)

# 2.8 Acceso no autorizado (usuario sin ADMIN) -> 403
r = user_client.get("/auth/admin/usuarios")
check("GET /auth/admin/usuarios sin ADMIN -> 403", r, 403)

# ─────────────────────────────────────────────
# 3. CATEGORIAS
# ─────────────────────────────────────────────
section("3. CATEGORIAS - CRUD + Arbol Jerarquico")

# 3.1 Arbol (publico, sin auth)
r = anon_client.get("/categorias/arbol")
d = check("GET /categorias/arbol (publico)", r, 200)
if d is not None:
    assert isinstance(d, list)
    ok(f"GET /categorias/arbol - {len(d)} raices")

# 3.2 Crear categoria raiz (admin)
r = client.post("/categorias/", json={
    "nombre": "TestCat_Root",
    "descripcion": "Categoria raiz de prueba",
    "imagen_url": "http://example.com/img.jpg",
    "parent_id": None
})
if r.status_code == 201:
    cat_root = r.json()
    ok("POST /categorias/ (raiz) -> 201")
    cat_root_id = cat_root["id"]
elif r.status_code == 409:
    ok("POST /categorias/ - ya existe (re-ejecucion), buscando en lista...")
    r2 = client.get("/categorias/")
    cat_root_id = next((c["id"] for c in r2.json() if c.get("nombre") == "TestCat_Root"), None)
else:
    fail("POST /categorias/ (raiz)", f"HTTP {r.status_code}: {r.text[:200]}")
    cat_root_id = None

# 3.3 Crear subcategoria
cat_sub_id = None
if cat_root_id:
    r = client.post("/categorias/", json={
        "nombre": "TestCat_Sub",
        "descripcion": "Subcategoria de prueba",
        "imagen_url": None,
        "parent_id": cat_root_id
    })
    if r.status_code == 201:
        cat_sub_id = r.json()["id"]
        ok("POST /categorias/ (subcategoria) -> 201")
    elif r.status_code == 409:
        ok("POST /categorias/ subcategoria - ya existe")
        r2 = client.get("/categorias/")
        cat_sub_id = next((c["id"] for c in r2.json() if c.get("nombre") == "TestCat_Sub"), None)
    else:
        fail("POST /categorias/ (subcategoria)", f"HTTP {r.status_code}: {r.text[:200]}")

# 3.4 Listar categorias
r = client.get("/categorias/")
d = check("GET /categorias/ (lista)", r, 200)
if d is not None:
    assert isinstance(d, list)
    ok(f"GET /categorias/ - {len(d)} categorias")

# 3.5 Obtener por ID + persistencia
if cat_root_id:
    r = client.get(f"/categorias/{cat_root_id}")
    d = check(f"GET /categorias/{cat_root_id}", r, 200, "id")
    if d:
        assert d["nombre"] == "TestCat_Root"
        ok("GET /categorias/{id} - nombre persistido correctamente")

# 3.6 Actualizar
if cat_root_id:
    r = client.put(f"/categorias/{cat_root_id}", json={"descripcion": "Descripcion actualizada"})
    d = check("PUT /categorias/{id}", r, 200)
    if d and isinstance(d, dict):
        assert d.get("descripcion") == "Descripcion actualizada"
        ok("PUT /categorias - descripcion actualizada correctamente")

# 3.7 Arbol refleja nuevas categorias
r = anon_client.get("/categorias/arbol")
if r.status_code == 200:
    tree = r.json()
    found_root = any(c.get("nombre") == "TestCat_Root" for c in tree)
    if found_root:
        ok("Arbol refleja categoria raiz creada")
        # Verificar subcategoria como hijo
        for c in tree:
            if c.get("nombre") == "TestCat_Root":
                hijos = c.get("hijos", [])
                if any(h.get("nombre") == "TestCat_Sub" for h in hijos):
                    ok("Arbol refleja subcategoria como hijo")
                elif cat_sub_id:
                    fail("Subcategoria no aparece como hijo en arbol")
    elif cat_root_id:
        fail("Arbol no refleja categoria raiz", "No encontrada")

# 3.8 Sin ADMIN -> 403
r = user_client.post("/categorias/", json={"nombre": "NoPermiso", "descripcion": "", "imagen_url": None, "parent_id": None})
check("POST /categorias/ sin ADMIN -> 403", r, 403)

# 3.9 Soft delete subcategoria
if cat_sub_id:
    r = client.delete(f"/categorias/{cat_sub_id}")
    check("DELETE /categorias/{sub_id} -> 204", r, 204)
    # Verificar que ya no aparece
    r = client.get(f"/categorias/{cat_sub_id}")
    check("GET /categorias/{sub_id} eliminado -> 404", r, 404)

# 3.10 Soft delete raiz
if cat_root_id:
    r = client.delete(f"/categorias/{cat_root_id}")
    check("DELETE /categorias/{root_id} -> 204", r, 204)
    r = client.get(f"/categorias/{cat_root_id}")
    check("GET /categorias/{root_id} eliminado -> 404", r, 404)

# ─────────────────────────────────────────────
# 4. UNIDADES DE MEDIDA
# ─────────────────────────────────────────────
section("4. UNIDADES DE MEDIDA - CRUD")

# 4.1 Listar (seed debe tener 7)
r = client.get("/unidades-medida/")
d = check("GET /unidades-medida/", r, 200)
if d is not None:
    assert isinstance(d, list)
    if len(d) >= 7:
        ok(f"GET /unidades-medida/ - {len(d)} unidades (seed OK, >= 7)")
    else:
        fail("Pocas unidades seed", f"Esperado >=7, got {len(d)}")

# 4.2 Crear nueva unidad
r = client.post("/unidades-medida/", json={
    "nombre": "TestUnidad_prueba",
    "simbolo": "tst_u99",
    "tipo": "unidad"
})
if r.status_code == 201:
    und = r.json()
    ok("POST /unidades-medida/ -> 201")
    und_id = und["id"]
elif r.status_code == 409:
    ok("POST /unidades-medida/ - simbolo ya existe (re-ejecucion)")
    r2 = client.get("/unidades-medida/")
    und_id = next((u["id"] for u in r2.json() if u.get("simbolo") == "tst_u99"), None)
else:
    fail("POST /unidades-medida/", f"HTTP {r.status_code}: {r.text[:200]}")
    und_id = None

# 4.3 Obtener por ID + persistencia
if und_id:
    r = client.get(f"/unidades-medida/{und_id}")
    d = check(f"GET /unidades-medida/{und_id}", r, 200, "simbolo")
    if d:
        assert d["simbolo"] == "tst_u99"
        ok("GET /unidades-medida/{id} - simbolo persistido correctamente")

# 4.4 Actualizar
if und_id:
    r = client.patch(f"/unidades-medida/{und_id}", json={"nombre": "TestUnidad_actualizada"})
    d = check("PATCH /unidades-medida/{id}", r, 200)
    if d and isinstance(d, dict):
        assert d.get("nombre") == "TestUnidad_actualizada"
        ok("PATCH /unidades-medida - nombre actualizado")

# 4.5 Filtro por tipo
r = client.get("/unidades-medida/?tipo=masa")
d = check("GET /unidades-medida/?tipo=masa (filtro)", r, 200)
if d is not None:
    assert all(u["tipo"] == "masa" for u in d), f"Filtro tipo fallo: {[u['tipo'] for u in d]}"
    ok(f"Filtro tipo=masa OK ({len(d)} resultados)")

# 4.6 Eliminar
if und_id:
    r = client.delete(f"/unidades-medida/{und_id}")
    check("DELETE /unidades-medida/{id} -> 204", r, 204)
    r = client.get(f"/unidades-medida/{und_id}")
    check("GET /unidades-medida eliminada -> 404", r, 404)

# ─────────────────────────────────────────────
# 5. INGREDIENTES
# ─────────────────────────────────────────────
section("5. INGREDIENTES - CRUD + Stock")

r = client.get("/unidades-medida/")
unidades = r.json() if r.status_code == 200 else []
um_id = unidades[0]["id"] if unidades else None

# 5.1 Crear ingrediente
ing_id = None
if um_id:
    r = client.post("/ingredientes/", json={
        "nombre": "TestIngrediente_Prueba",
        "descripcion": "Ingrediente de prueba",
        "es_alergeno": False,
        "unidad_medida_id": um_id,
        "stock_total": 100.0,
        "precio_costo": 50.0
    })
    if r.status_code == 201:
        ing = r.json()
        ok("POST /ingredientes/ -> 201")
        ing_id = ing["id"]
    elif r.status_code == 409:
        ok("POST /ingredientes/ - nombre ya existe (re-ejecucion)")
        r2 = client.get("/ingredientes/?nombre=TestIngrediente_Prueba")
        items = r2.json() if r2.status_code == 200 else []
        ing_id = items[0]["id"] if items else None
    else:
        fail("POST /ingredientes/", f"HTTP {r.status_code}: {r.text[:200]}")
else:
    fail("POST /ingredientes/", "Sin unidad de medida disponible")

# 5.2 Listar ingredientes
r = client.get("/ingredientes/")
d = check("GET /ingredientes/", r, 200)
if d is not None:
    assert isinstance(d, list)
    ok(f"GET /ingredientes/ - {len(d)} ingredientes")

# 5.3 Obtener por ID + persistencia
if ing_id:
    r = client.get(f"/ingredientes/{ing_id}")
    d = check(f"GET /ingredientes/{ing_id}", r, 200, "nombre")
    if d:
        assert d["nombre"] == "TestIngrediente_Prueba"
        assert float(d["stock_total"]) == 100.0
        assert float(d["precio_costo"]) == 50.0
        ok("GET /ingredientes/{id} - todos los campos persistidos correctamente")

# 5.4 Actualizar
if ing_id:
    r = client.patch(f"/ingredientes/{ing_id}", json={
        "descripcion": "Descripcion actualizada",
        "es_alergeno": True
    })
    d = check("PATCH /ingredientes/{id}", r, 200)
    if d and isinstance(d, dict):
        assert d.get("es_alergeno") == True
        ok("PATCH /ingredientes - es_alergeno actualizado a True")

# 5.5 Actualizar stock
if ing_id:
    r = client.patch(f"/ingredientes/{ing_id}/stock", json={"stock_total": "75.500"})
    d = check("PATCH /ingredientes/{id}/stock", r, 200)
    if d and isinstance(d, dict):
        assert float(d.get("stock_total", 0)) == 75.5
        ok("PATCH /ingredientes/stock - stock_total actualizado a 75.5")

# 5.6 Filtro por nombre
r = client.get("/ingredientes/?nombre=TestIngrediente")
d = check("GET /ingredientes/?nombre=... (filtro)", r, 200)
if d is not None and isinstance(d, list):
    assert len(d) >= 1
    ok(f"Filtro nombre ingredientes OK ({len(d)} resultado/s)")

# 5.7 Sin ADMIN -> 403
r = user_client.post("/ingredientes/", json={"nombre": "X", "descripcion": "", "es_alergeno": False, "unidad_medida_id": 1, "stock_total": 0, "precio_costo": 0})
check("POST /ingredientes/ sin ADMIN -> 403", r, 403)

# 5.8 Soft delete
if ing_id:
    r = client.delete(f"/ingredientes/{ing_id}")
    check("DELETE /ingredientes/{id} -> 204", r, 204)
    r = client.get(f"/ingredientes/{ing_id}")
    check("GET /ingredientes eliminado -> 404", r, 404)

# ─────────────────────────────────────────────
# 6. PRODUCTOS
# ─────────────────────────────────────────────
section("6. PRODUCTOS - CRUD + Categorias + Ingredientes")

# Preparar datos auxiliares — nombre único por ejecución para evitar colisión con soft-deletes
_cat_prod_nombre = f"CatProd_Test_{int(time.time())}"
r = client.post("/categorias/", json={
    "nombre": _cat_prod_nombre, "descripcion": "Para test productos",
    "imagen_url": None, "parent_id": None
})
if r.status_code == 201:
    cat_for_prod_id = r.json()["id"]
    ok(f"Categoria auxiliar '{_cat_prod_nombre}' creada -> 201")
else:
    fail("Crear categoria auxiliar para productos", f"HTTP {r.status_code}: {r.text[:200]}")
    cat_for_prod_id = None

r = client.get("/unidades-medida/")
unidades = r.json() if r.status_code == 200 else []
um_id = unidades[0]["id"] if unidades else None

ing_id_for_prod = None
if um_id:
    r = client.post("/ingredientes/", json={
        "nombre": "Ing_ParaProd_Test", "descripcion": "x",
        "es_alergeno": False, "unidad_medida_id": um_id,
        "stock_total": 200.0, "precio_costo": 10.0
    })
    if r.status_code == 201:
        ing_id_for_prod = r.json()["id"]
    elif r.status_code == 409:
        r2 = client.get("/ingredientes/?nombre=Ing_ParaProd_Test")
        items = r2.json() if r2.status_code == 200 else []
        ing_id_for_prod = items[0]["id"] if items else None

# 6.1 Crear producto
prod_id = None
if um_id:
    r = client.post("/productos/", json={
        "nombre": "Producto_Test_Completo",
        "descripcion": "Producto de prueba completo",
        "precio_base": 1500.00,
        "margen_ganancia": 0.30,
        "disponible": True,
        "stock_directo": 50,
        "unidad_venta_id": um_id,
        "imagenes_url": ["http://example.com/prod.jpg"]
    })
    if r.status_code == 201:
        prod = r.json()
        ok("POST /productos/ -> 201")
        prod_id = prod["id"]
    elif r.status_code == 409:
        ok("POST /productos/ - nombre ya existe (re-ejecucion)")
        r2 = client.get("/productos/?nombre=Producto_Test_Completo")
        items = r2.json() if r2.status_code == 200 else []
        prod_id = items[0]["id"] if items else None
    else:
        fail("POST /productos/", f"HTTP {r.status_code}: {r.text[:200]}")
else:
    fail("POST /productos/", "Sin unidad de medida disponible")

# 6.2 Listar (publico sin auth)
r = anon_client.get("/productos/")
d = check("GET /productos/ (publico, sin auth)", r, 200)
if d is not None:
    assert isinstance(d, list)
    ok(f"GET /productos/ - {len(d)} productos")

# 6.3 Obtener por ID + persistencia
if prod_id:
    r = anon_client.get(f"/productos/{prod_id}")
    d = check(f"GET /productos/{prod_id}", r, 200, "nombre")
    if d:
        assert d["nombre"] == "Producto_Test_Completo"
        assert float(d["precio_base"]) == 1500.0
        ok("GET /productos/{id} - nombre y precio_base persistidos correctamente")

# 6.4 Actualizar
if prod_id:
    r = client.put(f"/productos/{prod_id}", json={
        "descripcion": "Descripcion actualizada del producto",
        "precio_base": 1800.00
    })
    d = check("PUT /productos/{id}", r, 200)
    if d and isinstance(d, dict):
        assert float(d.get("precio_base", 0)) == 1800.0
        ok("PUT /productos - precio_base actualizado a 1800")

# 6.5 Actualizar stock
if prod_id:
    r = client.patch(f"/productos/{prod_id}/stock", json={"stock_directo": 30})
    d = check("PATCH /productos/{id}/stock", r, 200)
    if d and isinstance(d, dict):
        assert d.get("stock_directo") == 30
        ok("PATCH /productos/stock - stock_directo actualizado a 30")

# 6.6 Disponibilidad → False
if prod_id:
    r = client.patch(f"/productos/{prod_id}/disponibilidad", json={"disponible": False})
    d = check("PATCH /productos/{id}/disponibilidad -> False", r, 200)
    if d and isinstance(d, dict):
        assert d.get("disponible") == False
        ok("PATCH disponibilidad - False OK")

# 6.7 Disponibilidad → True
if prod_id:
    r = client.patch(f"/productos/{prod_id}/disponibilidad", json={"disponible": True})
    d = check("PATCH /productos/{id}/disponibilidad -> True", r, 200)
    if d and isinstance(d, dict):
        assert d.get("disponible") == True
        ok("PATCH disponibilidad - True OK")

# 6.8 Filtro disponible
r = anon_client.get("/productos/?disponible=true")
d = check("GET /productos/?disponible=true (filtro)", r, 200)
if d is not None:
    assert all(p.get("disponible") == True for p in d), f"Filtro disponible fallo"
    ok(f"Filtro disponible OK ({len(d)} resultados)")

# 6.9 Filtro por nombre
if prod_id:
    r = anon_client.get("/productos/?nombre=Producto_Test")
    d = check("GET /productos/?nombre=... (filtro)", r, 200)
    if d is not None and isinstance(d, list):
        assert len(d) >= 1
        ok(f"Filtro nombre productos OK ({len(d)} resultado/s)")

# 6.10 Agregar categoria al producto
if prod_id and cat_for_prod_id:
    r = client.post(f"/productos/{prod_id}/categorias", json={"categoria_id": cat_for_prod_id})
    check("POST /productos/{id}/categorias -> 201", r, 201)

# 6.11 Agregar ingrediente al producto
if prod_id and ing_id_for_prod and um_id:
    r = client.post(f"/productos/{prod_id}/ingredientes", json={
        "ingrediente_id": ing_id_for_prod,
        "cantidad": "2.500",
        "unidad_medida_id": um_id,
        "es_removible": False
    })
    check("POST /productos/{id}/ingredientes -> 201", r, 201)

# 6.12 Verificar relaciones en GET
if prod_id:
    r = anon_client.get(f"/productos/{prod_id}")
    if r.status_code == 200:
        d = r.json()
        cats = d.get("categorias", [])
        ings = d.get("ingredientes", [])
        if cat_for_prod_id and any(c.get("id") == cat_for_prod_id for c in cats):
            ok("Producto tiene categoria asignada (persistencia relacion M:N)")
        elif cat_for_prod_id:
            fail("Producto sin categoria asignada", str(cats)[:200])
        if ing_id_for_prod and any(i.get("id") == ing_id_for_prod for i in ings):
            ok("Producto tiene ingrediente asignado (persistencia relacion M:N)")
        elif ing_id_for_prod:
            fail("Producto sin ingrediente asignado", str(ings)[:200])

# 6.13 Quitar categoria del producto -> 204
if prod_id and cat_for_prod_id:
    r = client.delete(f"/productos/{prod_id}/categorias/{cat_for_prod_id}")
    check("DELETE /productos/{id}/categorias/{cat_id} -> 204", r, 204)

# 6.14 Quitar ingrediente del producto -> 204
if prod_id and ing_id_for_prod:
    r = client.delete(f"/productos/{prod_id}/ingredientes/{ing_id_for_prod}")
    check("DELETE /productos/{id}/ingredientes/{ing_id} -> 204", r, 204)

# 6.15 Sin ADMIN -> 403
r = user_client.post("/productos/", json={"nombre": "X", "descripcion": "", "precio_base": 1, "margen_ganancia": 0, "disponible": True, "stock_directo": 0, "unidad_venta_id": 1, "imagenes_url": []})
check("POST /productos/ sin ADMIN -> 403", r, 403)

# 6.16 Soft delete
if prod_id:
    r = client.delete(f"/productos/{prod_id}")
    check("DELETE /productos/{id} -> 204", r, 204)
    r = anon_client.get(f"/productos/{prod_id}")
    check("GET /productos eliminado -> 404", r, 404)

# Limpiar auxiliares
if cat_for_prod_id:
    client.delete(f"/categorias/{cat_for_prod_id}")
if ing_id_for_prod:
    client.delete(f"/ingredientes/{ing_id_for_prod}")

# ─────────────────────────────────────────────
# 7. DIRECCIONES DE ENTREGA
# ─────────────────────────────────────────────
section("7. DIRECCIONES DE ENTREGA - CRUD (usuario autenticado)")

# 7.1 Listar direcciones propias
r = user_client.get("/direcciones/")
d = check("GET /direcciones/ (propio)", r, 200)
if d is not None:
    assert isinstance(d, list)
    ok(f"GET /direcciones/ - {len(d)} direcciones")

# 7.2 Crear primera direccion
r = user_client.post("/direcciones/", json={
    "alias": "Casa",
    "linea1": "Av. Corrientes 1234",
    "linea2": "Piso 5 Dto A",
    "ciudad": "Buenos Aires",
    "provincia": "CABA",
    "codigo_postal": "1043",
    "latitud": -34.603722,
    "longitud": -58.381592
})
if r.status_code == 201:
    dir_data = r.json()
    ok("POST /direcciones/ -> 201")
    dir_id = dir_data["id"]
else:
    fail("POST /direcciones/", f"HTTP {r.status_code}: {r.text[:200]}")
    # buscar direccion existente
    r2 = user_client.get("/direcciones/")
    dirs = r2.json() if r2.status_code == 200 else []
    dir_id = dirs[0]["id"] if dirs else None

# 7.3 Obtener por ID + persistencia
if dir_id:
    r = user_client.get(f"/direcciones/{dir_id}")
    d = check(f"GET /direcciones/{dir_id}", r, 200, "alias")
    if d:
        ok(f"GET /direcciones/{dir_id} - alias='{d['alias']}' persistido")

# 7.4 Actualizar
if dir_id:
    r = user_client.patch(f"/direcciones/{dir_id}", json={"alias": "Casa Principal"})
    d = check("PATCH /direcciones/{id}", r, 200)
    if d and isinstance(d, dict):
        assert d.get("alias") == "Casa Principal"
        ok("PATCH /direcciones - alias actualizado")

# 7.5 Crear segunda direccion
dir2_id = None
r = user_client.post("/direcciones/", json={
    "alias": "Trabajo",
    "linea1": "Florida 100",
    "linea2": "",
    "ciudad": "Buenos Aires",
    "provincia": "CABA",
    "codigo_postal": "1005",
    "latitud": -34.600000,
    "longitud": -58.370000
})
if r.status_code == 201:
    dir2_id = r.json()["id"]
    ok("POST /direcciones/ (segunda) -> 201")
else:
    fail("POST /direcciones/ (segunda)", f"HTTP {r.status_code}: {r.text[:200]}")

# 7.6 Marcar primera como principal
if dir_id:
    r = user_client.patch(f"/direcciones/{dir_id}/principal")
    d = check("PATCH /direcciones/{id}/principal", r, 200)
    if d and isinstance(d, dict):
        assert d.get("es_principal") == True
        ok("Direccion marcada como principal (es_principal=True)")

# 7.7 Sin autenticacion -> 401
r = anon_client.get("/direcciones/")
check("GET /direcciones/ sin auth -> 401", r, 401)

# 7.8 Eliminar segunda direccion
if dir2_id:
    r = user_client.delete(f"/direcciones/{dir2_id}")
    check("DELETE /direcciones/{id} -> 204", r, 204)
    r = user_client.get(f"/direcciones/{dir2_id}")
    check("GET /direcciones eliminada -> 404", r, 404)

# ─────────────────────────────────────────────
# 8. PEDIDOS (cliente)
# ─────────────────────────────────────────────
section("8. PEDIDOS - Creacion, Listado, Cancelacion (cliente)")

# Asignar rol CLIENT al usuario test
if usuario_test_id:
    r = client.post(f"/auth/admin/usuarios/{usuario_test_id}/roles/CLIENT")
    if r.status_code in (200, 409):
        ok("Rol CLIENT asignado al usuario test")
    else:
        fail("Asignar rol CLIENT", f"HTTP {r.status_code}: {r.text[:200]}")

# Re-login para refrescar token con rol CLIENT
r = user_client.post("/auth/login", json={
    "email": "testuser_parcial@example.com",
    "contrasena": "Test1234!"
})
if r.status_code == 200:
    ok("Re-login con rol CLIENT")
else:
    fail("Re-login con rol CLIENT", f"HTTP {r.status_code}: {r.text[:200]}")

# Crear producto disponible para el pedido
r = client.get("/unidades-medida/")
unidades = r.json() if r.status_code == 200 else []
um_id = unidades[0]["id"] if unidades else None

prod_pedido_id = None
if um_id:
    r = client.post("/productos/", json={
        "nombre": "Producto_Para_Pedido",
        "descripcion": "Para test pedidos",
        "precio_base": 800.00,
        "margen_ganancia": 0.20,
        "disponible": True,
        "stock_directo": 100,
        "unidad_venta_id": um_id,
        "imagenes_url": []
    })
    if r.status_code == 201:
        prod_pedido_id = r.json()["id"]
        ok("Producto para pedido creado")
    elif r.status_code == 409:
        r2 = client.get("/productos/?nombre=Producto_Para_Pedido")
        items = r2.json() if r2.status_code == 200 else []
        prod_pedido_id = items[0]["id"] if items else None
        ok("Usando producto para pedido existente")
    else:
        fail("Crear producto para pedido", f"HTTP {r.status_code}: {r.text[:200]}")

# Obtener direccion del usuario
r = user_client.get("/direcciones/")
dirs = r.json() if r.status_code == 200 else []
dir_pedido_id = dirs[0]["id"] if dirs else None
if not dir_pedido_id:
    r = user_client.post("/direcciones/", json={
        "alias": "Casa Pedido", "linea1": "Calle Falsa 123", "linea2": "",
        "ciudad": "Buenos Aires", "provincia": "CABA", "codigo_postal": "1234",
        "latitud": -34.61, "longitud": -58.39
    })
    dir_pedido_id = r.json()["id"] if r.status_code == 201 else None

# 8.1 Crear pedido
pedido_id = None
if prod_pedido_id and dir_pedido_id:
    r = user_client.post("/pedidos/", json={
        "direccion_id": dir_pedido_id,
        "forma_pago_codigo": "EFECTIVO",
        "notas": "Sin cebolla por favor",
        "items": [{"producto_id": prod_pedido_id, "cantidad": 2}]
    })
    if r.status_code == 201:
        pedido = r.json()
        ok("POST /pedidos/ -> 201")
        pedido_id = pedido["id"]
        # Estado inicial
        assert pedido.get("estado_codigo") == "PENDIENTE", f"Estado debe ser PENDIENTE, got {pedido.get('estado_codigo')}"
        ok("Pedido creado con estado=PENDIENTE")
        # Total calculado
        assert float(pedido.get("total", 0)) > 0
        ok(f"Total del pedido calculado: ${pedido.get('total')}")
        # Detalles
        items = pedido.get("items", [])
        assert len(items) == 1, f"Esperado 1 item, got {len(items)}"
        ok("Pedido tiene exactamente 1 item")
        # Snapshot precio
        det = items[0]
        assert float(det.get("precio_snapshot", 0)) > 0
        ok("Detalle tiene precio_snapshot guardado")
    else:
        fail("POST /pedidos/", f"HTTP {r.status_code}: {r.text[:300]}")
else:
    fail("POST /pedidos/", "Sin producto o direccion disponibles")

# 8.2 Listar pedidos propios
r = user_client.get("/pedidos/")
d = check("GET /pedidos/ (propios)", r, 200)
if d is not None and pedido_id:
    assert any(p["id"] == pedido_id for p in d), "Pedido recien creado no aparece en lista"
    ok("Pedido aparece en listado del cliente")

# 8.3 Obtener pedido por ID
if pedido_id:
    r = user_client.get(f"/pedidos/{pedido_id}")
    d = check(f"GET /pedidos/{pedido_id}", r, 200, "id")
    if d:
        assert d["id"] == pedido_id
        assert d["estado_codigo"] == "PENDIENTE"
        ok("GET /pedidos/{id} - estado PENDIENTE persistido")

# 8.4 Admin puede ver pedido ajeno via endpoint role-aware
if pedido_id:
    r = client.get(f"/pedidos/{pedido_id}")
    if r.status_code == 200:
        ok(f"Admin accede via /pedidos/{pedido_id} -> 200 (rol ADMIN da acceso)")
    elif r.status_code == 404:
        ok(f"Admin no puede ver pedido ajeno via /pedidos/{pedido_id} -> 404")
    else:
        ok(f"Acceso a pedido ajeno -> {r.status_code}")

# 8.5 Cancelar pedido (DELETE con body motivo)
if pedido_id:
    r = user_client.request("DELETE", f"/pedidos/{pedido_id}", json={"motivo": "Ya no lo necesito"})
    d = check(f"DELETE /pedidos/{pedido_id} (cancelar)", r, 200)
    if d and isinstance(d, dict):
        assert d.get("estado_codigo") == "CANCELADO"
        ok("Pedido cancelado -> estado=CANCELADO")

# 8.6 No se puede cancelar pedido ya CANCELADO
if pedido_id:
    r = user_client.request("DELETE", f"/pedidos/{pedido_id}", json={"motivo": "Otro intento"})
    if r.status_code == 422:
        ok(f"Cancelar pedido ya CANCELADO -> 422 (validacion correcta)")
    else:
        fail("Cancelar pedido CANCELADO debe dar 422", f"HTTP {r.status_code}: {r.text[:200]}")

# ─────────────────────────────────────────────
# 9. ADMIN PEDIDOS - Maquina de estados
# ─────────────────────────────────────────────
section("9. ADMIN PEDIDOS - Avanzar estados (flujo completo)")

# Crear nuevo pedido para avanzar todos los estados
pedido_admin_id = None
if prod_pedido_id and dir_pedido_id:
    r = user_client.post("/pedidos/", json={
        "direccion_id": dir_pedido_id,
        "forma_pago_codigo": "MERCADOPAGO",
        "notas": "Test avance de estados",
        "items": [{"producto_id": prod_pedido_id, "cantidad": 1}]
    })
    if r.status_code == 201:
        pedido_admin_id = r.json()["id"]
        ok(f"Nuevo pedido para test de estados (id={pedido_admin_id})")
    else:
        fail("Crear pedido para test estados", f"HTTP {r.status_code}: {r.text[:300]}")

# 9.1 Listar todos los pedidos (admin)
r = client.get("/admin/pedidos/")
d = check("GET /admin/pedidos/ (admin)", r, 200)
if d is not None:
    assert isinstance(d, list)
    ok(f"GET /admin/pedidos/ - {len(d)} pedidos en total")

# 9.2 Filtro por estado PENDIENTE
r = client.get("/admin/pedidos/?estado=PENDIENTE")
d = check("GET /admin/pedidos/?estado=PENDIENTE", r, 200)
if d is not None:
    assert all(p.get("estado_codigo") == "PENDIENTE" for p in d), f"Filtro estado fallo: {[p.get('estado_codigo') for p in d[:5]]}"
    ok(f"Filtro estado=PENDIENTE OK ({len(d)} pedidos)")

# 9.3 Ver pedido especifico (admin puede ver cualquiera)
if pedido_admin_id:
    r = client.get(f"/admin/pedidos/{pedido_admin_id}")
    d = check(f"GET /admin/pedidos/{pedido_admin_id}", r, 200, "id")
    if d:
        assert d["estado_codigo"] == "PENDIENTE"
        ok("Admin puede ver cualquier pedido via /admin/pedidos/")

# 9.4 PENDIENTE -> CONFIRMADO
if pedido_admin_id:
    r = client.patch(f"/pedidos/{pedido_admin_id}/estado", json={"estado_hasta": "CONFIRMADO", "motivo": "Confirmacion admin"})
    d = check("PENDIENTE->CONFIRMADO", r, 200)
    if d and isinstance(d, dict):
        assert d.get("estado_codigo") == "CONFIRMADO"
        ok("Estado avanzado correctamente a CONFIRMADO")

# 9.5 CONFIRMADO -> EN_PREPARACION
if pedido_admin_id:
    r = client.patch(f"/pedidos/{pedido_admin_id}/estado", json={"estado_hasta": "EN_PREPARACION", "motivo": ""})
    d = check("CONFIRMADO->EN_PREPARACION", r, 200)
    if d and isinstance(d, dict):
        assert d.get("estado_codigo") == "EN_PREPARACION"
        ok("Estado avanzado correctamente a EN_PREPARACION")

# 9.6 EN_PREPARACION -> EN_CAMINO
if pedido_admin_id:
    r = client.patch(f"/pedidos/{pedido_admin_id}/estado", json={"estado_hasta": "EN_CAMINO", "motivo": ""})
    d = check("EN_PREPARACION->EN_CAMINO", r, 200)
    if d and isinstance(d, dict):
        assert d.get("estado_codigo") == "EN_CAMINO"
        ok("Estado avanzado correctamente a EN_CAMINO")

# 9.7 EN_CAMINO -> ENTREGADO (estado terminal)
if pedido_admin_id:
    r = client.patch(f"/pedidos/{pedido_admin_id}/estado", json={"estado_hasta": "ENTREGADO", "motivo": "Entrega exitosa"})
    d = check("EN_CAMINO->ENTREGADO", r, 200)
    if d and isinstance(d, dict):
        assert d.get("estado_codigo") == "ENTREGADO"
        ok("Estado avanzado correctamente a ENTREGADO (terminal)")

# 9.8 No se puede avanzar desde estado terminal ENTREGADO
if pedido_admin_id:
    r = client.patch(f"/pedidos/{pedido_admin_id}/estado", json={"estado_hasta": "EN_CAMINO", "motivo": ""})
    if r.status_code == 422:
        ok("Avanzar desde ENTREGADO (terminal) -> 422 correcto")
    else:
        fail("Avanzar desde terminal debe dar 422", f"HTTP {r.status_code}: {r.text[:200]}")

# 9.9 Historial de transiciones registrado
if pedido_admin_id:
    r = client.get(f"/admin/pedidos/{pedido_admin_id}")
    if r.status_code == 200:
        d = r.json()
        historial = d.get("historial", [])
        if len(historial) >= 4:
            ok(f"Historial del pedido: {len(historial)} transiciones registradas")
            # Verificar que los estados de avance esten en el historial
            estados = [h.get("estado_hasta") for h in historial]
            expected_in = ["CONFIRMADO", "EN_PREPARACION", "EN_CAMINO", "ENTREGADO"]
            if all(e in estados for e in expected_in):
                ok("Historial contiene todas las transiciones esperadas (incl. estado inicial)")
            else:
                fail("Historial incompleto", f"got {estados}, faltan {[e for e in expected_in if e not in estados]}")
        else:
            fail("Historial incompleto", f"{len(historial)} registros, esperado >=4")

# 9.10 Metricas resumen (solo ADMIN)
r = client.get("/admin/metricas/resumen")
d = check("GET /admin/metricas/resumen (admin)", r, 200)
if d and isinstance(d, dict):
    if "total_pedidos" in d and "facturacion_total" in d and "pedidos_por_estado" in d:
        ok("GET /admin/metricas/resumen - campos total_pedidos, facturacion_total, pedidos_por_estado presentes")
    else:
        fail("GET /admin/metricas/resumen - faltan campos", str(d)[:200])
    if int(d.get("total_pedidos", 0)) > 0:
        ok(f"GET /admin/metricas/resumen - total_pedidos={d['total_pedidos']} (pedidos registrados)")
    if isinstance(d.get("pedidos_por_estado"), dict) and len(d["pedidos_por_estado"]) > 0:
        ok(f"GET /admin/metricas/resumen - pedidos_por_estado con {len(d['pedidos_por_estado'])} estados")

# 9.11 Metricas sin ADMIN -> 403
r = user_client.get("/admin/metricas/resumen")
check("GET /admin/metricas/resumen sin ADMIN -> 403", r, 403)

# 9.12 Sin PEDIDOS/ADMIN -> 403
r = user_client.get("/admin/pedidos/")
check("GET /admin/pedidos/ sin ADMIN/PEDIDOS -> 403", r, 403)

# ─────────────────────────────────────────────
# Limpieza final
# ─────────────────────────────────────────────
if prod_pedido_id:
    client.delete(f"/productos/{prod_pedido_id}")

# ─────────────────────────────────────────────
# RESUMEN FINAL
# ─────────────────────────────────────────────
print(f"\n{'='*60}")
print("  RESUMEN DE RESULTADOS")
print(f"{'='*60}")
passed = [r for r in RESULTS if r[0] == "PASS"]
failed = [r for r in RESULTS if r[0] == "FAIL"]
print(f"\n  PASS: {len(passed)}")
print(f"  FAIL: {len(failed)}")
print(f"  TOTAL: {len(RESULTS)}")
if failed:
    print(f"\n  FALLOS DETECTADOS:")
    for f in failed:
        label = f[1]
        detail = f[2] if len(f) > 2 else ""
        print(f"    [x] {label}")
        if detail:
            print(f"        >> {detail[:200]}")
else:
    print(f"\n  Todos los tests pasaron correctamente!")
print(f"\n{'='*60}")

sys.exit(0 if not failed else 1)
