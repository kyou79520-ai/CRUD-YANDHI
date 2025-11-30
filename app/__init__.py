from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from sqlalchemy import text
from .config import Config
from .logger import setup_app_logger

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def migrate_database(app):
    """Ejecuta migraciones necesarias en la base de datos"""
    with app.app_context():
        try:
            # Verificar si las columnas existen
            inspector = db.inspect(db.engine)
            existing_columns = [col['name'] for col in inspector.get_columns('products')]
            
            print(f"📋 Columnas existentes en products: {existing_columns}")
            
            # Agregar min_stock si no existe
            if 'min_stock' not in existing_columns:
                print("➕ Agregando columna 'min_stock' a products...")
                db.session.execute(text(
                    "ALTER TABLE products ADD COLUMN min_stock INTEGER DEFAULT 10"
                ))
                db.session.commit()
                print("✅ Columna 'min_stock' agregada")
            else:
                print("ℹ️  Columna 'min_stock' ya existe")
            
            # Verificar si existe iva_rate (viejo) o iva (nuevo)
            if 'iva' not in existing_columns and 'iva_rate' not in existing_columns:
                print("➕ Agregando columna 'iva' a products...")
                db.session.execute(text(
                    "ALTER TABLE products ADD COLUMN iva INTEGER DEFAULT 16"
                ))
                db.session.commit()
                print("✅ Columna 'iva' agregada con valor por defecto de 16%")
            elif 'iva_rate' in existing_columns and 'iva' not in existing_columns:
                # Renombrar iva_rate a iva para consistencia
                print("➕ Renombrando columna 'iva_rate' a 'iva'...")
                db.session.execute(text(
                    "ALTER TABLE products RENAME COLUMN iva_rate TO iva"
                ))
                db.session.commit()
                print("✅ Columna renombrada de 'iva_rate' a 'iva'")
            else:
                print("ℹ️  Columna 'iva' ya existe")
            
            # Eliminar columna include_iva si existe (ya no la necesitamos)
            if 'include_iva' in existing_columns:
                print("🗑️  Eliminando columna obsoleta 'include_iva'...")
                try:
                    db.session.execute(text(
                        "ALTER TABLE products DROP COLUMN include_iva"
                    ))
                    db.session.commit()
                    print("✅ Columna 'include_iva' eliminada")
                except Exception as e:
                    print(f"⚠️  No se pudo eliminar 'include_iva': {e}")
                    db.session.rollback()
            
            # Agregar supplier_id si no existe
            if 'supplier_id' not in existing_columns:
                print("➕ Agregando columna 'supplier_id' a products...")
                db.session.execute(text(
                    "ALTER TABLE products ADD COLUMN supplier_id INTEGER"
                ))
                db.session.commit()
                print("✅ Columna 'supplier_id' agregada")
                
                # Intentar agregar foreign key
                try:
                    db.session.execute(text(
                        "ALTER TABLE products ADD CONSTRAINT fk_products_supplier "
                        "FOREIGN KEY (supplier_id) REFERENCES suppliers(id)"
                    ))
                    db.session.commit()
                    print("✅ Foreign key constraint agregada")
                except Exception as e:
                    print(f"ℹ️  Foreign key ya existe o no se pudo agregar: {e}")
                    db.session.rollback()
            else:
                print("ℹ️  Columna 'supplier_id' ya existe")
            
            # Actualizar productos existentes sin proveedor asignándoles el primer proveedor disponible
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM products WHERE supplier_id IS NULL"
            ))
            null_supplier_count = result.scalar()
            
            if null_supplier_count > 0:
                print(f"⚠️  Hay {null_supplier_count} productos sin proveedor")
                # Obtener el primer proveedor
                result = db.session.execute(text("SELECT id FROM suppliers LIMIT 1"))
                first_supplier = result.scalar()
                
                if first_supplier:
                    print(f"➕ Asignando proveedor por defecto (ID: {first_supplier}) a productos sin proveedor...")
                    db.session.execute(text(
                        f"UPDATE products SET supplier_id = {first_supplier} WHERE supplier_id IS NULL"
                    ))
                    db.session.commit()
                    print("✅ Productos actualizados con proveedor por defecto")
                else:
                    print("⚠️  No hay proveedores disponibles. Crea al menos un proveedor antes de agregar productos.")
            else:
                print("✅ Todos los productos tienen proveedor asignado")
                    
        except Exception as e:
            print(f"⚠️  Error en migración: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    setup_app_logger(app)
    
    # Importar TODOS los modelos
    from .models import User, Role, LogEntry, Customer, Product, Sale, SaleItem, Supplier
    
    # Crear tablas y datos iniciales automáticamente
    with app.app_context():
        try:
            # Primero crear todas las tablas
            db.create_all()
            print("✅ Tablas de base de datos verificadas/creadas")
            
            # Ejecutar migraciones si es necesario
            migrate_database(app)
            
            # Crear roles si no existen
            roles_needed = ['admin', 'manager', 'viewer']
            for role_name in roles_needed:
                if not Role.query.filter_by(name=role_name).first():
                    role = Role(name=role_name)
                    db.session.add(role)
            db.session.commit()
            print("✅ Roles verificados: admin, manager, viewer")
            
            # Crear usuario admin si no existe
            if not User.query.filter_by(username='admin').first():
                admin_role = Role.query.filter_by(name='admin').first()
                admin_user = User(username='admin', role=admin_role)
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Usuario admin creado (username: admin, password: admin123)")
            else:
                print("ℹ️  Usuario admin ya existe")
            
            # Crear usuario manager si no existe
            if not User.query.filter_by(username='manager').first():
                manager_role = Role.query.filter_by(name='manager').first()
                manager_user = User(username='manager', role=manager_role)
                manager_user.set_password('manager123')
                db.session.add(manager_user)
                db.session.commit()
                print("✅ Usuario manager creado (username: manager, password: manager123)")
            else:
                print("ℹ️  Usuario manager ya existe")
            
            # Crear usuario viewer si no existe
            if not User.query.filter_by(username='viewer').first():
                viewer_role = Role.query.filter_by(name='viewer').first()
                viewer_user = User(username='viewer', role=viewer_role)
                viewer_user.set_password('viewer123')
                db.session.add(viewer_user)
                db.session.commit()
                print("✅ Usuario viewer creado (username: viewer, password: viewer123)")
            else:
                print("ℹ️  Usuario viewer ya existe")
            
            # Agregar proveedores de ejemplo si no existen
            if Supplier.query.count() == 0:
                proveedores = [
                    Supplier(name="Cervecería Modelo", contact_name="Juan Pérez", 
                            email="contacto@modelo.com", phone="5551234567", 
                            address="CDMX, México"),
                    Supplier(name="Grupo Heineken México", contact_name="María García", 
                            email="ventas@heineken.mx", phone="5552345678", 
                            address="Monterrey, México"),
                    Supplier(name="Vinos L.A. Cetto", contact_name="Carlos López", 
                            email="info@lacetto.com", phone="5553456789", 
                            address="Baja California, México"),
                    Supplier(name="Casa Cuervo", contact_name="Ana Martínez", 
                            email="contacto@cuervo.com", phone="5554567890", 
                            address="Jalisco, México"),
                    Supplier(name="Distribuidora de Licores Nacional", contact_name="Roberto Sánchez", 
                            email="ventas@licoresnacional.com", phone="5555678901", 
                            address="Guadalajara, México")
                ]
                for prov in proveedores:
                    db.session.add(prov)
                db.session.commit()
                print(f"✅ {len(proveedores)} proveedores de ejemplo agregados")
            
            # Agregar productos de licorería si no existen
            if Product.query.count() == 0:
                # Obtener proveedores
                modelo = Supplier.query.filter_by(name="Cervecería Modelo").first()
                heineken = Supplier.query.filter_by(name="Grupo Heineken México").first()
                cetto = Supplier.query.filter_by(name="Vinos L.A. Cetto").first()
                cuervo = Supplier.query.filter_by(name="Casa Cuervo").first()
                distribuidor = Supplier.query.filter_by(name="Distribuidora de Licores Nacional").first()
                
                productos = [
                    # Cervezas
                    Product(name="Corona Extra 355ml", description="Cerveza clara mexicana", 
                           price=25.00, iva=16, stock=120, min_stock=50, category="Cervezas", supplier=modelo),
                    Product(name="Modelo Especial 355ml", description="Cerveza tipo pilsner", 
                           price=23.00, iva=16, stock=100, min_stock=50, category="Cervezas", supplier=modelo),
                    Product(name="Victoria 355ml", description="Cerveza tipo viena", 
                           price=22.00, iva=16, stock=90, min_stock=40, category="Cervezas", supplier=modelo),
                    Product(name="Heineken 355ml", description="Cerveza importada", 
                           price=30.00, iva=16, stock=80, min_stock=40, category="Cervezas", supplier=heineken),
                    Product(name="Tecate Light 355ml", description="Cerveza light", 
                           price=20.00, iva=16, stock=110, min_stock=50, category="Cervezas", supplier=heineken),
                    
                    # Vinos
                    Product(name="Vino L.A. Cetto Tinto", description="Vino tinto 750ml", 
                           price=180.00, iva=16, stock=40, min_stock=15, category="Vinos", supplier=cetto),
                    Product(name="Vino L.A. Cetto Blanco", description="Vino blanco 750ml", 
                           price=180.00, iva=16, stock=35, min_stock=15, category="Vinos", supplier=cetto),
                    Product(name="Vino Santo Tomás Tinto", description="Vino tinto 750ml", 
                           price=220.00, iva=16, stock=30, min_stock=10, category="Vinos", supplier=cetto),
                    Product(name="Vino Casa Madero Rosado", description="Vino rosado 750ml", 
                           price=200.00, iva=16, stock=25, min_stock=10, category="Vinos", supplier=cetto),
                    
                    # Licores y Destilados
                    Product(name="Tequila José Cuervo Especial", description="Tequila reposado 750ml", 
                           price=280.00, iva=16, stock=50, min_stock=20, category="Tequilas", supplier=cuervo),
                    Product(name="Tequila Jimador Reposado", description="Tequila 100% agave 750ml", 
                           price=320.00, iva=16, stock=45, min_stock=20, category="Tequilas", supplier=cuervo),
                    Product(name="Tequila Herradura Blanco", description="Tequila blanco 750ml", 
                           price=450.00, iva=16, stock=30, min_stock=15, category="Tequilas", supplier=cuervo),
                    Product(name="Mezcal 400 Conejos", description="Mezcal joven 750ml", 
                           price=380.00, iva=16, stock=35, min_stock=15, category="Mezcales", supplier=distribuidor),
                    Product(name="Ron Bacardi Blanco", description="Ron blanco 750ml", 
                           price=250.00, iva=16, stock=40, min_stock=20, category="Rones", supplier=distribuidor),
                    Product(name="Vodka Absolut", description="Vodka premium 750ml", 
                           price=420.00, iva=16, stock=30, min_stock=15, category="Vodkas", supplier=distribuidor),
                    Product(name="Whisky Johnnie Walker Red", description="Whisky escocés 750ml", 
                           price=480.00, iva=16, stock=25, min_stock=10, category="Whiskys", supplier=distribuidor),
                    
                    # Aperitivos y Mezclas
                    Product(name="Squirt 600ml", description="Refresco de toronja", 
                           price=15.00, iva=16, stock=100, min_stock=30, category="Refrescos", supplier=distribuidor),
                    Product(name="Coca Cola 600ml", description="Refresco de cola", 
                           price=15.00, iva=16, stock=100, min_stock=30, category="Refrescos", supplier=distribuidor),
                    Product(name="Agua Mineral Topo Chico", description="Agua mineral 355ml", 
                           price=18.00, iva=16, stock=80, min_stock=25, category="Refrescos", supplier=distribuidor),
                    Product(name="Jugo Jumex Naranja 1L", description="Jugo de naranja", 
                           price=25.00, iva=16, stock=60, min_stock=20, category="Jugos", supplier=distribuidor),
                    
                    # Botanas
                    Product(name="Cacahuates Japoneses", description="Botana 150g", 
                           price=30.00, iva=16, stock=70, min_stock=30, category="Botanas", supplier=distribuidor),
                    Product(name="Papas Sabritas Original", description="Papas fritas 170g", 
                           price=35.00, iva=16, stock=60, min_stock=25, category="Botanas", supplier=distribuidor),
                    Product(name="Chicharrón Preparado", description="Botana 100g", 
                           price=25.00, iva=16, stock=50, min_stock=20, category="Botanas", supplier=distribuidor),
                    Product(name="Mix de Nueces", description="Mezcla de nueces 200g", 
                           price=55.00, iva=16, stock=40, min_stock=15, category="Botanas", supplier=distribuidor),
                    
                    # Cigarros
                    Product(name="Marlboro Rojo", description="Cajetilla 20 cigarros", 
                           price=75.00, iva=16, stock=100, min_stock=40, category="Cigarros", supplier=distribuidor),
                    Product(name="Camel Blue", description="Cajetilla 20 cigarros", 
                           price=70.00, iva=16, stock=80, min_stock=35, category="Cigarros", supplier=distribuidor),
                ]
                for p in productos:
                    db.session.add(p)
                db.session.commit()
                print(f"✅ {len(productos)} productos de licorería agregados")
            
            # Agregar clientes de ejemplo si no existen
            if Customer.query.count() == 0:
                clientes = [
                    Customer(name="Juan Pérez", email="juan@email.com", phone="5551234567", address="Calle Juárez #123, Centro"),
                    Customer(name="María García", email="maria@email.com", phone="5557654321", address="Av. Hidalgo #456, Col. Norte"),
                    Customer(name="Carlos López", email="carlos@email.com", phone="5559876543", address="Blvd. Morelos #789, Col. Sur"),
                    Customer(name="Ana Martínez", email="ana@email.com", phone="5552468135", address="Calle Allende #321, Centro"),
                    Customer(name="Roberto Sánchez", email="roberto@email.com", phone="5553691470", address="Av. Reforma #654, Col. Este")
                ]
                for c in clientes:
                    db.session.add(c)
                db.session.commit()
                print(f"✅ {len(clientes)} clientes de ejemplo agregados")
                
        except Exception as e:
            print(f"❌ Error al inicializar base de datos: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
    
    # Registrar blueprints
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp, url_prefix="/api")
    
    # Ruta principal - servir el frontend
    @app.route('/')
    def index():
        return send_from_directory(app.template_folder, 'index.html')
    
    return app