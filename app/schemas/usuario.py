from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UsuarioCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=80)
    apellido: str = Field(min_length=2, max_length=80)
    email: EmailStr
    celular: Optional[str] = Field(default=None, max_length=20)
    contrasena: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    contrasena: str


class UsuarioAdminUpdate(BaseModel):
    activo: Optional[bool] = None
    roles: Optional[list[str]] = None


class UsuarioPublico(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: str
    celular: Optional[str] = None
    roles: list[str] = []
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expira_en: int
