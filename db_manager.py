from extensions import db
from models import Guia, Idioma, Queja, DisponibilidadFecha, GuiaIdioma
from werkzeug.security import generate_password_hash
from sqlalchemy import or_, extract
from datetime import datetime

# --- Funciones de Inicialización ---
def db_inicializar_admin_y_idiomas(db):
    """Crea el administrador principal y los idiomas base si no existen."""
    try:
        if Guia.query.filter_by(licencia='ADMIN001').first() is None:
            # Hash para 'admin123'
            password_hash = generate_password_hash('admin123')
            admin = Guia(
                licencia='ADMIN001',
                nombre='Administrador Principal',
                password_hash=password_hash,
                rol='admin',
                aprobado=True,
                telefono='N/A',
                email='admin@guia.com',
                bio='Cuenta de administrador principal.'
            )
            db.session.add(admin)
            print("ADMIN001 creado.")

        idiomas_base = ['Español', 'Inglés', 'Portugués', 'Alemán', 'Francés']
        for nombre in idiomas_base:
            if Idioma.query.filter_by(nombre=nombre).first() is None:
                idioma = Idioma(nombre=nombre)
                db.session.add(idioma)
                print(f"Idioma '{nombre}' agregado.")

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error durante la inicialización de DB: {e}")

# --- Funciones de Guías (Usuarios) ---

def registrar_guia(licencia, nombre, password):
    """Registra un nuevo guía con estado 'no aprobado' por defecto."""
    if Guia.query.filter_by(licencia=licencia).first():
        return False
    
    password_hash = generate_password_hash(password)
    nuevo_guia = Guia(
        licencia=licencia,
        nombre=nombre,
        password_hash=password_hash,
        rol='guia',
        aprobado=False,
        telefono=None,
        email=None,
        bio=None
    )
    try:
        db.session.add(nuevo_guia)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error al registrar guía: {e}")
        return False

def get_guia_data(licencia, all_data=False):
    """Obtiene datos esenciales del guía para login o todos los datos para perfil."""
    guia = Guia.query.filter_by(licencia=licencia).first()
    if guia:
        if all_data:
            return (guia.password_hash, guia.nombre, guia.rol, guia.aprobado, guia.id, guia.telefono, guia.email, guia.bio)
        else:
            return (guia.password_hash, guia.rol, guia.aprobado)
    return None

def actualizar_password_db(licencia, nueva_password):
    """Actualiza la contraseña de un guía."""
    guia = Guia.query.filter_by(licencia=licencia).first()
    if guia:
        try:
            guia.password_hash = generate_password_hash(nueva_password)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar contraseña: {e}")
            return False
    return False

def actualizar_perfil_db(licencia, nombre, telefono, email, bio):
    """Actualiza los campos de perfil de un guía."""
    guia = Guia.query.filter_by(licencia=licencia).first()
    if guia:
        try:
            guia.nombre = nombre
            guia.telefono = telefono if telefono else None
            guia.email = email if email else None
            guia.bio = bio if bio else None
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar perfil: {e}")
            return False
    return False

def obtener_todos_los_guias():
    """Retorna una lista de todos los guías (incluyendo el admin)."""
    guias = Guia.query.all()
    lista_guias = []
    for g in guias:
        idiomas_guia = obtener_idiomas_de_guia(g.licencia)
        lista_guias.append({
            'licencia': g.licencia,
            'nombre': g.nombre,
            'rol': g.rol,
            'aprobado': g.aprobado,
            'email': g.email if g.email else 'N/A',
            'idiomas': ', '.join(idiomas_guia)
        })
    return lista_guias

def cambiar_aprobacion(licencia, estado):
    """Cambia el estado de aprobación de un guía."""
    guia = Guia.query.filter_by(licencia=licencia).first()
    if guia:
        try:
            guia.aprobado = (estado == 1)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al cambiar aprobación: {e}")
            return False
    return False

def promover_a_admin(licencia):
    """Cambia el rol de un guía a admin."""
    guia = Guia.query.filter_by(licencia=licencia).first()
    if guia and guia.rol != 'admin':
        try:
            guia.rol = 'admin'
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al promover a admin: {e}")
            return False
    return False

def degradar_a_guia(licencia):
    """Cambia el rol de un admin a guía (si no es ADMIN001)."""
    if licencia == 'ADMIN001':
        return False
        
    guia = Guia.query.filter_by(licencia=licencia).first()
    if guia and guia.rol == 'admin':
        try:
            guia.rol = 'guia'
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al degradar a guía: {e}")
            return False
    return False

def eliminar_guia(licencia):
    """Elimina un guía y sus registros asociados."""
    guia = Guia.query.filter_by(licencia=licencia).first()
    if guia and licencia != 'ADMIN001':
        try:
            # Elimina registros en tablas intermedias/dependientes (Quejas, Disponibilidad, GuiaIdioma)
            Queja.query.filter_by(licencia_guia=licencia).delete()
            DisponibilidadFecha.query.filter_by(licencia=licencia).delete()
            GuiaIdioma.query.filter_by(guia_id=guia.id).delete()
            
            db.session.delete(guia)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar guía: {e}")
            return False
    return False

# --- Funciones de Idiomas (Administración) ---

def agregar_idioma_db(nombre):
    """Agrega un nuevo idioma si no existe."""
    if Idioma.query.filter_by(nombre=nombre).first():
        return False
    
    nuevo_idioma = Idioma(nombre=nombre)
    try:
        db.session.add(nuevo_idioma)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error al agregar idioma: {e}")
        return False

def obtener_todos_los_idiomas():
    """Retorna una lista de tuplas (id, nombre) de todos los idiomas."""
    idiomas = Idioma.query.order_by(Idioma.nombre).all()
    return [(i.id, i.nombre) for i in idiomas]

def actualizar_idioma_db(idioma_id, nuevo_nombre):
    """Actualiza el nombre de un idioma."""
    idioma = Idioma.query.get(idioma_id)
    if idioma:
        # Verifica si el nuevo nombre ya existe
        if Idioma.query.filter(Idioma.nombre == nuevo_nombre, Idioma.id != idioma_id).first():
            return False
            
        try:
            idioma.nombre = nuevo_nombre
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar idioma: {e}")
            return False
    return False

def eliminar_idioma_db(idioma_id):
    """Elimina un idioma y sus asociaciones con los guías."""
    idioma = Idioma.query.get(idioma_id)
    if idioma:
        try:
            # Elimina las asociaciones en la tabla GuiaIdioma
            GuiaIdioma.query.filter_by(idioma_id=idioma_id).delete()
            db.session.delete(idioma)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar idioma: {e}")
            return False
    return False

# --- Funciones de Idiomas (Guía) ---

def obtener_idiomas_de_guia(licencia):
    """Retorna una lista de los nombres de los idiomas que habla un guía."""
    guia = Guia.query.filter_by(licencia=licencia).first()
    if guia:
        return [gi.idioma.nombre for gi in guia.idiomas_asociados]
    return []

def actualizar_idiomas_de_guia(licencia, idiomas_ids):
    """Sincroniza los idiomas de un guía con los IDs seleccionados."""
    guia = Guia.query.filter_by(licencia=licencia).first()
    if guia:
        try:
            # 1. Eliminar todas las asociaciones existentes
            GuiaIdioma.query.filter_by(guia_id=guia.id).delete()
            
            # 2. Crear nuevas asociaciones
            for idioma_id_str in idiomas_ids:
                try:
                    idioma_id = int(idioma_id_str)
                    nueva_asociacion = GuiaIdioma(guia_id=guia.id, idioma_id=idioma_id)
                    db.session.add(nueva_asociacion)
                except ValueError:
                    # Ignorar IDs inválidos
                    continue
            
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al actualizar idiomas del guía: {e}")
            return False
    return False

# --- Funciones de Quejas ---

def registrar_queja(licencia_guia, descripcion, reportado_por):
    """Registra una nueva queja."""
    if not Guia.query.filter_by(licencia=licencia_guia).first():
        return False
        
    nueva_queja = Queja(
        licencia_guia=licencia_guia,
        descripcion=descripcion,
        fecha_registro=datetime.now(),
        estado='pendiente',
        reportado_por=reportado_por
    )
    try:
        db.session.add(nueva_queja)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error al registrar queja: {e}")
        return False

def obtener_todas_las_quejas():
    """Retorna todas las quejas para el panel de administración."""
    quejas = Queja.query.order_by(Queja.fecha_registro.desc()).all()
    lista_quejas = []
    for q in quejas:
        lista_quejas.append({
            'id': q.id,
            'licencia_guia': q.licencia_guia,
            'nombre_guia': q.guia.nombre,
            'descripcion': q.descripcion,
            'fecha_registro': q.fecha_registro.strftime('%d/%m/%Y %H:%M'),
            'estado': q.estado,
            'reportado_por': q.reportado_por
        })
    return lista_quejas

def obtener_todas_las_quejas_para_guias():
    """Retorna todas las quejas (anónimas) para el panel de guías."""
    quejas = Queja.query.filter(Queja.reportado_por.startswith('Público')).order_by(Queja.fecha_registro.desc()).all()
    lista_quejas = []
    for q in quejas:
        lista_quejas.append({
            'id': q.id,
            'licencia_guia': q.licencia_guia,
            'nombre_guia': q.guia.nombre,
            'descripcion': q.descripcion,
            'fecha_registro': q.fecha_registro.strftime('%d/%m/%Y %H:%M'),
            'estado': q.estado,
            'reportado_por': 'Público' # Se anonimiza el nombre del reportante
        })
    return lista_quejas


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
            print(f"Error al eliminar la queja {queja_id}: {e}")
            return False
    return False

# --- Funciones de Disponibilidad ---

def agregar_disponibilidad_fecha(licencia, fecha, hora_inicio, hora_fin):
    """Agrega una fecha de disponibilidad específica para un guía."""
    try:
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d').date()
        
        # Verificar si ya existe una entrada para esa licencia y fecha
        if DisponibilidadFecha.query.filter_by(licencia=licencia, fecha=fecha_dt).first():
            return False

        nueva_disponibilidad = DisponibilidadFecha(
            licencia=licencia,
            fecha=fecha_dt,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin
        )
        db.session.add(nueva_disponibilidad)
        db.session.commit()
        return True
    except ValueError:
        # Error en formato de fecha
        return False
    except Exception as e:
        db.session.rollback()
        print(f"Error al agregar disponibilidad: {e}")
        return False

def obtener_disponibilidad_fechas(licencia):
    """Retorna las fechas de disponibilidad futura para un guía."""
    fechas = DisponibilidadFecha.query.filter(
        DisponibilidadFecha.licencia == licencia,
        DisponibilidadFecha.fecha >= datetime.now().date()
    ).order_by(DisponibilidadFecha.fecha).all()
    
    lista_fechas = []
    for f in fechas:
        lista_fechas.append({
            'id': f.id,
            'fecha': f.fecha.strftime('%Y-%m-%d'),
            'inicio': f.hora_inicio,
            'fin': f.hora_fin
        })
    return lista_fechas

def eliminar_disponibilidad_fecha(fecha_id, licencia_actual):
    """Elimina una fecha de disponibilidad por ID y verifica la pertenencia."""
    fecha = DisponibilidadFecha.query.filter(
        DisponibilidadFecha.id == fecha_id,
        DisponibilidadFecha.licencia == licencia_actual
    ).first()
    
    if fecha:
        try:
            db.session.delete(fecha)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar disponibilidad: {e}")
            return False
    return False

def buscar_guias_disponibles_por_fecha(fecha_str, idioma_id=None):
    """Busca guías aprobados disponibles en una fecha específica y opcionalmente por idioma."""
    try:
        fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return []

    # 1. Subconsulta de guías disponibles para la fecha
    guias_disponibles_licencias = db.session.query(DisponibilidadFecha.licencia).filter(
        DisponibilidadFecha.fecha == fecha_dt
    ).subquery()

    # 2. Consulta principal: Guías aprobados y disponibles
    query = Guia.query.filter(
        Guia.aprobado == True,
        Guia.rol == 'guia',
        Guia.licencia.in_(guias_disponibles_licencias)
    )

    # 3. Filtrar por idioma si se especifica
    if idioma_id:
        query = query.join(GuiaIdioma).filter(
            GuiaIdioma.idioma_id == idioma_id
        )

    guias = query.all()
    
    resultados = []
    for g in guias:
        # Obtener el horario de disponibilidad para la fecha
        disponibilidad = DisponibilidadFecha.query.filter_by(licencia=g.licencia, fecha=fecha_dt).first()
        
        # Obtener los nombres de los idiomas que habla
        idiomas_nombres = obtener_idiomas_de_guia(g.licencia)
        
        resultados.append({
            'nombre': g.nombre,
            'licencia': g.licencia,
            'telefono': g.telefono if g.telefono else 'No especificado',
            'email': g.email if g.email else 'No especificado',
            'bio': g.bio if g.bio else 'Sin biografía.',
            'horario': f"{disponibilidad.hora_inicio} - {disponibilidad.hora_fin}" if disponibilidad else 'N/A',
            'idiomas': ', '.join(idiomas_nombres)
        })

    return resultados
