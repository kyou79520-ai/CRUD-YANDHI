from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .models import User, LogEntry
from . import db
import json

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
    
    # Crear el identity como diccionario
    user_data = {
        "id": user.id,
        "username": user.username,
        "role": user.role.name
    }
    
    # Convertir a string JSON para el token
    identity_string = json.dumps(user_data)
    
    # Crear token con string como identity
    access_token = create_access_token(identity=identity_string)
    
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
    
    # Devolver token y usuario
    return jsonify({
        "access_token": access_token,
        "user": user_data
    }), 200

@bp.route("/whoami", methods=["GET"])
@jwt_required()
def whoami():
    # Obtener el identity (string) y convertirlo de vuelta a dict
    identity_string = get_jwt_identity()
    identity = json.loads(identity_string)
    return jsonify(identity)