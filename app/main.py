from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

import app.models

from alembic.config import Config
from alembic import command
from app.core.config import configuracion
from app.core.rate_limiter import limiter
from app.db.seed import ejecutar_seed
from app.routers import auth, categorias, direcciones, ingredientes, pedidos, productos, unidades_medida


def aplicar_migraciones() -> None:
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    aplicar_migraciones()
    ejecutar_seed()
    yield


app = FastAPI(
    title="API Parcial 1 - Catálogo de Productos",
    description="Backend del parcial integrador — FastAPI + SQLModel + PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=configuracion.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://httpstatuses.io/{exc.status_code}",
            "title": exc.detail if isinstance(exc.detail, str) else "Error",
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": str(request.url.path),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "type": "https://httpstatuses.io/422",
            "title": "Unprocessable Entity",
            "status": 422,
            "detail": exc.errors(),
            "instance": str(request.url.path),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "type": "https://httpstatuses.io/500",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "Error interno del servidor",
            "instance": str(request.url.path),
        },
    )


_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=_PREFIX)
app.include_router(direcciones.router, prefix=_PREFIX)
app.include_router(categorias.router, prefix=_PREFIX)
app.include_router(ingredientes.router, prefix=_PREFIX)
app.include_router(productos.router, prefix=_PREFIX)
app.include_router(unidades_medida.router, prefix=_PREFIX)
app.include_router(pedidos.router, prefix=_PREFIX)
