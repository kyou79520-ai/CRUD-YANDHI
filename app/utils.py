from functools import wraps
from flask import jsonify, g, current_app
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from .models import LogEntry
from . import db


def role_required(allowed_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception as e:
                # TEMPORAL: Ver el error real
                current_app.logger.error(f"JWT verification failed: {str(e)}")
                return jsonify({"msg":"Token missing or invalid", "error": str(e)}), 401
            
            identity = get_jwt_identity()
            if not identity:
                return jsonify({"msg":"No identity in token"}), 401
            
            role = identity.get("role")
            if not role:
                return jsonify({"msg":"No role in token identity"}), 401
            
            if role not in allowed_roles:
                return jsonify({"msg":"Access forbidden for role"}), 403
            
            # attach user identity to g for logging
            g.current_user = identity
            return fn(*args, **kwargs)
        return wrapper
    return decorator