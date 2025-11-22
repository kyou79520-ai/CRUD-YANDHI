from functools import wraps
from flask import jsonify, g, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from .models import LogEntry
from . import db
import json

def role_required(allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception as e:
                current_app.logger.error(f"JWT verification failed: {str(e)}")
                return jsonify({"msg": "Token missing or invalid", "error": str(e)}), 401
            
            # Obtener el identity (es un string JSON)
            identity_string = get_jwt_identity()
            
            if not identity_string:
                return jsonify({"msg": "No identity in token"}), 401
            
            try:
                # Convertir de string JSON a diccionario
                identity = json.loads(identity_string)
            except json.JSONDecodeError:
                current_app.logger.error("Failed to parse JWT identity")
                return jsonify({"msg": "Invalid token format"}), 401
            
            role = identity.get("role")
            if not role:
                return jsonify({"msg": "No role in token identity"}), 401
            
            if role not in allowed_roles:
                return jsonify({"msg": "Access forbidden for role"}), 403
            
            # Adjuntar identidad del usuario a g para logging
            g.current_user = identity
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def log_db_action(action, details=None):
    """
    Registra acciones de base de datos para auditoría
    """
    try:
        user_id = g.current_user.get("id") if hasattr(g, 'current_user') else None
        username = g.current_user.get("username") if hasattr(g, 'current_user') else "system"
        
        log_entry = LogEntry(
            action=action,
            details=details,
            user_id=user_id,
            username=username
        )
        db.session.add(log_entry)
        db.session.commit()
        current_app.logger.info(f"[DB_ACTION] {action} by {username} - {details}")
    except Exception as e:
        current_app.logger.error(f"Error logging action: {str(e)}")
        # No fallar si el log falla
        pass