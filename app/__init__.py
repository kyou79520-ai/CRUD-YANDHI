from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from .config import Config
from .logger import setup_app_logger

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    setup_app_logger(app)
    
    # Importar TODOS los modelos
    from .models import User, Role, LogEntry, Customer, Product, Sale, SaleItem
    
    # Crear tablas y datos iniciales automáticamente
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tablas de base de datos verificadas/creadas")
            
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
                print("✅ Usuario admin ya existe")
            
            # Crear usuario manager si no existe
            if not User.query.filter_by(username='manager').first():
                manager_role = Role.query.filter_by(name='manager').first()
                manager_user = User(username='manager', role=manager_role)
                manager_user.set_password('manager123')
                db.session.add(manager_user)
                db.session.commit()
                print("✅ Usuario manager creado (username: manager, password: manager123)")
            
            # Crear usuario viewer si no existe
            if not User.query.filter_by(username='viewer').first():
                viewer_role = Role.query.filter_by(name='viewer').first()
                viewer_user = User(username='viewer', role=viewer_role)
                viewer_user.set_password('viewer123')
                db.session.add(viewer_user)
                db.session.commit()
                print("✅ Usuario viewer creado (username: viewer, password: viewer123)")
            
            # Agregar productos de licorería si no existen
            if Product.query.count() == 0:
                productos = [
                    # Cervezas
                    Product(name="Corona Extra 355ml", description="Cerveza clara mexicana", price=25.00, stock=120, category="Cervezas"),
                    Product(name="Modelo Especial 355ml", description="Cerveza tipo pilsner", price=23.00, stock=100, category="Cervezas"),
                    Product(name="Victoria 355ml", description="Cerveza tipo viena", price=22.00, stock=90, category="Cervezas"),
                    Product(name="Heineken 355ml", description="Cerveza importada", price=30.00, stock=80, category="Cervezas"),
                    Product(name="Tecate Light 355ml", description="Cerveza light", price=20.00, stock=110, category="Cervezas"),
                    
                    # Vinos
                    Product(name="Vino L.A. Cetto Tinto", description="Vino tinto 750ml", price=180.00, stock=40, category="Vinos"),
                    Product(name="Vino L.A. Cetto Blanco", description="Vino blanco 750ml", price=180.00, stock=35, category="Vinos"),
                    Product(name="Vino Santo Tomás Tinto", description="Vino tinto 750ml", price=220.00, stock=30, category="Vinos"),
                    Product(name="Vino Casa Madero Rosado", description="Vino rosado 750ml", price=200.00, stock=25, category="Vinos"),
                    
                    # Licores y Destilados
                    Product(name="Tequila José Cuervo Especial", description="Tequila reposado 750ml", price=280.00, stock=50, category="Tequilas"),
                    Product(name="Tequila Jimador Reposado", description="Tequila 100% agave 750ml", price=320.00, stock=45, category="Tequilas"),
                    Product(name="Tequila Herradura Blanco", description="Tequila blanco 750ml", price=450.00, stock=30, category="Tequilas"),
                    Product(name="Mezcal 400 Conejos", description="Mezcal joven 750ml", price=380.00, stock=35, category="Mezcales"),
                    Product(name="Ron Bacardi Blanco", description="Ron blanco 750ml", price=250.00, stock=40, category="Rones"),
                    Product(name="Vodka Absolut", description="Vodka premium 750ml", price=420.00, stock=30, category="Vodkas"),
                    Product(name="Whisky Johnnie Walker Red", description="Whisky escocés 750ml", price=480.00, stock=25, category="Whiskys"),
                    
                    # Aperitivos y Mezclas
                    Product(name="Squirt 600ml", description="Refresco de toronja", price=15.00, stock=100, category="Refrescos"),
                    Product(name="Coca Cola 600ml", description="Refresco de cola", price=15.00, stock=100, category="Refrescos"),
                    Product(name="Agua Mineral Topo Chico", description="Agua mineral 355ml", price=18.00, stock=80, category="Refrescos"),
                    Product(name="Jugo Jumex Naranja 1L", description="Jugo de naranja", price=25.00, stock=60, category="Jugos"),
                    
                    # Botanas
                    Product(name="Cacahuates Japoneses", description="Botana 150g", price=30.00, stock=70, category="Botanas"),
                    Product(name="Papas Sabritas Original", description="Papas fritas 170g", price=35.00, stock=60, category="Botanas"),
                    Product(name="Chicharrón Preparado", description="Botana 100g", price=25.00, stock=50, category="Botanas"),
                    Product(name="Mix de Nueces", description="Mezcla de nueces 200g", price=55.00, stock=40, category="Botanas"),
                    
                    # Cigarros
                    Product(name="Marlboro Rojo", description="Cajetilla 20 cigarros", price=75.00, stock=100, category="Cigarros"),
                    Product(name="Camel Blue", description="Cajetilla 20 cigarros", price=70.00, stock=80, category="Cigarros"),
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
            db.session.rollback()
    
    # Registrar blueprints
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp, url_prefix="/api")
    
    # Ruta principal - servir el frontend
    @app.route('/')
    def index():
        return send_from_directory(app.template_folder, 'index.html')
    
    return app