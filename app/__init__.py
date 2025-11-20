from flask import Flask
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
    
    # Importar modelos
    from .models import User, Role, LogEntry
    
    # Crear tablas y datos iniciales automáticamente
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tablas de base de datos verificadas/creadas")
            
            # Crear roles si no existen
            if not Role.query.first():
                admin_role = Role(name='admin')
                manager_role = Role(name='manager')
                viewer_role = Role(name='viewer')
                db.session.add_all([admin_role, manager_role, viewer_role])
                db.session.commit()
                print("✅ Roles creados: admin, manager, viewer")
            else:
                print("✅ Roles ya existen")
            
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
                
        except Exception as e:
            print(f"❌ Error al inicializar base de datos: {e}")
            db.session.rollback()
    
    # Registrar blueprints
    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp, url_prefix="/api")
    
    @app.route('/')
    def index():
        return "Sistema de Gestión - API funcionando"
    
    return app