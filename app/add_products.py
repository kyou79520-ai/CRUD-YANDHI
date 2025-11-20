# add_products.py - Script para agregar productos nuevos a la licorería
from app import create_app, db
from app.models import Product

app = create_app()

# Lista de nuevos productos a agregar
nuevos_productos = [
    # Agrega aquí los productos que quieras
    Product(name="Cerveza XX Lager 355ml", description="Cerveza clara", price=24.00, stock=100, category="Cervezas"),
    Product(name="Brandy Presidente", description="Brandy mexicano 750ml", price=180.00, stock=40, category="Licores"),
    # Agrega más productos aquí...
]

with app.app_context():
    try:
        for producto in nuevos_productos:
            # Verificar si ya existe
            existe = Product.query.filter_by(name=producto.name).first()
            if not existe:
                db.session.add(producto)
                print(f"✅ Agregado: {producto.name}")
            else:
                print(f"⚠️  Ya existe: {producto.name}")
        
        db.session.commit()
        print(f"\n🎉 Proceso completado. Total productos en BD: {Product.query.count()}")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()