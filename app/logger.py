import logging
from logging.handlers import RotatingFileHandler
from flask import g

def setup_app_logger(app):
    log_file = app.config.get("LOG_FILE", "app_operations.log")
    handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=2)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
