from pydantic_settings import BaseSettings


class Configuracion(BaseSettings):
    SECRET_KEY: str
    ALGORITMO: str = "HS256"
    MINUTOS_EXPIRACION_TOKEN: int = 30
    DIAS_EXPIRACION_REFRESH_TOKEN: int = 7
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    COOKIES_SECURE: bool = True
    RATE_LIMIT_LOGIN: str = "5/15minutes"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


configuracion = Configuracion()
