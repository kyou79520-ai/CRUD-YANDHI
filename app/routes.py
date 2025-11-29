from flask import Blueprint, request, jsonify, current_app, g
from . import db
from .models import User, Role, Customer, Product, Sale, SaleItem, LogEntry, Supplier
from .utils import role_required, log_db_action
from .auth import bp as auth_bp
from datetime import datetime, timedelta
from sqlalchemy import func, desc

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
    # Obtener parámetros de búsqueda
    search = request.args.get('search', '')
    
    query = Customer.query
    
    if search:
        query = query.filter(
            (Customer.name.ilike(f'%{search}%')) |
            (Customer.email.ilike(f'%{search}%')) |
            (Customer.phone.ilike(f'%{search}%'))
        )
    
    customers = query.all()
    return jsonify([{
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone,
        "address": c.address,
        "total_purchases": sum(s.total for s in c.sales),
        "purchase_count": len(c.sales)
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

# ==================== SUPPLIERS ====================
@bp.route("/suppliers", methods=["POST"])
@role_required(["admin", "manager"])
def create_supplier():
    data = request.json
    supplier = Supplier(
        name=data.get("name"),
        contact_name=data.get("contact_name"),
        email=data.get("email"),
        phone=data.get("phone"),
        address=data.get("address")
    )
    db.session.add(supplier)
    db.session.commit()
    log_db_action("create_supplier", f"supplier_id={supplier.id}, name={supplier.name}")
    return jsonify({"id": supplier.id, "name": supplier.name}), 201

@bp.route("/suppliers", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def list_suppliers():
    search = request.args.get('search', '')
    
    query = Supplier.query
    
    if search:
        query = query.filter(
            (Supplier.name.ilike(f'%{search}%')) |
            (Supplier.contact_name.ilike(f'%{search}%')) |
            (Supplier.email.ilike(f'%{search}%'))
        )
    
    suppliers = query.all()
    return jsonify([{
        "id": s.id,
        "name": s.name,
        "contact_name": s.contact_name,
        "email": s.email,
        "phone": s.phone,
        "address": s.address,
        "product_count": len(s.products)
    } for s in suppliers])

@bp.route("/suppliers/<int:sid>/products", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def list_supplier_products(sid):
    """Obtener todos los productos de un proveedor específico"""
    supplier = Supplier.query.get_or_404(sid)
    products = Product.query.filter_by(supplier_id=sid).all()
    
    return jsonify({
        "supplier": {
            "id": supplier.id,
            "name": supplier.name,
            "contact_name": supplier.contact_name
        },
        "products": [{
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "price": p.price,
            "price_with_iva": p.price_with_iva,
            "stock": p.stock,
            "min_stock": p.min_stock,
            "is_low_stock": p.is_low_stock
        } for p in products]
    })

@bp.route("/suppliers/<int:sid>", methods=["PUT"])
@role_required(["admin", "manager"])
def update_supplier(sid):
    supplier = Supplier.query.get_or_404(sid)
    data = request.json
    supplier.name = data.get("name", supplier.name)
    supplier.contact_name = data.get("contact_name", supplier.contact_name)
    supplier.email = data.get("email", supplier.email)
    supplier.phone = data.get("phone", supplier.phone)
    supplier.address = data.get("address", supplier.address)
    db.session.commit()
    log_db_action("update_supplier", f"supplier_id={sid}")
    return jsonify({"msg": "updated"})

@bp.route("/suppliers/<int:sid>", methods=["DELETE"])
@role_required(["admin"])
def delete_supplier(sid):
    supplier = Supplier.query.get_or_404(sid)
    db.session.delete(supplier)
    db.session.commit()
    log_db_action("delete_supplier", f"supplier_id={sid}")
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
        min_stock=data.get("min_stock", 10),
        category=data.get("category"),
        supplier_id=data.get("supplier_id"),
        include_iva=data.get("include_iva", True),
        iva_rate=data.get("iva_rate", 16.0)
    )
    db.session.add(product)
    db.session.commit()
    log_db_action("create_product", f"product_id={product.id}, name={product.name}")
    return jsonify({"id": product.id, "name": product.name}), 201

@bp.route("/products", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def list_products():
    # Filtros de búsqueda
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    supplier_id = request.args.get('supplier_id', '')
    low_stock = request.args.get('low_stock', '')
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    
    if category:
        query = query.filter_by(category=category)
    
    if supplier_id:
        query = query.filter_by(supplier_id=int(supplier_id))
    
    if low_stock == 'true':
        query = query.filter(Product.stock <= Product.min_stock)
    
    products = query.all()
    return jsonify([{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "price": p.price,
        "price_with_iva": p.price_with_iva,
        "iva_amount": p.iva_amount,
        "include_iva": p.include_iva,
        "iva_rate": p.iva_rate,
        "stock": p.stock,
        "min_stock": p.min_stock,
        "category": p.category,
        "supplier_id": p.supplier_id,
        "supplier_name": p.supplier.name if p.supplier else None,
        "is_low_stock": p.is_low_stock
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
    product.min_stock = data.get("min_stock", product.min_stock)
    product.category = data.get("category", product.category)
    product.supplier_id = data.get("supplier_id", product.supplier_id)
    product.include_iva = data.get("include_iva", product.include_iva)
    product.iva_rate = data.get("iva_rate", product.iva_rate)
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
    
    # Calcular subtotal, IVA y total
    subtotal = 0
    total_iva = 0
    
    for item in items_data:
        product = Product.query.get(item["product_id"])
        if not product:
            return jsonify({"msg": f"Product {item['product_id']} not found"}), 404
        if product.stock < item["quantity"]:
            return jsonify({"msg": f"Insufficient stock for {product.name}"}), 400
        
        item_subtotal = product.price * item["quantity"]
        item_iva = product.iva_amount * item["quantity"]
        
        subtotal += item_subtotal
        total_iva += item_iva
    
    total = subtotal + total_iva
    
    # Crear venta
    sale = Sale(
        customer_id=data.get("customer_id"),
        user_id=g.current_user["id"],
        subtotal=subtotal,
        iva=total_iva,
        total=total,
        payment_method=data.get("payment_method", "cash"),
        status="completed"
    )
    db.session.add(sale)
    db.session.flush()
    
    # Crear items y actualizar stock
    for item in items_data:
        product = Product.query.get(item["product_id"])
        item_iva = product.iva_amount * item["quantity"]
        item_subtotal = (product.price * item["quantity"]) + item_iva
        
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=product.id,
            quantity=item["quantity"],
            unit_price=product.price,
            iva_amount=item_iva,
            subtotal=item_subtotal
        )
        product.stock -= item["quantity"]
        db.session.add(sale_item)
    
    db.session.commit()
    log_db_action("create_sale", f"sale_id={sale.id}, total=${total:.2f}")
    return jsonify({
        "id": sale.id,
        "subtotal": subtotal,
        "iva": total_iva,
        "total": total
    }), 201

@bp.route("/sales", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def list_sales():
    # Filtros de consulta
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    customer_id = request.args.get('customer_id', '')
    user_id = request.args.get('user_id', '')
    payment_method = request.args.get('payment_method', '')
    
    query = Sale.query
    
    if start_date:
        query = query.filter(Sale.created_at >= datetime.fromisoformat(start_date))
    
    if end_date:
        query = query.filter(Sale.created_at <= datetime.fromisoformat(end_date))
    
    if customer_id:
        query = query.filter_by(customer_id=int(customer_id))
    
    if user_id:
        query = query.filter_by(user_id=int(user_id))
    
    if payment_method:
        query = query.filter_by(payment_method=payment_method)
    
    sales = query.order_by(Sale.created_at.desc()).all()
    
    return jsonify([{
        "id": s.id,
        "customer": s.customer.name if s.customer else "N/A",
        "user": s.user.username,
        "subtotal": s.subtotal,
        "iva": s.iva,
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
        "subtotal": sale.subtotal,
        "iva": sale.iva,
        "total": sale.total,
        "payment_method": sale.payment_method,
        "status": sale.status,
        "created_at": sale.created_at.isoformat(),
        "items": [{
            "product": item.product.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "iva_amount": item.iva_amount,
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

# ==================== REPORTS / CONSULTAS ====================
@bp.route("/reports/sales-summary", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def sales_summary():
    """Resumen de ventas por período"""
    period = request.args.get('period', 'today')  # today, week, month, year
    
    now = datetime.now()
    
    if period == 'today':
        start_date = now.replace(hour=0, minute=0, second=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)
    
    sales = Sale.query.filter(Sale.created_at >= start_date).all()
    
    total_sales = sum(s.total for s in sales)
    total_iva = sum(s.iva for s in sales)
    count = len(sales)
    
    return jsonify({
        "period": period,
        "total_sales": total_sales,
        "total_iva": total_iva,
        "count": count,
        "average": total_sales / count if count > 0 else 0
    })

@bp.route("/reports/top-products", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def top_products():
    """Productos más vendidos"""
    limit = request.args.get('limit', 10, type=int)
    
    top = db.session.query(
        Product.name,
        func.sum(SaleItem.quantity).label('total_sold'),
        func.sum(SaleItem.subtotal).label('total_revenue')
    ).join(SaleItem).group_by(Product.id, Product.name)\
     .order_by(desc('total_sold')).limit(limit).all()
    
    return jsonify([{
        "product": row[0],
        "quantity_sold": row[1],
        "revenue": row[2]
    } for row in top])

@bp.route("/reports/top-customers", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def top_customers():
    """Clientes frecuentes"""
    limit = request.args.get('limit', 10, type=int)
    
    top = db.session.query(
        Customer.name,
        func.count(Sale.id).label('purchase_count'),
        func.sum(Sale.total).label('total_spent')
    ).join(Sale).group_by(Customer.id, Customer.name)\
     .order_by(desc('total_spent')).limit(limit).all()
    
    return jsonify([{
        "customer": row[0],
        "purchases": row[1],
        "total_spent": row[2]
    } for row in top])

# ==================== LOGS ====================
@bp.route("/logs", methods=["GET"])
@role_required(["admin", "manager"])
def list_logs():
    search = request.args.get('search', '')
    action = request.args.get('action', '')
    
    query = LogEntry.query
    
    if search:
        query = query.filter(
            (LogEntry.username.ilike(f'%{search}%')) |
            (LogEntry.details.ilike(f'%{search}%'))
        )
    
    if action:
        query = query.filter(LogEntry.action.ilike(f'%{action}%'))
    
    logs = query.order_by(LogEntry.timestamp.desc()).limit(100).all()
    
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
    total_sales = db.session.query(func.sum(Sale.total)).scalar() or 0
    total_products = Product.query.count()
    total_customers = Customer.query.count()
    total_suppliers = Supplier.query.count()
    low_stock_products = Product.query.filter(Product.stock <= Product.min_stock).count()
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()
    
    # Ventas de hoy
    today = datetime.now().replace(hour=0, minute=0, second=0)
    today_sales = db.session.query(func.sum(Sale.total)).filter(Sale.created_at >= today).scalar() or 0
    
    return jsonify({
        "total_sales": total_sales,
        "today_sales": today_sales,
        "total_products": total_products,
        "total_customers": total_customers,
        "total_suppliers": total_suppliers,
        "low_stock_products": low_stock_products,
        "recent_sales": [{
            "id": s.id,
            "total": s.total,
            "created_at": s.created_at.isoformat()
        } for s in recent_sales]
    })