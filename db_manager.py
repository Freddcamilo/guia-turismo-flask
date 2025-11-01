<<<<<<< HEAD
# db_manager.py - Versión Final Limpia y Corregida para PostgreSQL

import os
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from psycopg2 import sql # Necesario para manejar identificadores y consultas dinámicas
from dotenv import load_dotenv # Opcional: para cargar DATABASE_URL localmente

# Cargar variables de entorno si usas un archivo .env local
# load_dotenv() 

ADMIN_LICENCIA = 'ADMIN001'
ADMIN_PASSWORD_DEFAULT = 'admin123' 

def get_db_connection():
    """Establece la conexión con la base de datos PostgreSQL usando la URL de entorno."""
    
    # Render, Railway o cualquier hosting proporcionará esta variable.
    # Para pruebas locales, defínela manualmente o usa dotenv.
    DATABASE_URL = os.environ.get('DATABASE_URL') 
    
    if not DATABASE_URL:
        # Esto es crítico para el despliegue.
        raise Exception("Error de configuración: La variable de entorno 'DATABASE_URL' no está definida.")
        
    try:
        # Conexión con la URL proporcionada
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error al conectar con PostgreSQL: {e}")
        raise e

# --------------------------------------------------------------------------
# 1. INICIALIZACIÓN Y ESQUEMAS
# --------------------------------------------------------------------------

def inicializar_db():
    """Crea todas las tablas ajustando la sintaxis a PostgreSQL."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tabla GUIAS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS GUIAS (
                licencia VARCHAR(10) PRIMARY KEY,
                nombre VARCHAR(255) NOT NULL,
                password VARCHAR(255) NOT NULL,
                rol VARCHAR(50) NOT NULL DEFAULT 'guia',
                aprobado INTEGER NOT NULL DEFAULT 0,
                telefono VARCHAR(50) DEFAULT '',         
                email VARCHAR(255) DEFAULT '',           
                bio TEXT DEFAULT '',                     
                fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
    
        # Tabla IDIOMAS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS IDIOMAS (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL UNIQUE
            );
        """)
        
        # Tabla GUIA_IDIOMAS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS GUIA_IDIOMAS (
                licencia VARCHAR(10) NOT NULL,
                idioma_id INTEGER NOT NULL,
                PRIMARY KEY (licencia, idioma_id),
                FOREIGN KEY (licencia) REFERENCES GUIAS (licencia) ON DELETE CASCADE,
                FOREIGN KEY (idioma_id) REFERENCES IDIOMAS (id) ON DELETE CASCADE
            );
        """)

        # Tabla QUEJAS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS QUEJAS (
                id SERIAL PRIMARY KEY,
                licencia_guia VARCHAR(10) NOT NULL,
                fecha_queja TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                descripcion TEXT NOT NULL,
                estado VARCHAR(50) NOT NULL DEFAULT 'pendiente', 
                reportado_por TEXT, 
                FOREIGN KEY (licencia_guia) REFERENCES GUIAS (licencia) ON DELETE CASCADE
            );
        """)

        # Tabla DISPONIBILIDAD_FECHAS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS DISPONIBILIDAD_FECHAS (
                id SERIAL PRIMARY KEY,
                licencia_guia VARCHAR(10) NOT NULL,
                fecha DATE NOT NULL,
                hora_inicio TIME NOT NULL,
                hora_fin TIME NOT NULL,
                FOREIGN KEY (licencia_guia) REFERENCES GUIAS (licencia) ON DELETE CASCADE,
                UNIQUE (licencia_guia, fecha) 
            );
        """)

        # Asegurar Administrador Principal
        admin_password_hash = generate_password_hash(ADMIN_PASSWORD_DEFAULT)
        cursor.execute("SELECT COUNT(*) FROM GUIAS WHERE licencia = %s", (ADMIN_LICENCIA,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO GUIAS (licencia, nombre, password, rol, aprobado) 
                VALUES (%s, %s, %s, 'admin', 1)
            """, (ADMIN_LICENCIA, 'Administrador Principal', admin_password_hash))
            
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error al inicializar DB: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn: conn.close()

# --------------------------------------------------------------------------
# 2. FUNCIONES DE REGISTRO Y LOGIN
# --------------------------------------------------------------------------

def registrar_guia(licencia, nombre, password):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        password_hash = generate_password_hash(password)
        # Usamos %s para placeholders de PostgreSQL
        cursor.execute("INSERT INTO GUIAS (licencia, nombre, password, rol, aprobado) VALUES (%s, %s, %s, 'guia', 0)", 
                       (licencia, nombre, password_hash))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        return False
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def get_guia_data(licencia, all_data=False):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Usamos %s para placeholders de PostgreSQL
        query = "SELECT * FROM GUIAS WHERE licencia = %s" if all_data else "SELECT password, rol, aprobado FROM GUIAS WHERE licencia = %s"
        cursor.execute(query, (licencia,)) 
        data = cursor.fetchone()
        return data
    except psycopg2.Error:
        return None
    finally:
        if conn: conn.close()

# --------------------------------------------------------------------------
# 3. FUNCIONES DE ADMINISTRACIÓN (CRUD Guías)
# --------------------------------------------------------------------------

def obtener_todos_los_guias():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT licencia, nombre, rol, aprobado, fecha_registro, telefono, email FROM GUIAS ORDER BY fecha_registro DESC")
        guias = cursor.fetchall()
        return guias
    except psycopg2.Error:
        return []
    finally:
        if conn: conn.close()

def cambiar_aprobacion(licencia, estado):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE GUIAS SET aprobado = %s WHERE licencia = %s", (estado, licencia))
        conn.commit()
        return cursor.rowcount > 0
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def eliminar_guia(licencia):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM GUIAS WHERE licencia = %s", (licencia,))
        conn.commit()
        return cursor.rowcount > 0
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def promover_a_admin(licencia):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE GUIAS SET rol = 'admin' WHERE licencia = %s AND rol != 'admin'", (licencia,))
        conn.commit()
        return cursor.rowcount > 0
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def degradar_a_guia(licencia):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if licencia == ADMIN_LICENCIA:
            return False 
        cursor.execute("UPDATE GUIAS SET rol = 'guia' WHERE licencia = %s AND rol = 'admin'", (licencia,))
        conn.commit()
        return cursor.rowcount > 0
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

# --------------------------------------------------------------------------
# 4. FUNCIONES DE IDIOMAS (ADMIN/GUÍA)
# --------------------------------------------------------------------------

def agregar_idioma_db(nombre_idioma):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO IDIOMAS (nombre) VALUES (%s)", (nombre_idioma,))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        return False
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def obtener_todos_los_idiomas():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM IDIOMAS ORDER BY nombre ASC")
        idiomas = cursor.fetchall()
        return idiomas
    except psycopg2.Error:
        return []
    finally:
        if conn: conn.close()

def actualizar_idioma_db(idioma_id, nuevo_nombre):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE IDIOMAS SET nombre = %s WHERE id = %s", (nuevo_nombre, idioma_id))
        conn.commit()
        return cursor.rowcount > 0
    except psycopg2.IntegrityError:
        return False
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def eliminar_idioma_db(idioma_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM IDIOMAS WHERE id = %s", (idioma_id,))
        conn.commit()
        return cursor.rowcount > 0
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def obtener_idiomas_de_guia(licencia):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT idioma_id FROM GUIA_IDIOMAS WHERE licencia = %s", (licencia,))
        idiomas_ids = [row[0] for row in cursor.fetchall()]
        return idiomas_ids
    except psycopg2.Error:
        return []
    finally:
        if conn: conn.close()

def actualizar_idiomas_de_guia(licencia, idioma_ids):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # 1. Eliminar idiomas existentes
        cursor.execute("DELETE FROM GUIA_IDIOMAS WHERE licencia = %s", (licencia,))
        
        # 2. Insertar nuevos idiomas
        if idioma_ids:
            data = [(licencia, int(idioma_id)) for idioma_id in idioma_ids]
            insert_query = "INSERT INTO GUIA_IDIOMAS (licencia, idioma_id) VALUES (%s, %s)"
            cursor.executemany(insert_query, data)

        conn.commit()
        return True
    except psycopg2.Error:
        if conn: conn.rollback()
        return False
    finally:
        if conn: conn.close()

def obtener_idiomas_de_multiples_guias(licencias):
    """
    Obtiene los nombres de los idiomas dominados para una lista de licencias de guías.
    Devuelve un diccionario: {licencia: 'Idioma1, Idioma2, ...'}
    """
    if not licencias:
        return {}
        
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Usamos sql.SQL e sql.Placeholder para crear una consulta segura con múltiples parámetros
        placeholders = sql.SQL(',').join(sql.Placeholder() * len(licencias))
        
        query = sql.SQL("""
            SELECT 
                GI.licencia, 
                STRING_AGG(I.nombre, ', ') as idiomas_dominados -- STRING_AGG es el equivalente de GROUP_CONCAT en PostgreSQL
            FROM GUIA_IDIOMAS GI
            JOIN IDIOMAS I ON GI.idioma_id = I.id
            WHERE GI.licencia IN ({})
            GROUP BY GI.licencia
        """).format(placeholders)

        cursor.execute(query, licencias)
        
        idiomas_por_guia = {row[0]: row[1] for row in cursor.fetchall()}
        return idiomas_por_guia
    except psycopg2.Error:
        return {}
    finally:
        if conn: conn.close()


# --------------------------------------------------------------------------
# 5. FUNCIONES DE PERFIL EXTENDIDO (GUÍA)
# --------------------------------------------------------------------------

def actualizar_password_db(licencia, nueva_password):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        password_hash = generate_password_hash(nueva_password)
        cursor.execute("UPDATE GUIAS SET password = %s WHERE licencia = %s", (password_hash, licencia))
        conn.commit()
        return cursor.rowcount > 0
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def actualizar_perfil_db(licencia, nuevo_nombre, nuevo_telefono, nuevo_email, nueva_bio):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE GUIAS SET nombre = %s, telefono = %s, email = %s, bio = %s WHERE licencia = %s", 
                       (nuevo_nombre, nuevo_telefono, nuevo_email, nueva_bio, licencia))
        conn.commit()
        return cursor.rowcount > 0
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

# --------------------------------------------------------------------------
# 6. FUNCIONES DE GESTIÓN DE QUEJAS
# --------------------------------------------------------------------------

def registrar_queja(licencia_guia, descripcion, reportado_por=None):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO QUEJAS (licencia_guia, descripcion, reportado_por, estado) VALUES (%s, %s, %s, 'pendiente')", 
                       (licencia_guia, descripcion, reportado_por))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        return False
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def obtener_todas_las_quejas():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.id, q.licencia_guia, g.nombre, q.fecha_queja, q.descripcion, q.estado, q.reportado_por
            FROM QUEJAS q JOIN GUIAS g ON q.licencia_guia = g.licencia
            ORDER BY q.fecha_queja DESC
        """)
        quejas = cursor.fetchall()
        return quejas
    except psycopg2.Error:
        return []
    finally:
        if conn: conn.close()

def obtener_todas_las_quejas_para_guias():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                q.id, 
                q.licencia_guia, 
                g.nombre as nombre_guia,
                q.fecha_queja, 
                q.descripcion, 
                q.estado, 
                q.reportado_por
            FROM QUEJAS q
            JOIN GUIAS g ON q.licencia_guia = g.licencia
            ORDER BY q.fecha_queja DESC
        """)
        quejas = cursor.fetchall()
        return quejas
    except psycopg2.Error:
        return []
    finally:
        if conn: conn.close()


def actualizar_estado_queja(queja_id, nuevo_estado):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE QUEJAS SET estado = %s WHERE id = %s", (nuevo_estado, queja_id))
        conn.commit()
        return cursor.rowcount > 0
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def eliminar_queja_db(queja_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM QUEJAS WHERE id = %s", (queja_id,))
        conn.commit()
        return cursor.rowcount > 0
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

# --------------------------------------------------------------------------
# 7. FUNCIONES DE DISPONIBILIDAD (SOLO FECHAS) Y BÚSQUEDA
# --------------------------------------------------------------------------

def agregar_disponibilidad_fecha(licencia_guia, fecha, hora_inicio, hora_fin):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO DISPONIBILIDAD_FECHAS (licencia_guia, fecha, hora_inicio, hora_fin) VALUES (%s, %s, %s, %s)", 
                       (licencia_guia, fecha, hora_inicio, hora_fin))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        return False # Falla si ya existe una entrada para esa licencia/fecha (UNIQUE constraint)
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def obtener_disponibilidad_fechas(licencia_guia):
    """Obtiene todas las fechas específicas de disponibilidad de un guía (solo futuras o actuales)."""
    conn = None
    try:
        conn = get_db_connection()
        # Usamos una subclase de cursor o similar para obtener resultados como dict/Row si es necesario, pero aquí solo fetchall()
        cursor = conn.cursor()
        # En PostgreSQL, usamos CURRENT_DATE o NOW()::DATE para la fecha actual
        cursor.execute("""
            SELECT id, fecha, hora_inicio as inicio, hora_fin as fin
            FROM DISPONIBILIDAD_FECHAS 
            WHERE licencia_guia = %s AND fecha >= CURRENT_DATE
            ORDER BY fecha ASC
        """, (licencia_guia,))
        # Adaptación: El código anterior usaba row_factory=sqlite3.Row. Aquí devolvemos una lista de tuplas y mapeamos en el app.py si es necesario.
        # Para ser compatible con el código antiguo que usa dict(row) y evitar errores, devolvemos la tupla y el mapeo puede ser necesario en app.py.
        # Pero si el código en app.py espera un resultado de estilo diccionario, esto podría fallar.
        # Por simplicidad y compatibilidad con psycopg2.fetchall(), devolveremos las tuplas. Si falla en app.py, lo corregimos.
        
        # Mapeamos a lista de diccionarios para mantener compatibilidad con el código Flask (si usa dict(row))
        columnas = ['id', 'fecha', 'inicio', 'fin']
        data = [dict(zip(columnas, row)) for row in cursor.fetchall()]
        
        return data
    except psycopg2.Error:
        return []
    finally:
        if conn: conn.close()

def eliminar_disponibilidad_fecha(fecha_id, licencia_guia):
    """Elimina una fecha específica de disponibilidad."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM DISPONIBILIDAD_FECHAS WHERE id = %s AND licencia_guia = %s", 
                       (fecha_id, licencia_guia))
        conn.commit()
        return cursor.rowcount > 0
    except psycopg2.Error:
        return False
    finally:
        if conn: conn.close()

def buscar_guias_disponibles_por_fecha(fecha_buscada, idioma_id=None):
    """
    Busca guías que tienen disponibilidad registrada para la fecha_buscada,
    opcionalmente filtrado por un idioma específico.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        base_query = """
            SELECT 
                G.licencia, G.nombre, G.telefono, G.email, G.bio, 
                TO_CHAR(DF.hora_inicio, 'HH24:MI') as hora_inicio, 
                TO_CHAR(DF.hora_fin, 'HH24:MI') as hora_fin
            FROM GUIAS G
            JOIN DISPONIBILIDAD_FECHAS DF ON G.licencia = DF.licencia_guia
            WHERE DF.fecha = %s AND G.aprobado = 1
        """
        params = [fecha_buscada]
        
        if idioma_id:
            base_query += """
                AND G.licencia IN (
                    SELECT licencia FROM GUIA_IDIOMAS WHERE idioma_id = %s
                )
            """
            params.append(idioma_id)
            
        base_query += " ORDER BY G.nombre"
        
        cursor.execute(base_query, params)
        guias_raw = cursor.fetchall()

        # Mapeamos a lista de diccionarios con nombres de columnas
        columnas = ['licencia', 'nombre', 'telefono', 'email', 'bio', 'hora_inicio', 'hora_fin']
        guias = [dict(zip(columnas, row)) for row in guias_raw]
        
    except psycopg2.Error:
        return []
    finally:
        if conn: conn.close()

    # Enriquecer con idiomas, fuera de la conexión DB principal
    licencias = [g['licencia'] for g in guias]
    idiomas_por_guia = obtener_idiomas_de_multiples_guias(licencias)
    
    for guia in guias:
        guia['idiomas_dominados'] = idiomas_por_guia.get(guia['licencia'], 'N/A')
            
=======
# db_manager.py (VERSIÓN CORREGIDA FINAL)

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, time
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

# SE CORRIGE ESTA LÍNEA: Ahora importa 'db' desde extensions.py para romper la dependencia circular
from extensions import db 

ADMIN_LICENCIA = 'ADMIN001'
ADMIN_PASSWORD_DEFAULT = 'admin123'

# --------------------------------------------------------------------------
# 1. MODELOS DE SQLALCHEMY
# --------------------------------------------------------------------------

# Tabla auxiliar para la relación muchos a muchos Guia <-> Idioma
GuiaIdioma = db.Table('guia_idiomas',
    db.Column('licencia', db.String(50), db.ForeignKey('guias.licencia', ondelete='CASCADE'), primary_key=True),
    db.Column('idioma_id', db.Integer, db.ForeignKey('idiomas.id', ondelete='CASCADE'), primary_key=True)
)

class Guia(db.Model):
    __tablename__ = 'guias'
    licencia = db.Column(db.String(50), primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False) 
    rol = db.Column(db.String(10), nullable=False, default='guia')
    aprobado = db.Column(db.Integer, nullable=False, default=0) 
    telefono = db.Column(db.String(20), default='')
    email = db.Column(db.String(100), default='')
    bio = db.Column(db.Text, default='')
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación muchos a muchos con Idioma
    idiomas = db.relationship('Idioma', secondary=GuiaIdioma, backref=db.backref('guias_que_lo_hablan', lazy='dynamic'))

class Idioma(db.Model):
    __tablename__ = 'idiomas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

class Queja(db.Model):
    __tablename__ = 'quejas'
    id = db.Column(db.Integer, primary_key=True)
    licencia_guia = db.Column(db.String(50), db.ForeignKey('guias.licencia', ondelete='CASCADE'), nullable=False)
    fecha_queja = db.Column(db.DateTime, default=datetime.utcnow)
    descripcion = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(20), nullable=False, default='pendiente')
    reportado_por = db.Column(db.String(100), default='')
    
    guia = db.relationship('Guia', backref='quejas')

class DisponibilidadFecha(db.Model):
    __tablename__ = 'disponibilidad_fechas'
    id = db.Column(db.Integer, primary_key=True)
    licencia_guia = db.Column(db.String(50), db.ForeignKey('guias.licencia', ondelete='CASCADE'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    
    guia = db.relationship('Guia', backref='disponibilidades')
    
    __table_args__ = (db.UniqueConstraint('licencia_guia', 'fecha', name='_guia_fecha_uc'),)
    
# --------------------------------------------------------------------------
# 1.1 FUNCIÓN DE INICIALIZACIÓN Y ADMIN
# --------------------------------------------------------------------------

def db_inicializar_admin_y_idiomas(db_obj):
    """Inserta el administrador inicial y los idiomas base si no existen."""
    try:
        # 1. Crear Administrador Principal si no existe
        admin = Guia.query.get(ADMIN_LICENCIA)
        if not admin:
            admin_password_hash = generate_password_hash(ADMIN_PASSWORD_DEFAULT)
            admin = Guia(licencia=ADMIN_LICENCIA, nombre='Administrador Principal', password=admin_password_hash, rol='admin', aprobado=1)
            db_obj.session.add(admin)
            
        # 2. Insertar Idiomas Base (Ejemplo)
        idiomas_base = ['Español', 'Inglés', 'Francés', 'Alemán']
        for nombre in idiomas_base:
            if not Idioma.query.filter_by(nombre=nombre).first():
                db_obj.session.add(Idioma(nombre=nombre))
                
        db_obj.session.commit()
    except Exception as e:
        db_obj.session.rollback()
        print(f"Error al inicializar la DB: {e}")

# --------------------------------------------------------------------------
# 2. FUNCIONES DE REGISTRO Y LOGIN (MIGRADAS)
# --------------------------------------------------------------------------

def registrar_guia(licencia, nombre, password):
    try:
        if Guia.query.get(licencia):
            return False 
        
        password_hash = generate_password_hash(password)
        nuevo_guia = Guia(licencia=licencia, nombre=nombre, password=password_hash, rol='guia', aprobado=0)
        
        db.session.add(nuevo_guia)
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        return False
    except Exception:
        db.session.rollback()
        return False

def get_guia_data(licencia, all_data=False):
    guia = Guia.query.get(licencia)
    if not guia:
        return None

    if all_data:
        return (guia.licencia, guia.nombre, guia.password, guia.rol, guia.aprobado, guia.telefono, guia.email, guia.bio, guia.fecha_registro)
    else:
        return (guia.password, guia.rol, guia.aprobado)

# --------------------------------------------------------------------------
# 3. FUNCIONES DE ADMINISTRACIÓN (MIGRADAS)
# --------------------------------------------------------------------------

def obtener_todos_los_guias():
    guias = Guia.query.order_by(Guia.fecha_registro.desc()).all()
    return [(g.licencia, g.nombre, g.rol, g.aprobado, g.fecha_registro, g.telefono, g.email) for g in guias]

def cambiar_aprobacion(licencia, estado):
    guia = Guia.query.get(licencia)
    if not guia:
        return False
    try:
        guia.aprobado = estado
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

def eliminar_guia(licencia):
    if licencia == ADMIN_LICENCIA:
        return False
    guia = Guia.query.get(licencia)
    if not guia:
        return False
    try:
        db.session.delete(guia)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

def promover_a_admin(licencia):
    guia = Guia.query.filter(Guia.licencia == licencia, Guia.rol != 'admin').first()
    if not guia:
        return False
    try:
        guia.rol = 'admin'
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

def degradar_a_guia(licencia):
    if licencia == ADMIN_LICENCIA:
        return False
    guia = Guia.query.filter(Guia.licencia == licencia, Guia.rol == 'admin').first()
    if not guia:
        return False
    try:
        guia.rol = 'guia'
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

# --------------------------------------------------------------------------
# 4. FUNCIONES DE IDIOMAS (MIGRADAS)
# --------------------------------------------------------------------------

def agregar_idioma_db(nombre_idioma):
    try:
        if Idioma.query.filter_by(nombre=nombre_idioma).first():
            return False 
        
        nuevo_idioma = Idioma(nombre=nombre_idioma)
        db.session.add(nuevo_idioma)
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        return False
    except Exception:
        db.session.rollback()
        return False

def obtener_todos_los_idiomas():
    idiomas = Idioma.query.order_by(Idioma.nombre.asc()).all()
    return [(i.id, i.nombre) for i in idiomas]

def actualizar_idioma_db(idioma_id, nuevo_nombre):
    idioma = Idioma.query.get(idioma_id)
    if not idioma:
        return False
    try:
        if Idioma.query.filter(Idioma.nombre == nuevo_nombre, Idioma.id != idioma_id).first():
             return False
             
        idioma.nombre = nuevo_nombre
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        return False
    except Exception:
        db.session.rollback()
        return False

def eliminar_idioma_db(idioma_id):
    idioma = Idioma.query.get(idioma_id)
    if not idioma:
        return False
    try:
        db.session.delete(idioma)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

def obtener_idiomas_de_guia(licencia):
    guia = Guia.query.get(licencia)
    if not guia:
        return []
        
    return [idioma.id for idioma in guia.idiomas]

def actualizar_idiomas_de_guia(licencia, idioma_ids):
    guia = Guia.query.get(licencia)
    if not guia:
        return False
    try:
        guia.idiomas.clear() 
        db.session.flush() 
        
        nuevos_idiomas = Idioma.query.filter(Idioma.id.in_([int(id) for id in idioma_ids])).all()
        for idioma in nuevos_idiomas:
            guia.idiomas.append(idioma)
            
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

def obtener_idiomas_de_multiples_guias(licencias):
    if not licencias:
        return {}
        
    if db.engine.driver == 'psycopg2': # PostgreSQL driver
        agg_func = func.string_agg(Idioma.nombre, ', ').label('idiomas_dominados')
    else: # SQLite u otro
        agg_func = func.group_concat(Idioma.nombre, ', ').label('idiomas_dominados')

    resultados = db.session.query(
        GuiaIdioma.c.licencia,
        agg_func
    ).join(Idioma, GuiaIdioma.c.idioma_id == Idioma.id).filter(
        GuiaIdioma.c.licencia.in_(licencias)
    ).group_by(GuiaIdioma.c.licencia).all()
    
    return {lic: idiomas for lic, idiomas in resultados}

# --------------------------------------------------------------------------
# 5. FUNCIONES DE PERFIL EXTENDIDO (MIGRADAS)
# --------------------------------------------------------------------------

def actualizar_password_db(licencia, nueva_password):
    guia = Guia.query.get(licencia)
    if not guia:
        return False
    try:
        password_hash = generate_password_hash(nueva_password)
        guia.password = password_hash
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

def actualizar_perfil_db(licencia, nuevo_nombre, nuevo_telefono, nuevo_email, nueva_bio):
    guia = Guia.query.get(licencia)
    if not guia:
        return False
    try:
        guia.nombre = nuevo_nombre
        guia.telefono = nuevo_telefono
        guia.email = nuevo_email
        guia.bio = nueva_bio
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

# --------------------------------------------------------------------------
# 6. FUNCIONES DE GESTIÓN DE QUEJAS (MIGRADAS)
# --------------------------------------------------------------------------

def registrar_queja(licencia_guia, descripcion, reportado_por=None):
    try:
        nueva_queja = Queja(
            licencia_guia=licencia_guia,
            descripcion=descripcion,
            reportado_por=reportado_por,
            estado='pendiente'
        )
        db.session.add(nueva_queja)
        db.session.commit()
        return True
    except IntegrityError: 
        db.session.rollback()
        return False
    except Exception:
        db.session.rollback()
        return False

def obtener_todas_las_quejas():
    quejas = db.session.query(
        Queja.id, Queja.licencia_guia, Guia.nombre, Queja.fecha_queja, Queja.descripcion, Queja.estado, Queja.reportado_por
    ).join(Guia, Queja.licencia_guia == Guia.licencia).order_by(Queja.fecha_queja.desc()).all()
    
    return quejas

def obtener_todas_las_quejas_para_guias():
    return obtener_todas_las_quejas()


def actualizar_estado_queja(queja_id, nuevo_estado):
    queja = Queja.query.get(queja_id)
    if not queja:
        return False
    try:
        queja.estado = nuevo_estado
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

def eliminar_queja_db(queja_id):
    queja = Queja.query.get(queja_id)
    if not queja:
        return False
    try:
        db.session.delete(queja)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

# --------------------------------------------------------------------------
# 7. FUNCIONES DE DISPONIBILIDAD (MIGRADAS)
# --------------------------------------------------------------------------

def agregar_disponibilidad_fecha(licencia_guia, fecha_str, hora_inicio_str, hora_fin_str):
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        hora_inicio_obj = datetime.strptime(hora_inicio_str, '%H:%M').time()
        hora_fin_obj = datetime.strptime(hora_fin_str, '%H:%M').time()
        
        nueva_disponibilidad = DisponibilidadFecha(
            licencia_guia=licencia_guia,
            fecha=fecha_obj,
            hora_inicio=hora_inicio_obj,
            hora_fin=hora_fin_obj
        )
        db.session.add(nueva_disponibilidad)
        db.session.commit()
        return True
    except ValueError: 
        return False
    except IntegrityError: 
        db.session.rollback()
        return False
    except Exception:
        db.session.rollback()
        return False

def obtener_disponibilidad_fechas(licencia_guia):
    fechas = DisponibilidadFecha.query.filter(
        DisponibilidadFecha.licencia_guia == licencia_guia,
        DisponibilidadFecha.fecha >= func.current_date()
    ).order_by(DisponibilidadFecha.fecha.asc()).all()
    
    data = []
    for f in fechas:
        data.append({
            'id': f.id,
            'fecha': f.fecha.strftime('%Y-%m-%d'),
            'inicio': f.hora_inicio.strftime('%H:%M'),
            'fin': f.hora_fin.strftime('%H:%M')
        })
    return data

def eliminar_disponibilidad_fecha(fecha_id, licencia_guia):
    disponibilidad = DisponibilidadFecha.query.filter_by(id=fecha_id, licencia_guia=licencia_guia).first()
    if not disponibilidad:
        return False
    try:
        db.session.delete(disponibilidad)
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False

def buscar_guias_disponibles_por_fecha(fecha_buscada, idioma_id=None):
    try:
        fecha_obj = datetime.strptime(fecha_buscada, '%Y-%m-%d').date()
    except ValueError:
        return []

    query = db.session.query(
        Guia.licencia, Guia.nombre, Guia.telefono, Guia.email, Guia.bio,
        DisponibilidadFecha.hora_inicio, DisponibilidadFecha.hora_fin
    ).join(DisponibilidadFecha, Guia.licencia == DisponibilidadFecha.licencia_guia).filter(
        DisponibilidadFecha.fecha == fecha_obj,
        Guia.aprobado == 1
    )
    
    if idioma_id:
        query = query.join(GuiaIdioma, Guia.licencia == GuiaIdioma.c.licencia).filter(
            GuiaIdioma.c.idioma_id == idioma_id
        )
        
    query = query.order_by(Guia.nombre)
    
    guias_raw = query.all()
    
    licencias = [g[0] for g in guias_raw]
    idiomas_por_guia = obtener_idiomas_de_multiples_guias(licencias)
    
    guias = []
    for lic, nombre, tel, email, bio, inicio, fin in guias_raw:
        guias.append({
            'licencia': lic,
            'nombre': nombre,
            'telefono': tel,
            'email': email,
            'bio': bio,
            'hora_inicio': inicio.strftime('%H:%M'),
            'hora_fin': fin.strftime('%H:%M'),
            'idiomas_dominados': idiomas_por_guia.get(lic, 'N/A')
        })
        
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    return guias
