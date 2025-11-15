from flask import Blueprint, request, jsonify, current_app, g
from . import db
from .models import User, Role, Project, Task
from .utils import role_required, log_db_action
from .auth import bp as auth_bp

bp = Blueprint("api", __name__)
bp.register_blueprint(auth_bp)

# --- User management (admin only for creating other users)
@bp.route("/users", methods=["POST"])
@role_required(["admin"])
def create_user():
    data = request.json
    username = data.get("username"); password = data.get("password"); role_name = data.get("role","viewer")
    if not username or not password:
        return jsonify({"msg":"username and password required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"msg":"username exists"}), 400
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return jsonify({"msg":"invalid role"}), 400
    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user); db.session.commit()
    log_db_action("create_user", f"created user {username}")
    return jsonify({"id": user.id, "username": user.username}), 201

@bp.route("/users/<int:user_id>", methods=["DELETE"])
@role_required(["admin"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user); db.session.commit()
    log_db_action("delete_user", f"deleted user id={user_id}")
    return jsonify({"msg":"deleted"})

# --- Projects CRUD
@bp.route("/projects", methods=["POST"])
@role_required(["admin","manager"])
def create_project():
    data = request.json
    p = Project(name=data.get("name"), description=data.get("description"), created_by=g.current_user["id"])
    db.session.add(p); db.session.commit()
    log_db_action("create_project", f"project_id={p.id}")
    return jsonify({"id": p.id, "name": p.name}), 201

@bp.route("/projects", methods=["GET"])
@role_required(["admin","manager","viewer"])
def list_projects():
    projects = Project.query.all()
    return jsonify([{"id":p.id,"name":p.name,"description":p.description} for p in projects])

@bp.route("/projects/<int:pid>", methods=["PUT"])
@role_required(["admin","manager"])
def edit_project(pid):
    p = Project.query.get_or_404(pid)
    data = request.json
    p.name = data.get("name", p.name)
    p.description = data.get("description", p.description)
    db.session.commit()
    log_db_action("edit_project", f"project_id={pid}")
    return jsonify({"msg":"updated"})

@bp.route("/projects/<int:pid>", methods=["DELETE"])
@role_required(["admin"])
def delete_project(pid):
    p = Project.query.get_or_404(pid)
    db.session.delete(p); db.session.commit()
    log_db_action("delete_project", f"project_id={pid}")
    return jsonify({"msg":"deleted"})

# --- Tasks CRUD
@bp.route("/tasks", methods=["POST"])
@role_required(["admin","manager"])
def create_task():
    data = request.json
    t = Task(title=data.get("title"), details=data.get("details"), status=data.get("status","pending"),
             project_id=data.get("project_id"), assigned_to=data.get("assigned_to"))
    db.session.add(t); db.session.commit()
    log_db_action("create_task", f"task_id={t.id}")
    return jsonify({"id": t.id, "title": t.title}), 201

@bp.route("/tasks", methods=["GET"])
@role_required(["admin","manager","viewer"])
def list_tasks():
    tasks = Task.query.all()
    return jsonify([{"id":t.id,"title":t.title,"status":t.status,"project_id":t.project_id} for t in tasks])

@bp.route("/tasks/<int:tid>", methods=["PUT"])
@role_required(["admin","manager"])
def update_task(tid):
    t = Task.query.get_or_404(tid)
    data = request.json
    t.title = data.get("title", t.title)
    t.details = data.get("details", t.details)
    t.status = data.get("status", t.status)
    db.session.commit()
    log_db_action("update_task", f"task_id={tid}")
    return jsonify({"msg":"updated"})

@bp.route("/tasks/<int:tid>", methods=["DELETE"])
@role_required(["admin","manager"])
def delete_task(tid):
    t = Task.query.get_or_404(tid)
    db.session.delete(t); db.session.commit()
    log_db_action("delete_task", f"task_id={tid}")
    return jsonify({"msg":"deleted"})
