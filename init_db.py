# init_db.py
from app import app
from extensions import db
from db_manager import db_inicializar_admin_y_idiomas

print("Iniciando la inicialización de la base de datos...")

with app.app_context():
    # Crea todas las tablas definidas en los modelos (si no existen)
    db.create_all()
    print("Tablas creadas con éxito.")
    
    # Crea el administrador ADMIN001 y los idiomas base (si no existen)
    db_inicializar_admin_y_idiomas(db)
    print("Admin y idiomas base inicializados con éxito.")
