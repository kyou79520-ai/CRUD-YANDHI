from flask import Blueprint, request, jsonify, current_app, g
from . import db
from .utils import role_required, log_db_action
from .auth import bp as auth_bp
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from .models import User, Role, Customer, Product, Sale, SaleItem, LogEntry, Supplier, SupplierProduct

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
        "total_purchases": sum(s.total for s in c.sales) if hasattr(c, 'sales') else 0,
        "purchase_count": len(c.sales) if hasattr(c, 'sales') else 0
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
        "product_count": len(s.products) if hasattr(s, 'products') else 0
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
            "min_stock": getattr(p, 'min_stock', 10),
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
    
    try:
        # Obtener IVA (puede venir como iva o iva_rate)
        iva = data.get("iva", data.get("iva_rate", 16))
        
        product = Product(
            name=data.get("name"),
            description=data.get("description"),
            price=data.get("price"),
            iva=iva,
            stock=data.get("stock", 0),
            min_stock=data.get("min_stock", 10),
            category=data.get("category"),
            supplier_id=data.get("supplier_id")
        )
        db.session.add(product)
        db.session.commit()
        log_db_action("create_product", f"product_id={product.id}, name={product.name}")
        return jsonify({"id": product.id, "name": product.name}), 201
    except Exception as e:
        current_app.logger.error(f"Error creating product: {str(e)}")
        db.session.rollback()
        return jsonify({"msg": f"Error creating product: {str(e)}"}), 500

@bp.route("/products", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def list_products():
    try:
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
        result = []
        
        for p in products:
            try:
                # Obtener IVA de forma segura (puede ser iva, iva_rate, o default 16)
                iva = 16
                if hasattr(p, 'iva') and p.iva:
                    iva = p.iva
                elif hasattr(p, 'iva_rate') and p.iva_rate:
                    iva = p.iva_rate
                
                # Calcular precio con IVA
                price_with_iva = p.price * (1 + iva / 100)
                
                # Obtener nombre del proveedor
                supplier_name = None
                if p.supplier_id and hasattr(p, 'supplier') and p.supplier:
                    supplier_name = p.supplier.name
                
                # Construir diccionario del producto
                product_data = {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price": p.price,
                    "price_with_iva": price_with_iva,
                    "iva": iva,  # Solo devolver el porcentaje de IVA
                    "stock": p.stock,
                    "min_stock": getattr(p, 'min_stock', 10),
                    "category": p.category,
                    "supplier_id": p.supplier_id,
                    "supplier_name": supplier_name,
                    "is_low_stock": p.stock <= getattr(p, 'min_stock', 10)
                }
                
                result.append(product_data)
            except Exception as e:
                current_app.logger.error(f"Error processing product {p.id}: {str(e)}")
                # Agregar producto con datos mínimos
                result.append({
                    "id": p.id,
                    "name": p.name,
                    "description": p.description or "",
                    "price": p.price,
                    "price_with_iva": p.price * 1.16,
                    "iva": 16,
                    "stock": p.stock,
                    "min_stock": 10,
                    "category": p.category or "",
                    "supplier_id": None,
                    "supplier_name": "Error",
                    "is_low_stock": False
                })
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error in list_products: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"msg": f"Error loading products: {str(e)}"}), 500

@bp.route("/products/<int:pid>", methods=["PUT"])
@role_required(["admin", "manager"])
def update_product(pid):
    try:
        product = Product.query.get_or_404(pid)
        data = request.json
        
        product.name = data.get("name", product.name)
        product.description = data.get("description", product.description)
        product.price = data.get("price", product.price)
        product.stock = data.get("stock", product.stock)
        
        # Actualizar min_stock de forma segura
        if "min_stock" in data:
            product.min_stock = data.get("min_stock")
        elif not hasattr(product, 'min_stock') or product.min_stock is None:
            product.min_stock = 10
        
        product.category = data.get("category", product.category)
        product.supplier_id = data.get("supplier_id", product.supplier_id)
        
        # Actualizar IVA (puede venir como iva o iva_rate)
        if "iva" in data:
            product.iva = data.get("iva")
        elif "iva_rate" in data:
            if hasattr(product, 'iva'):
                product.iva = data.get("iva_rate")
            elif hasattr(product, 'iva_rate'):
                product.iva_rate = data.get("iva_rate")
        
        db.session.commit()
        log_db_action("update_product", f"product_id={pid}")
        return jsonify({"msg": "updated"})
    except Exception as e:
        current_app.logger.error(f"Error updating product {pid}: {str(e)}")
        db.session.rollback()
        return jsonify({"msg": f"Error updating product: {str(e)}"}), 500

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
    try:
        data = request.get_json() or {}
        items_data = data.get("items") or []

        if not items_data:
            return jsonify({"msg": "No items in sale"}), 400

        subtotal = 0.0
        total_iva = 0.0

        # --- Validar items y calcular totales ---
        for item in items_data:
            product_id = item.get("product_id")
            quantity = item.get("quantity")

            if not product_id or not isinstance(quantity, (int, float)) or quantity <= 0:
                return jsonify({"msg": "Invalid item data"}), 400

            product = Product.query.get(product_id)
            if not product:
                return jsonify({"msg": f"Product {product_id} not found"}), 404

            if product.stock < quantity:
                return jsonify({"msg": f"Insufficient stock for {product.name}"}), 400

            # IVA seguro (si product.iva es None, usa 16 por defecto)
            iva_attr = getattr(product, "iva", None)
            if iva_attr is None:
                iva_attr = getattr(product, "iva_rate", 16)
            iva_rate = iva_attr if isinstance(iva_attr, (int, float)) else 16

            line_subtotal = product.price * quantity
            line_iva = line_subtotal * (iva_rate / 100.0)

            subtotal += line_subtotal
            total_iva += line_iva

        total = subtotal + total_iva

        # --- Obtener user_id desde g.current_user ---
        user_id = None
        if hasattr(g, "current_user") and g.current_user:
            cu = g.current_user
            if isinstance(cu, dict):
                user_id = cu.get("id")
            else:
                user_id = getattr(cu, "id", None)

        if not user_id:
            return jsonify({"msg": "User not found in context"}), 401

        # --- Crear venta (sin pasar kwargs que no existan en el modelo) ---
        sale = Sale(
            customer_id=data.get("customer_id"),
            user_id=user_id,
            total=total,
            payment_method=data.get("payment_method", "cash"),
            status="completed"
        )

        # Asignar subtotal / iva solo si esas columnas existen en la tabla
        if hasattr(Sale, "subtotal"):
            sale.subtotal = subtotal
        if hasattr(Sale, "iva"):
            sale.iva = total_iva

        db.session.add(sale)
        db.session.flush()  # para obtener sale.id

        # --- Crear items y actualizar stock ---
        for item in items_data:
            product = Product.query.get(item["product_id"])
            quantity = item["quantity"]

            iva_attr = getattr(product, "iva", None)
            if iva_attr is None:
                iva_attr = getattr(product, "iva_rate", 16)
            iva_rate = iva_attr if isinstance(iva_attr, (int, float)) else 16

            line_subtotal = product.price * quantity
            line_iva = line_subtotal * (iva_rate / 100.0)
            line_total = line_subtotal + line_iva

            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price,
                subtotal=line_total
            )

            # Guardar el IVA por item solo si la columna existe
            if hasattr(SaleItem, "iva_amount"):
                sale_item.iva_amount = line_iva

            product.stock -= quantity
            db.session.add(sale_item)

        db.session.commit()
        log_db_action("create_sale", f"sale_id={sale.id}, total=${total:.2f}")

        return jsonify({
            "id": sale.id,
            "subtotal": subtotal,
            "iva": total_iva,
            "total": total
        }), 201

    except Exception as e:
        current_app.logger.exception("Error creating sale")
        db.session.rollback()
        # Muy útil para debug en el front
        return jsonify({"msg": "Error creating sale", "error": str(e)}), 500


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
        "subtotal": getattr(s, 'subtotal', None),
        "iva": getattr(s, 'iva', None),
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
        "subtotal": getattr(sale, 'subtotal', None),
        "iva": getattr(sale, 'iva', None),
        "total": sale.total,
        "payment_method": sale.payment_method,
        "status": sale.status,
        "created_at": sale.created_at.isoformat(),
        "items": [{
            "product": item.product.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "iva_amount": getattr(item, 'iva_amount', None),
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
    period = request.args.get('period', 'today')
    
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
    total_iva = sum(getattr(s, 'iva', 0) for s in sales)
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

# ==================== SUPPLIER PRODUCTS (AGREGAR AL FINAL) ====================


@bp.route("/suppliers/<int:sid>/products-catalog", methods=["GET"])
@role_required(["admin", "manager", "viewer"])
def list_supplier_products_catalog(sid):
    """Obtener todos los productos que vende un proveedor (catálogo del proveedor)"""
    supplier = Supplier.query.get_or_404(sid)
    supplier_products = SupplierProduct.query.filter_by(supplier_id=sid).all()
    
    return jsonify({
        "supplier": {
            "id": supplier.id,
            "name": supplier.name,
            "contact_name": supplier.contact_name
        },
        "products": [{
            "id": sp.id,
            "product_id": sp.product_id,
            "product_name": sp.product.name,
            "product_category": sp.product.category,
            "purchase_price": sp.purchase_price,
            "sale_price": sp.product.price,
            "quantity_available": sp.quantity_available,
            "profit_margin": sp.profit_margin,
            "profit_percentage": sp.profit_percentage,
            "last_updated": sp.last_updated.isoformat()
        } for sp in supplier_products]
    })

@bp.route("/suppliers/<int:sid>/products-catalog", methods=["POST"])
@role_required(["admin", "manager"])
def add_product_to_supplier(sid):
    """Agregar un producto que vende el proveedor"""
    supplier = Supplier.query.get_or_404(sid)
    data = request.json
    
    product_id = data.get("product_id")
    purchase_price = data.get("purchase_price")
    quantity_available = data.get("quantity_available", 0)
    
    if not product_id or purchase_price is None:
        return jsonify({"msg": "product_id and purchase_price required"}), 400
    
    product = Product.query.get_or_404(product_id)
    
    # Verificar si ya existe la relación
    existing = SupplierProduct.query.filter_by(
        supplier_id=sid, 
        product_id=product_id
    ).first()
    
    if existing:
        return jsonify({"msg": "Product already assigned to this supplier"}), 400
    
    supplier_product = SupplierProduct(
        supplier_id=sid,
        product_id=product_id,
        purchase_price=float(purchase_price),
        quantity_available=int(quantity_available)
    )
    
    db.session.add(supplier_product)
    db.session.commit()
    
    log_db_action("add_supplier_product", 
                  f"supplier_id={sid}, product_id={product_id}, price={purchase_price}")
    
    return jsonify({
        "id": supplier_product.id,
        "product_name": product.name,
        "purchase_price": supplier_product.purchase_price
    }), 201

@bp.route("/suppliers/<int:sid>/products-catalog/<int:sp_id>", methods=["PUT"])
@role_required(["admin", "manager"])
def update_supplier_product(sid, sp_id):
    """Actualizar precio y cantidad de un producto del proveedor"""
    supplier_product = SupplierProduct.query.get_or_404(sp_id)
    
    if supplier_product.supplier_id != sid:
        return jsonify({"msg": "Product does not belong to this supplier"}), 400
    
    data = request.json
    
    if "purchase_price" in data:
        supplier_product.purchase_price = float(data["purchase_price"])
    
    if "quantity_available" in data:
        supplier_product.quantity_available = int(data["quantity_available"])
    
    db.session.commit()
    log_db_action("update_supplier_product", f"sp_id={sp_id}")
    
    return jsonify({"msg": "updated"})

@bp.route("/suppliers/<int:sid>/products-catalog/<int:sp_id>", methods=["DELETE"])
@role_required(["admin"])
def delete_supplier_product(sid, sp_id):
    """Eliminar un producto de la lista del proveedor"""
    supplier_product = SupplierProduct.query.get_or_404(sp_id)
    
    if supplier_product.supplier_id != sid:
        return jsonify({"msg": "Product does not belong to this supplier"}), 400
    
    db.session.delete(supplier_product)
    db.session.commit()
    log_db_action("delete_supplier_product", f"sp_id={sp_id}")
    
    return jsonify({"msg": "deleted"})