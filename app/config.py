import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Claves necesarias
    SECRET_KEY = os.getenv("supersecret123")
    JWT_SECRET_KEY = os.getenv("jwtsecret456")

    # Base de datos — Railway te da DATABASE_URL automáticamente
    SQLALCHEMY_DATABASE_URI = os.getenv("postgresql://postgres:qFlKJSWOPANJLYOaqOjvylicHSOHojQJ@postgres.railway.internal:5432/railway")

    # Config extra
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Logs
    LOG_FILE = os.getenv("LOG_FILE", "app_operations.log")
