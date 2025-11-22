import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Claves necesarias
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecret123")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwtsecret456")

    # Base de datos — Railway/Render proveen DATABASE_URL
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://localhost/yandhi_db"
    )

    # Corrección: 'postgres://' → 'postgresql+psycopg2://'
    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql+psycopg2://",
            1
        )

    # Corrección: 'postgresql://' → 'postgresql+psycopg2://'
    if database_url.startswith("postgresql://") and "+psycopg2" not in database_url:
        database_url = database_url.replace(
            "postgresql://",
            "postgresql+psycopg2://",
            1
        )

    SQLALCHEMY_DATABASE_URI = database_url

    # Mejores prácticas de SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Configuración de JWT (AGREGADO)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_IDENTITY_CLAIM = 'sub'
    
    # Logs
    LOG_FILE = os.getenv("LOG_FILE", "app_operations.log")