from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .models import User, LogEntry
from . import db

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"msg": "username and password required"}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({"msg": "Invalid credentials"}), 401
    
    # Crear el token con la información del usuario
    access_token = create_access_token(
        identity={
            "id": user.id, 
            "username": user.username, 
            "role": user.role.name
        }
    )
    
    # Log de login
    try:
        le = LogEntry(
            user_id=user.id, 
            username=user.username, 
            action="login", 
            details="Login exitoso"
        )
        db.session.add(le)
        db.session.commit()
    except Exception:
        current_app.logger.exception("failed to write login log")
    
    current_app.logger.info(f"USER={user.username} ACTION=login")
    
    # IMPORTANTE: Devolver tanto el token como la info del usuario
    return jsonify({
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role.name
        }
    }), 200

@bp.route("/whoami", methods=["GET"])
@jwt_required()
def whoami():
    identity = get_jwt_identity()
    return jsonify(identity)