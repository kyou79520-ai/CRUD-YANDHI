from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    role = db.relationship("Role", backref="users")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Customer(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    contact_name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)  # Precio sin IVA
    stock = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=10)
    category = db.Column(db.String(100))
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"))
    include_iva = db.Column(db.Boolean, default=True)  # NUEVO: Si incluye IVA
    iva_rate = db.Column(db.Float, default=16.0)  # NUEVO: Tasa de IVA (16%)
    supplier = db.relationship("Supplier", backref="products")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_low_stock(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock <= self.min_stock
    
    @property
    def price_with_iva(self):
        """Calcula el precio con IVA incluido"""
        if self.include_iva:
            return self.price * (1 + self.iva_rate / 100)
        return self.price
    
    @property
    def iva_amount(self):
        """Calcula el monto de IVA"""
        if self.include_iva:
            return self.price * (self.iva_rate / 100)
        return 0

class Sale(db.Model):
    __tablename__ = "sales"
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subtotal = db.Column(db.Float, nullable=False)  # NUEVO: Subtotal sin IVA
    iva = db.Column(db.Float, default=0)  # NUEVO: Monto de IVA
    total = db.Column(db.Float, nullable=False)  # Total con IVA
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(50), default="completed")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    customer = db.relationship("Customer", backref="sales")
    user = db.relationship("User", backref="sales")

class SaleItem(db.Model):
    __tablename__ = "sale_items"
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)  # Precio unitario sin IVA
    iva_amount = db.Column(db.Float, default=0)  # NUEVO: Monto de IVA del item
    subtotal = db.Column(db.Float, nullable=False)  # Subtotal del item con IVA
    
    sale = db.relationship("Sale", backref="items")
    product = db.relationship("Product", backref="sale_items")

class LogEntry(db.Model):
    __tablename__ = "logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    username = db.Column(db.String(80))
    action = db.Column(db.String(255))
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)