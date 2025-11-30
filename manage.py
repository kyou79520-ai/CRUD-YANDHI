from app import create_app, db
from flask_migrate import Migrate
from app.models import Role, User
import click
import os

app = create_app()
migrate = Migrate(app, db)

@app.cli.command("create-defaults")
def create_defaults():
    """Crea roles y un usuario admin por defecto (admin/admin123)"""
    with app.app_context():
        if not Role.query.filter_by(name="admin").first():
            r1 = Role(name="admin")
            r2 = Role(name="manager")
            r3 = Role(name="viewer")
            db.session.add_all([r1, r2, r3])
            db.session.commit()
            print("✅ Roles created")
        if not User.query.filter_by(username="admin").first():
            admin_role = Role.query.filter_by(name="admin").first()
            u = User(username="admin", role=admin_role)
            u.set_password("admin123")
            db.session.add(u)
            db.session.commit()
            print("✅ Admin user created (username=admin, password=admin123)")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)