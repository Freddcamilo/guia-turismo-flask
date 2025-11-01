# db_manager.py (VERSIÓN FINAL Y COMPLETA)

from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import or_, and_, extract
import locale
import os

# Establecer la localización a español para el formato de fechas
try:
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES')
    except locale.Error:
        pass

# --- 1. Definición de Modelos (Tablas) ---

# Tabla de asociación para la relación muchos a muchos Guia-Idioma
GuiaIdioma = db.Table('guia_idioma',
    db.Column('guia_licencia', db.String(50), db.ForeignKey('guia.licencia', ondelete='CASCADE'), primary_key=True),
    db.Column('idioma_id', db.Integer, db.ForeignKey('idioma.id', ondelete='CASCADE'), primary_key=True)
)

class Guia(db.Model):
    __tablename__ = 'guia'
    licencia = db.Column(db.String(50), primary_key=True, unique=True, nullable=False)
    nombre_completo = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(20), default='guia') # 'guia' o 'admin'
    aprobado = db.Column(db.Integer, default=0) # 0: Pendiente, 1: Aprobado
    telefono = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación uno a muchos con Queja y DisponibilidadFecha
    quejas_recibidas = db.relationship('Queja', backref='guia', lazy=True, cascade="all, delete-orphan")
    disponibilidad = db.relationship('DisponibilidadFecha', backref='guia', lazy=True, cascade="all, delete-orphan")
    
    # Relación muchos a muchos con Idioma
    idiomas = db.relationship('Idioma', secondary=GuiaIdioma, backref=db.backref('guias', lazy='dynamic'))

    def __repr__(self):
        return f'<Guia {self.licencia} - {self.nombre_completo}>'

class Idioma(db.Model):
    __tablename__ = 'idioma'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Idioma {self.nombre}>'

class Queja(db.Model):
    __tablename__ = 'queja'
    id = db.Column(db.Integer, primary_key=True)
    guia_licencia = db.Column(db.String(50), db.ForeignKey('guia.licencia', ondelete='CASCADE'), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_reporte = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='pendiente') # pendiente, en revision, resuelta
    reportado_por = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<Queja {self.id} - Guía: {self.guia_licencia} - Estado: {self.estado}>'

class DisponibilidadFecha(db.Model):
    __tablename__ = 'disponibilidad_fecha'
    id = db.Column(db.Integer, primary_key=True)
    guia_licencia = db.Column(db.String(50), db.ForeignKey('guia.licencia', ondelete='CASCADE'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.String(5), nullable=True)
    hora_fin = db.Column(db.String(5), nullable=True)

    # Combinación de licencia y fecha debe ser única (un guía solo puede tener una entrada por fecha)
    __table_args__ = (db.UniqueConstraint('guia_licencia', 'fecha', name='_guia_fecha_uc'),)

    def __repr__(self):
        return f'<Disponibilidad {self.guia_licencia} - {self.fecha}>'


# --- 2. Funciones de Inicialización ---

def db_inicializar_admin_y_idiomas(db):
    """Crea el administrador inicial y los idiomas base si no existen."""
    # Contexto de la aplicación es necesario para interactuar con db
    
    # 1. Crear usuario Administrador inicial (ADMIN001)
    if not Guia.query.get('ADMIN001'):
        try:
            hashed_password = generate_password_hash('admin1234')
            admin_guia = Guia(
                licencia='ADMIN001',
                nombre_completo='Administrador Principal',
                password_hash=hashed_password,
                rol='admin',
                aprobado=1,
                email='admin@mp.com'
            )
            db.session.add(admin_guia)
            print("ADMIN001 creado.")
        except IntegrityError:
            db.session.rollback()
            print("ADMIN001 ya existe (IntegrityError).")
        except OperationalError as e:
            # Esto puede ocurrir si la tabla Guia aún no existe
            db.session.rollback()
            print(f"Error Operacional al crear ADMIN001: {e}")
        except Exception as e:
            db.session.rollback()
            print(f"Error desconocido al crear ADMIN001: {e}")


    # 2. Crear idiomas base
    idiomas_base = ['Español', 'Inglés', 'Portugués', 'Alemán', 'Francés']
    
    for nombre in idiomas_base:
        if not Idioma.query.filter_by(nombre=nombre).first():
            try:
                nuevo_idioma = Idioma(nombre=nombre)
                db.session.add(nuevo_idioma)
                print(f"Idioma '{nombre}' agregado.")
            except IntegrityError:
                db.session.rollback()
                print(f"Idioma '{nombre}' ya existe.")
            except Exception as e:
                db.session.rollback()
                print(f"Error al agregar idioma '{nombre}': {e}")
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error al commitear la inicialización: {e}")

# --- 3. Funciones de Guías (Usuarios) ---

def registrar_guia(licencia, nombre, password):
    """Registra un nuevo guía con rol 'guia' y estado 'pendiente'."""
    try:
        if Guia.query.get(licencia):
            return False # Licencia ya registrada

        hashed_password = generate_password_hash(password)
        
        nuevo_guia = Guia(
            licencia=licencia,
            nombre_completo=nombre,
            password_hash=hashed_password,
            rol='guia',
            aprobado=0
        )
        db.session.add(nuevo_guia)
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error al registrar guía: {e}")
        return False

def get_guia_data(licencia, all_data=False):
    """Obtiene datos de un guía para login o edición de perfil."""
    guia = Guia.query.get(licencia)
    if guia:
        if all_data:
            return (guia.password_hash, guia.nombre_completo, guia.rol, guia.aprobado, guia.licencia, guia.telefono, guia.email, guia.bio)
        else:
            return (guia.password_hash, guia.rol, guia.aprobado)
    return None

def obtener_todos_los_guias():
    """Retorna una lista de todos los guías registrados."""
    return Guia.query.order_by(Guia.fecha_registro.desc()).all()

def cambiar_aprobacion(licencia, estado):
    """Cambia el estado de aprobación de un guía (0:pendiente, 1:aprobado)."""
    guia = Guia.query.get(licencia)
    if guia:
        try:
            guia.aprobado = estado
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al cambiar aprobación: {e}")
    return False

def eliminar_guia(licencia):
    """Elimina un guía y toda la información asociada (Quejas, Disponibilidad, Idiomas)."""
    guia = Guia.query.get(licencia)
    if guia and guia.licencia != 'ADMIN001':
        try:
            db.session.delete(guia)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar guía: {e}")
    return False

def actualizar_password_db(licencia, nueva_password):
    """Actualiza la contraseña de un guía."""
    guia = Guia.query.get(licencia)
    if guia:
        try:
            guia.password_hash = generate_password_hash(nueva_password)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar password: {e}")
    return False

def actualizar_perfil_db(licencia, nombre, telefono, email, bio):
    """Actualiza la información pública y de contacto de un guía."""
    guia = Guia.query.get(licencia)
    if guia:
        try:
            guia.nombre_completo = nombre
            guia.telefono = telefono
            guia.email = email
            guia.bio = bio
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar perfil: {e}")
    return False

def promover_a_admin(licencia):
    """Cambia el rol de un guía a 'admin'."""
    guia = Guia.query.get(licencia)
    if guia and guia.rol != 'admin':
        try:
            guia.rol = 'admin'
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al promover a admin: {e}")
    return False

def degradar_a_guia(licencia):
    """Cambia el rol de un admin a 'guia'."""
    guia = Guia.query.get(licencia)
    if guia and guia.rol == 'admin' and guia.licencia != 'ADMIN001':
        try:
            guia.rol = 'guia'
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al degradar a guia: {e}")
    return False

# --- 4. Funciones de Idiomas ---

def obtener_todos_los_idiomas():
    """Retorna una lista de tuplas (id, nombre) de todos los idiomas."""
    return db.session.query(Idioma.id, Idioma.nombre).order_by(Idioma.nombre).all()

def agregar_idioma_db(nombre):
    """Agrega un nuevo idioma a la base de datos."""
    try:
        nuevo_idioma = Idioma(nombre=nombre)
        db.session.add(nuevo_idioma)
        db.session.commit()
        return True
    except IntegrityError:
        db.session.rollback()
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error al agregar idioma: {e}")
        return False

def actualizar_idioma_db(idioma_id, nuevo_nombre):
    """Actualiza el nombre de un idioma existente."""
    idioma = Idioma.query.get(idioma_id)
    if idioma:
        try:
            idioma.nombre = nuevo_nombre
            db.session.commit()
            return True
        except IntegrityError:
            db.session.rollback()
            return False
        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar idioma: {e}")
    return False

def eliminar_idioma_db(idioma_id):
    """Elimina un idioma y sus relaciones con los guías."""
    idioma = Idioma.query.get(idioma_id)
    if idioma:
        try:
            db.session.delete(idioma)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar idioma: {e}")
    return False

def obtener_idiomas_de_guia(licencia):
    """Retorna una lista de IDs de idiomas que un guía habla."""
    guia = Guia.query.get(licencia)
    if guia:
        return [idioma.id for idioma in guia.idiomas]
    return []

def actualizar_idiomas_de_guia(licencia, idiomas_ids):
    """Actualiza la lista de idiomas que habla un guía."""
    guia = Guia.query.get(licencia)
    if guia:
        try:
            # Limpiar la lista actual de idiomas
            guia.idiomas.clear()
            db.session.commit()

            # Agregar los nuevos idiomas
            for id_idioma in idiomas_ids:
                idioma = Idioma.query.get(id_idioma)
                if idioma:
                    guia.idiomas.append(idioma)
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar idiomas de guía: {e}")
    return False

# --- 5. Funciones de Quejas ---

def registrar_queja(licencia_guia, descripcion, reportado_por):
    """Registra una nueva queja contra un guía."""
    try:
        nueva_queja = Queja(
            guia_licencia=licencia_guia,
            descripcion=descripcion,
            estado='pendiente',
            reportado_por=reportado_por
        )
        db.session.add(nueva_queja)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error al registrar queja: {e}")
        return False

def obtener_todas_las_quejas():
    """Retorna todas las quejas para el panel de administración."""
    return Queja.query.order_by(Queja.fecha_reporte.desc()).all()

def obtener_todas_las_quejas_para_guias():
    """Retorna todas las quejas con información básica para el panel de guías."""
    quejas = db.session.query(
        Queja.id,
        Queja.guia_licencia,
        Guia.nombre_completo,
        Queja.fecha_reporte,
        Queja.estado
    ).join(Guia, Guia.licencia == Queja.guia_licencia).order_by(Queja.fecha_reporte.desc()).all()
    
    # Formatear la salida para el template
    quejas_formato = []
    for q_id, q_licencia, g_nombre, q_fecha, q_estado in quejas:
        quejas_formato.append({
            'id': q_id,
            'licencia_guia': q_licencia,
            'nombre_guia': g_nombre,
            'fecha_reporte': q_fecha.strftime('%d/%m/%Y %H:%M'),
            'estado': q_estado
        })
    return quejas_formato

def actualizar_estado_queja(queja_id, nuevo_estado):
    """Actualiza el estado de una queja."""
    queja = Queja.query.get(queja_id)
    if queja:
        try:
            queja.estado = nuevo_estado
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar estado de queja: {e}")
    return False

def eliminar_queja_db(queja_id):
    """Elimina una queja por su ID."""
    queja = Queja.query.get(queja_id)
    if queja:
        try:
            db.session.delete(queja)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar queja: {e}")
    return False

# --- 6. Funciones de Disponibilidad ---

def agregar_disponibilidad_fecha(licencia, fecha_str, hora_inicio, hora_fin):
    """Agrega una nueva fecha de disponibilidad para un guía."""
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()

        # Verificar si ya existe una entrada para esta fecha
        existe = DisponibilidadFecha.query.filter(
            DisponibilidadFecha.guia_licencia == licencia,
            DisponibilidadFecha.fecha == fecha_obj
        ).first()

        if existe:
            return False # Ya existe disponibilidad para esta fecha

        nueva_disponibilidad = DisponibilidadFecha(
            guia_licencia=licencia,
            fecha=fecha_obj,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin
        )
        db.session.add(nueva_disponibilidad)
        db.session.commit()
        return True
    except ValueError:
        db.session.rollback()
        return False # Formato de fecha inválido
    except IntegrityError:
        db.session.rollback()
        return False # Violación de restricción única
    except Exception as e:
        db.session.rollback()
        print(f"Error al agregar disponibilidad: {e}")
        return False

def obtener_disponibilidad_fechas(licencia):
    """Retorna una lista de las fechas de disponibilidad de un guía."""
    disponibilidad = DisponibilidadFecha.query.filter_by(guia_licencia=licencia).order_by(DisponibilidadFecha.fecha).all()
    
    return [{
        'id': d.id,
        'fecha': d.fecha.strftime('%Y-%m-%d'),
        'inicio': d.hora_inicio,
        'fin': d.hora_fin
    } for d in disponibilidad]

def eliminar_disponibilidad_fecha(fecha_id, licencia_guia):
    """Elimina una entrada de disponibilidad si pertenece al guía."""
    disponibilidad = DisponibilidadFecha.query.filter(
        DisponibilidadFecha.id == fecha_id,
        DisponibilidadFecha.guia_licencia == licencia_guia
    ).first()

    if disponibilidad:
        try:
            db.session.delete(disponibilidad)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar disponibilidad: {e}")
    return False

def buscar_guias_disponibles_por_fecha(fecha_str, idioma_id=None):
    """Busca guías que estén disponibles en una fecha específica y hablen un idioma (opcional)."""
    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return []

    # 1. Obtener todas las licencias disponibles para esa fecha
    licencias_disponibles = db.session.query(DisponibilidadFecha.guia_licencia).filter(
        DisponibilidadFecha.fecha == fecha_obj
    ).subquery()

    # 2. Base Query: Guías Aprobados y Disponibles
    query = db.session.query(Guia).filter(
        Guia.aprobado == 1,
        Guia.licencia.in_(licencias_disponibles)
    )

    # 3. Filtrar por Idioma si se especificó
    if idioma_id:
        query = query.join(Guia.idiomas).filter(Idioma.id == idioma_id)

    guias_encontrados = query.all()

    # 4. Formatear los resultados
    resultados = []
    for guia in guias_encontrados:
        
        # Obtener el idioma de forma más legible
        idiomas_que_habla = ", ".join([i.nombre for i in guia.idiomas])
        
        # Obtener los horarios disponibles
        horarios = DisponibilidadFecha.query.filter(
            DisponibilidadFecha.guia_licencia == guia.licencia,
            DisponibilidadFecha.fecha == fecha_obj
        ).first()
        
        horario_str = f"{horarios.hora_inicio} - {horarios.hora_fin}" if horarios else "No especificado"

        resultados.append({
            'licencia': guia.licencia,
            'nombre': guia.nombre_completo,
            'telefono': guia.telefono or 'N/A',
            'email': guia.email or 'N/A',
            'bio': guia.bio or 'Sin biografía',
            'idiomas': idiomas_que_habla,
            'horario': horario_str
        })
        
    return resultados
