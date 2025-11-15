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
            except Exception:
                return jsonify({"msg":"Token missing or invalid"}), 401
            identity = get_jwt_identity()
            role = identity.get("role")
            if role not in allowed_roles:
                return jsonify({"msg":"Access forbidden for role"}), 403
            # attach user identity to g for logging
            g.current_user = identity
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def log_db_action(action, details=""):
    from flask import current_app, g
    identity = getattr(g, "current_user", None)
    uid = identity.get("id") if identity else None
    uname = identity.get("username") if identity else None
    try:
        le = LogEntry(user_id=uid, username=uname, action=action, details=details)
        db.session.add(le)
        db.session.commit()
    except Exception:
        current_app.logger.exception("failed to write db log")
    current_app.logger.info(f"USER={uname} ACTION={action} DETAILS={details}")
