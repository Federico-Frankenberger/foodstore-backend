import os
from sqlmodel import Session, create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL no está configurada. Revisá el archivo .env")

motor = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"options": "-c client_encoding=utf8"},
)


def get_session():
    return Session(motor)
