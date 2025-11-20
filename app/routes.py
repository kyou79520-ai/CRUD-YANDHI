from flask import Blueprint, request, jsonify, current_app, g
from . import db
from .models import User, Role, Customer, Product, Sale, SaleItem, LogEntry
from .utils import role_required, log_db_action
from .auth import bp as auth_bp

bp = Blueprint("api", __name__)
bp.register_blueprint(auth_bp)

# ==================== USERS ====================
@bp.route("/users", methods=["POST"])
@role_required(["admin"])
def create_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    role_name = data.get("role", "viewer")
    
    if not username or not password:
        return jsonify({"msg": "username and password required"}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "username exists"}), 400
    
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return jsonify({"msg": "invalid role"}), 400
    
    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    log_db_action("create_user", f"created user {username} with role {role_name}")
    return jsonify({"id": user.id, "username": user.username, "role": role_name}), 201

@bp.route("/users", methods=["GET"])
@role_required(["admin", "manager"])
def list_users():
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "username": u.username,
        "role": u.role.name,
        "created_at": u.created_at.isoformat()
    } for u in users])

@bp.route("/users/<int:user_id>", methods=["DELETE"])
@role_required(["admin"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    log_db_action("delete_user", f"deleted user {username}")
    return jsonify({"msg": "deleted"})

# ==================== CUSTOMERS ====================
@bp.route("/customers", methods=["POST"])
@role_required(["admin", "manager"])
def create_customer():
    data = request.json
    customer = Customer(
        name=data.get("name"),
        email=data.get("email"),
        phone=data.get("phone"),
        address=data.get("address")
    )
    db.session.add(customer)
    db.session.commit()
    log_db_action("create_customer", f"customer_id={customer.id}, name={customer.name}")
    return jsonify({"id": customer.id, "name": customer.name}), 201

@bp.route("/customers", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def list_customers():
    customers = Customer.query.all()
    return jsonify([{
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone,
        "address": c.address
    } for c in customers])

@bp.route("/customers/<int:cid>", methods=["PUT"])
@role_required(["admin", "manager"])
def update_customer(cid):
    customer = Customer.query.get_or_404(cid)
    data = request.json
    customer.name = data.get("name", customer.name)
    customer.email = data.get("email", customer.email)
    customer.phone = data.get("phone", customer.phone)
    customer.address = data.get("address", customer.address)
    db.session.commit()
    log_db_action("update_customer", f"customer_id={cid}")
    return jsonify({"msg": "updated"})

@bp.route("/customers/<int:cid>", methods=["DELETE"])
@role_required(["admin"])
def delete_customer(cid):
    customer = Customer.query.get_or_404(cid)
    db.session.delete(customer)
    db.session.commit()
    log_db_action("delete_customer", f"customer_id={cid}")
    return jsonify({"msg": "deleted"})

# ==================== PRODUCTS ====================
@bp.route("/products", methods=["POST"])
@role_required(["admin", "manager"])
def create_product():
    data = request.json
    product = Product(
        name=data.get("name"),
        description=data.get("description"),
        price=data.get("price"),
        stock=data.get("stock", 0),
        category=data.get("category")
    )
    db.session.add(product)
    db.session.commit()
    log_db_action("create_product", f"product_id={product.id}, name={product.name}")
    return jsonify({"id": product.id, "name": product.name}), 201

@bp.route("/products", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def list_products():
    products = Product.query.all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "stock": p.stock,
        "category": p.category
    } for p in products])

@bp.route("/products/<int:pid>", methods=["PUT"])
@role_required(["admin", "manager"])
def update_product(pid):
    product = Product.query.get_or_404(pid)
    data = request.json
    product.name = data.get("name", product.name)
    product.description = data.get("description", product.description)
    product.price = data.get("price", product.price)
    product.stock = data.get("stock", product.stock)
    product.category = data.get("category", product.category)
    db.session.commit()
    log_db_action("update_product", f"product_id={pid}")
    return jsonify({"msg": "updated"})

@bp.route("/products/<int:pid>", methods=["DELETE"])
@role_required(["admin"])
def delete_product(pid):
    product = Product.query.get_or_404(pid)
    db.session.delete(product)
    db.session.commit()
    log_db_action("delete_product", f"product_id={pid}")
    return jsonify({"msg": "deleted"})

# ==================== SALES ====================
@bp.route("/sales", methods=["POST"])
@role_required(["admin", "manager"])
def create_sale():
    data = request.json
    items_data = data.get("items", [])
    
    if not items_data:
        return jsonify({"msg": "No items in sale"}), 400
    
    # Calcular total y verificar stock
    total = 0
    for item in items_data:
        product = Product.query.get(item["product_id"])
        if not product:
            return jsonify({"msg": f"Product {item['product_id']} not found"}), 404
        if product.stock < item["quantity"]:
            return jsonify({"msg": f"Insufficient stock for {product.name}"}), 400
        total += product.price * item["quantity"]
    
    # Crear venta
    sale = Sale(
        customer_id=data.get("customer_id"),
        user_id=g.current_user["id"],
        total=total,
        payment_method=data.get("payment_method", "cash"),
        status="completed"
    )
    db.session.add(sale)
    db.session.flush()
    
    # Crear items y actualizar stock
    for item in items_data:
        product = Product.query.get(item["product_id"])
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            quantity=item["quantity"],
            unit_price=product.price,
            subtotal=product.price * item["quantity"]
        )
        product.stock -= item["quantity"]
        db.session.add(sale_item)
    
    db.session.commit()
    log_db_action("create_sale", f"sale_id={sale.id}, total=${total}")
    return jsonify({"id": sale.id, "total": total}), 201

@bp.route("/sales", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def list_sales():
    sales = Sale.query.order_by(Sale.created_at.desc()).all()
    return jsonify([{
        "id": s.id,
        "customer": s.customer.name if s.customer else "N/A",
        "user": s.user.username,
        "total": s.total,
        "payment_method": s.payment_method,
        "status": s.status,
        "created_at": s.created_at.isoformat()
    } for s in sales])

@bp.route("/sales/<int:sid>", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def get_sale(sid):
    sale = Sale.query.get_or_404(sid)
    return jsonify({
        "id": sale.id,
        "customer": sale.customer.name if sale.customer else "N/A",
        "user": sale.user.username,
        "total": sale.total,
        "payment_method": sale.payment_method,
        "status": sale.status,
        "created_at": sale.created_at.isoformat(),
        "items": [{
            "product": item.product.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "subtotal": item.subtotal
        } for item in sale.items]
    })

@bp.route("/sales/<int:sid>", methods=["DELETE"])
@role_required(["admin"])
def delete_sale(sid):
    sale = Sale.query.get_or_404(sid)
    # Restaurar stock
    for item in sale.items:
        product = Product.query.get(item.product_id)
        if product:
            product.stock += item.quantity
    db.session.delete(sale)
    db.session.commit()
    log_db_action("delete_sale", f"sale_id={sid}")
    return jsonify({"msg": "deleted"})

# ==================== LOGS ====================
@bp.route("/logs", methods=["GET"])
@role_required(["admin", "manager"])
def list_logs():
    logs = LogEntry.query.order_by(LogEntry.timestamp.desc()).limit(100).all()
    return jsonify([{
        "id": l.id,
        "username": l.username,
        "action": l.action,
        "details": l.details,
        "timestamp": l.timestamp.isoformat()
    } for l in logs])

# ==================== DASHBOARD ====================
@bp.route("/dashboard", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def dashboard():
    total_sales = db.session.query(db.func.sum(Sale.total)).scalar() or 0
    total_products = Product.query.count()
    total_customers = Customer.query.count()
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()
    
    return jsonify({
        "total_sales": total_sales,
        "total_products": total_products,
        "total_customers": total_customers,
        "recent_sales": [{
            "id": s.id,
            "total": s.total,
            "created_at": s.created_at.isoformat()
        } for s in recent_sales]
    })