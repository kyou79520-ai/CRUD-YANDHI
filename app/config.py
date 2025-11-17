import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Claves necesarias
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecret123")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwtsecret456")
    
    # Base de datos — Railway/Render envía DATABASE_URL automáticamente
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:qFlKJSWOPANJLYOaqOjvylicHSOHojQJ@postgres.railway.internal:5432/railway"
    )

    # Corrección automática del formato 'postgres://' → 'postgresql://'
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url

    # SQLAlchemy mejora
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Logs
    LOG_FILE = os.getenv("LOG_FILE", "app_operations.log")
