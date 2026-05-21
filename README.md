# Primer Parcial — Programación IV

Backend REST API desarrollado con **FastAPI**, **SQLModel** y **PostgreSQL** como parte del primer parcial integrador de Programación IV (Food Store v5.0).

## Integrantes

- Federico Frankenberger
- Emilia Barros
- Miguel Barrera
- Guadalupe Maricchiolo

## Video de presentación

<!-- Reemplazá este link con el link real del video una vez subido -->
[Ver video de presentación](https://youtu.be/LINK_DEL_VIDEO)

---

## Descripción

API completa para la gestión de una tienda de comida con:

- **Autenticación** — JWT HS256 (access 30 min) + Refresh Token 7 días con rotación (RTR). Cookies HttpOnly, SameSite=Strict. Replay attack mitigation con revocación masiva de sesiones.
- **RBAC** — 4 roles: `ADMIN`, `STOCK`, `PEDIDOS`, `CLIENT`.
- **Catálogo** — CRUD completo de Categorías (árbol jerárquico), Ingredientes, Productos y Unidades de Medida. Relaciones N:N Producto–Categoría y Producto–Ingrediente.
- **Pedidos** — Máquina de estados `PENDIENTE → CONFIRMADO → EN_PREPARACION → EN_CAMINO → ENTREGADO / CANCELADO`. Stock descontado al crear y restaurado al cancelar. Historial de transiciones. Snapshot de precio y dirección al momento de la compra.
- **Direcciones de entrega** — CRUD con soporte para dirección principal por usuario.
- **Métricas** — Resumen de facturación y pedidos por estado para administradores.
- **Seguridad adicional** — Rate limiting en login (5/15 min), CORS configurable, RFC 7807 Problem Details en todos los errores, soft delete en entidades principales.

---

## Requisitos

- Python 3.11+
- Docker (para la base de datos PostgreSQL)

---

## Instalación y ejecución

```bash
# 1. Clonar el repositorio y entrar al directorio backend
git clone <url-del-repositorio>
cd Primer_Parcial_Prog4/backend

# 2. Crear entorno virtual e instalar dependencias
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con los datos reales (ver sección Variables de entorno)

# 4. Levantar la base de datos con Docker
cd ..
docker-compose up -d
cd backend

# 5. Iniciar el servidor (puerto 8000 por defecto)
uvicorn app.main:app --reload
```

Las migraciones Alembic y el seed inicial (roles, estados, formas de pago, usuario admin) se aplican automáticamente al iniciar el servidor.

**Credenciales del admin por defecto:**
```
email:    admin@foodstore.com
password: Admin1234!
```

---

## Variables de entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | URL de conexión PostgreSQL | `postgresql+psycopg://user:pass@localhost:5435/db` |
| `SECRET_KEY` | Clave HMAC para JWT (mín. 32 chars) | `una-clave-muy-secreta-de-produccion` |
| `DIAS_EXPIRACION_REFRESH_TOKEN` | Vida del refresh token en días | `7` |
| `CORS_ORIGINS` | Orígenes permitidos (JSON array) | `["http://localhost:5173"]` |
| `COOKIES_SECURE` | `true` en producción (HTTPS), `false` en desarrollo HTTP | `true` |
| `RATE_LIMIT_LOGIN` | Límite de intentos de login | `5/15minutes` |

---

## Endpoints principales

La documentación interactiva completa está disponible en **`/docs`** (Swagger UI) una vez levantado el servidor.

| Módulo | Endpoints |
|---|---|
| Auth | `POST /api/v1/auth/register` · `POST /api/v1/auth/login` · `POST /api/v1/auth/refresh` · `POST /api/v1/auth/logout` · `GET /api/v1/auth/me` |
| Admin usuarios | `GET /api/v1/auth/admin/usuarios` · `PUT /api/v1/auth/admin/usuarios/{id}` · `POST/DELETE /api/v1/auth/admin/usuarios/{id}/roles/{rol}` |
| Categorías | `GET/POST /api/v1/categorias/` · `GET /api/v1/categorias/arbol` · `PUT/DELETE /api/v1/categorias/{id}` |
| Ingredientes | `GET/POST /api/v1/ingredientes/` · `PATCH /api/v1/ingredientes/{id}` · `PATCH /api/v1/ingredientes/{id}/stock` |
| Productos | `GET/POST /api/v1/productos/` · `PUT /api/v1/productos/{id}` · `PATCH /api/v1/productos/{id}/disponibilidad` |
| Direcciones | `GET/POST /api/v1/direcciones/` · `PATCH /api/v1/direcciones/{id}` · `PATCH /api/v1/direcciones/{id}/principal` |
| Pedidos | `POST /api/v1/pedidos/` · `GET /api/v1/pedidos/{id}` · `DELETE /api/v1/pedidos/{id}` · `PATCH /api/v1/pedidos/{id}/estado` |
| Admin pedidos | `GET /api/v1/admin/pedidos/` · `GET /api/v1/admin/pedidos/{id}` · `GET /api/v1/admin/metricas/resumen` |

### Autenticación desde el frontend

Las cookies son **HttpOnly** — el JS no puede leerlas, el browser las adjunta automáticamente. Cada request debe incluir credenciales:

```js
// fetch
fetch(url, { credentials: 'include' })

// axios
axios.defaults.withCredentials = true
```

---

## Tests

### Suite de integración (pytest) — BD de test aislada

```bash
# Requiere el contenedor Docker activo (crea parcial_test_db automáticamente)
pytest tests/ -v
```

103 tests cubriendo auth, usuarios, direcciones y pedidos.

### Test completo contra servidor real

```bash
# Requiere el servidor corriendo en localhost:8001
uvicorn app.main:app --port 8001

python test_completo.py
```

136 tests cubriendo todos los endpoints de la API.

---

## Estructura del proyecto

```
backend/
├── app/
│   ├── main.py              # Lifespan, middleware, routers
│   ├── core/
│   │   ├── config.py        # Pydantic Settings (lee .env)
│   │   ├── security.py      # JWT, bcrypt, hash tokens
│   │   ├── deps.py          # Dependencias FastAPI (auth, roles)
│   │   └── rate_limiter.py  # slowapi limiter
│   ├── models/              # SQLModel — tablas de la BD
│   ├── schemas/             # Pydantic — request/response
│   ├── repositories/        # Acceso a datos (BaseRepository[T])
│   ├── services/            # Lógica de negocio
│   ├── routers/             # Endpoints HTTP
│   ├── uow/                 # Unit of Work
│   └── db/
│       └── seed.py          # Datos iniciales (roles, estados, admin)
├── alembic/                 # Migraciones de base de datos
├── tests/                   # Suite pytest (integración)
├── test_completo.py         # Test end-to-end contra servidor real
├── .env.example             # Plantilla de variables de entorno
└── requirements.txt
```
