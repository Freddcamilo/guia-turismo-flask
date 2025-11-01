# extensions.py

from flask_sqlalchemy import SQLAlchemy

# Inicializamos el objeto SQLAlchemy, pero no lo atamos (bind) a la app
# Se atará más tarde en app.py (db.init_app(app))
db = SQLAlchemy()
