import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Claves necesarias
    SECRET_KEY = os.getenv("supersecret123")
    JWT_SECRET_KEY = os.getenv("jwtsecret456")

    # Base de datos — Railway te da DATABASE_URL automáticamente
    SQLALCHEMY_DATABASE_URI = os.getenv("postgresql://crud_yandhi_db_user:B0MnZON06afdwf413CNHhvbWub9zs4EC@dpg-d4d9buk9c44c73980hig-a/crud_yandhi_db")

    # Config extra
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Logs
    LOG_FILE = os.getenv("LOG_FILE", "app_operations.log")
