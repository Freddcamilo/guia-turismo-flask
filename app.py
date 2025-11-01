<<<<<<< HEAD
# app.py - Versión Final Limpia y Corregida para Render (PostgreSQL)

import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime, date
from werkzeug.security import check_password_hash
# import sqlite3 # <--- Ya no se necesita, usas PostgreSQL

# Importar TODAS las funciones necesarias de db_manager
from db_manager import (
    inicializar_db, registrar_guia, get_guia_data, check_password_hash,
    obtener_todos_los_guias, cambiar_aprobacion, eliminar_guia, promover_a_admin, degradar_a_guia,
    obtener_todos_los_idiomas, agregar_idioma_db, actualizar_idioma_db, eliminar_idioma_db, 
    obtener_idiomas_de_guia, actualizar_idiomas_de_guia, obtener_idiomas_de_multiples_guias,
    actualizar_password_db, actualizar_perfil_db, 
    registrar_queja, obtener_todas_las_quejas, actualizar_estado_queja, eliminar_queja_db,
    agregar_disponibilidad_fecha, obtener_disponibilidad_fechas, eliminar_disponibilidad_fecha,
    buscar_guias_disponibles_por_fecha,
    obtener_todas_las_quejas_para_guias
)

app = Flask(__name__)
# Usa la variable de entorno SECRET_KEY (necesaria en Render)
app.secret_key = os.environ.get('SECRET_KEY', 'una_clave_secreta_por_defecto_y_muy_larga')


# --------------------------------------------------------------------------
# DECORADORES Y FUNCIONES GLOBALES
# --------------------------------------------------------------------------

def login_required(f):
    """Decorador para requerir inicio de sesión."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session.get('logged_in'):
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorador para requerir rol de administrador."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_rol') != 'admin':
            flash('Acceso denegado: Se requiere ser administrador.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


# --------------------------------------------------------------------------
# RUTAS PÚBLICAS Y DE AUTENTICACIÓN
=======
# app.py (VERSIÓN FINAL CORREGIDA)

from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime
import locale
import os 
# AÑADIDO: Importar el objeto 'db' desde el nuevo archivo de extensiones
from extensions import db 

# Establecer la localización a español
try:
    locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'es_ES')
    except locale.Error:
        pass

# --- 1. Configuración de la Aplicación y la Base de Datos ---
app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Configuración de Conexión a Base de Datos (PostgreSQL en la Nube / SQLite Local)
DB_URL = os.environ.get('DATABASE_URL', 'sqlite:///guias_local.db')
DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# AÑADIDO: Inicializar 'db' con la aplicación
db.init_app(app)

# Importar funciones de db_manager.py (incluye la importación de modelos)
from db_manager import (
    Guia, Idioma, Queja, DisponibilidadFecha, GuiaIdioma, db_inicializar_admin_y_idiomas, 
    registrar_guia, get_guia_data,
    actualizar_password_db, actualizar_perfil_db,
    obtener_todos_los_guias, cambiar_aprobacion, eliminar_guia, promover_a_admin, degradar_a_guia,
    agregar_idioma_db, obtener_todos_los_idiomas, actualizar_idioma_db, eliminar_idioma_db,
    obtener_idiomas_de_guia, actualizar_idiomas_de_guia,
    registrar_queja, obtener_todas_las_quejas, actualizar_estado_queja,
    agregar_disponibilidad_fecha, obtener_disponibilidad_fechas, eliminar_disponibilidad_fecha,
    buscar_guias_disponibles_por_fecha,
    obtener_todas_las_quejas_para_guias,
    eliminar_queja_db
)

# --------------------------------------------------------------------------
# Decoradores y Sesión 
# --------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('menu_principal'))
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------------------------------------------------
# Rutas Públicas y de Autenticación 
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
# --------------------------------------------------------------------------

@app.before_first_request
def setup():
    """Inicializa la base de datos al inicio."""
    # Esto creará las tablas si no existen.
    try:
        inicializar_db()
        print("Base de datos PostgreSQL inicializada o verificada con éxito.")
    except Exception as e:
        print(f"ERROR FATAL al inicializar la DB: {e}")
        # En un entorno de producción, puedes optar por no continuar si la DB falla.

@app.route('/')
<<<<<<< HEAD
def home():
    # Obtener el catálogo de idiomas para el filtro de búsqueda
    idiomas_catalogo = obtener_todos_los_idiomas()
    return render_template('home.html', idiomas_catalogo=idiomas_catalogo)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        licencia = request.form['licencia'].strip()
        password = request.form['password']
        
        guia_data = get_guia_data(licencia, all_data=False) # Obtiene (password_hash, rol, aprobado)

        if guia_data and check_password_hash(guia_data[0], password):
            rol = guia_data[1]
            aprobado = guia_data[2]
            
            if aprobado == 0 and rol != 'admin':
                flash('Tu cuenta aún está pendiente de aprobación por el administrador.', 'warning')
                return redirect(url_for('login'))
            
            # Inicio de sesión exitoso
            session['logged_in'] = True
            session['user_licencia'] = licencia
            session['user_rol'] = rol
            
            if rol == 'admin':
                return redirect(url_for('panel_admin'))
            else:
                return redirect(url_for('panel_guia'))
        else:
            flash('Credenciales inválidas.', 'error')
    
    return render_template('login.html')
=======
@app.route('/menu')
def menu_principal():
    return render_template('menu_principal.html')

@app.route('/registro_guia', methods=['GET', 'POST'])
def registro_guia():
    if request.method == 'POST':
        licencia = request.form.get('licencia')
        nombre = request.form.get('nombre')
        password = request.form.get('password')
        
        if not licencia or not nombre or not password:
            flash('Todos los campos son obligatorios.', 'error')
            return render_template('registro_guia.html')

        if registrar_guia(licencia, nombre, password):
            flash('Registro exitoso. Su cuenta debe ser aprobada por un administrador antes de iniciar sesión.', 'success')
            return redirect(url_for('login_guia'))
        else:
            flash('Error: La licencia ya está registrada.', 'error')
            return render_template('registro_guia.html')

    return render_template('registro_guia.html')

@app.route('/login_guia', methods=['GET', 'POST'])
def login_guia():
    if request.method == 'POST':
        licencia = request.form.get('licencia')
        password = request.form.get('password')
        
        guia_data = get_guia_data(licencia)
        
        if guia_data:
            guia_password_hash = guia_data[0]
            guia_rol = guia_data[1]
            guia_aprobado = guia_data[2]
            
            if check_password_hash(guia_password_hash, password):
                
                if guia_aprobado == 0:
                    flash('Su cuenta aún no ha sido aprobada por un administrador.', 'warning')
                    return render_template('login_guia.html')

                session['logged_in'] = True
                session['user_licencia'] = licencia
                session['user_rol'] = guia_rol
                
                flash('Inicio de sesión exitoso.', 'success')
                
                if guia_rol == 'admin':
                    return redirect(url_for('panel_admin'))
                else:
                    return redirect(url_for('panel_guia'))
            else:
                flash('Licencia o Contraseña incorrecta.', 'error')
        else:
            flash('Licencia o Contraseña incorrecta.', 'error')
            
    return render_template('login_guia.html')
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)

@app.route('/logout')
@login_required
def logout():
    session.clear()
<<<<<<< HEAD
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        licencia = request.form['licencia'].strip()
        nombre = request.form['nombre']
        password = request.form['password']
        
        if registrar_guia(licencia, nombre, password):
            flash('Registro exitoso. Tu cuenta está pendiente de aprobación por el administrador.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error al registrar: La licencia ya está en uso o datos inválidos.', 'error')
    
    return render_template('register.html')

@app.route('/reportar_queja', methods=['GET', 'POST'])
def reportar_queja():
    guias = obtener_todos_los_guias() 
    
    if request.method == 'POST':
        licencia_guia = request.form.get('licencia_guia')
        descripcion = request.form.get('descripcion')
        reportado_por = request.form.get('reportado_por') or "Anónimo" # Reportado por campo de texto público
        
        if not get_guia_data(licencia_guia, all_data=False):
            flash(f'Error: No existe un guía registrado con la licencia {licencia_guia}.', 'error')
            return render_template('reportar_queja.html', guias=guias)

        if registrar_queja(licencia_guia, descripcion, reportado_por):
            flash('Queja registrada con éxito. Será revisada por la administración.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Error al registrar la queja.', 'error')
            
    return render_template('reportar_queja.html', guias=guias)

@app.route('/buscar_guia', methods=['POST'])
def buscar_guia():
    fecha_str = request.form.get('fecha')
    idioma_id = request.form.get('idioma')
    
    if not fecha_str:
        flash('Debe seleccionar una fecha para buscar.', 'error')
        return redirect(url_for('home'))

    try:
        fecha_buscada = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Formato de fecha inválido.', 'error')
        return redirect(url_for('home'))

    idioma_id = int(idioma_id) if idioma_id and idioma_id != '0' else None
    
    guias_disponibles = buscar_guias_disponibles_por_fecha(fecha_buscada, idioma_id)
    
    idiomas_catalogo = {i[0]: i[1] for i in obtener_todos_los_idiomas()}
    idioma_nombre = idiomas_catalogo.get(idioma_id) if idioma_id else "Cualquier idioma"
    
    return render_template('resultados_busqueda.html', 
                            guias=guias_disponibles, 
                            fecha=fecha_buscada.strftime('%d-%m-%Y'),
                            idioma_nombre=idioma_nombre)


# --------------------------------------------------------------------------
# RUTAS DE PANELES Y FUNCIONALIDAD DE GUÍA
=======
    flash('Has cerrado sesión con éxito.', 'info')
    return redirect(url_for('menu_principal'))

@app.route('/reportar_queja', methods=['GET', 'POST'])
def reportar_queja_publico():
    if request.method == 'POST':
        licencia_guia = request.form.get('licencia_guia').strip()
        nombre_reportante = request.form.get('nombre_reportante').strip()
        descripcion = request.form.get('descripcion').strip()
        
        if not licencia_guia or not descripcion:
            flash('La licencia del guía y la descripción son obligatorias.', 'error')
            return render_template('reportar_queja.html')
        
        if not get_guia_data(licencia_guia):
            flash(f'Error: No existe un guía registrado con la licencia {licencia_guia}.', 'error')
            return render_template('reportar_queja.html', 
                                   licencia_guia=licencia_guia, 
                                   nombre_reportante=nombre_reportante, 
                                   descripcion=descripcion)

        reportado_por_tag = f"Público: {nombre_reportante}" if nombre_reportante else "Público Anónimo"

        if registrar_queja(licencia_guia, descripcion, reportado_por_tag):
            flash('Su queja ha sido registrada y será revisada por la administración.', 'success')
            return redirect(url_for('menu_principal'))
        else:
            flash('Error al intentar registrar la queja.', 'error')

    return render_template('reportar_queja.html')

@app.route('/buscar_guia', methods=['GET', 'POST'])
def buscar_guia():
    idiomas = obtener_todos_los_idiomas()
    resultados = []
    
    fecha_actual_str = datetime.now().strftime('%Y-%m-%d')
    fecha_actual_formateada = datetime.now().strftime('%A, %d de %B').title()
    
    fecha_buscada = fecha_actual_str
    fecha_buscada_formateada = fecha_actual_formateada
    idioma_id = None
    
    if request.method == 'POST':
        fecha_buscada = request.form.get('fecha_buscada')
        idioma_id = request.form.get('idioma_id')
        
        if not fecha_buscada:
            flash('Por favor, ingrese una fecha válida.', 'error')
            fecha_buscada = fecha_actual_str
        
        try:
            fecha_buscada_obj = datetime.strptime(fecha_buscada, '%Y-%m-%d')
            fecha_buscada_formateada = fecha_buscada_obj.strftime('%A, %d de %B').title()
        except ValueError:
            flash('Formato de fecha inválido. Usando la fecha actual.', 'error')
            fecha_buscada = fecha_actual_str
            fecha_buscada_formateada = fecha_actual_formateada
    
    if fecha_buscada:
        idioma_id_int = int(idioma_id) if idioma_id and idioma_id.isdigit() else None
        
        resultados = buscar_guias_disponibles_por_fecha(fecha_buscada, idioma_id_int)
        
        if request.method == 'POST':
            if not resultados:
                flash(f"No se encontraron guías disponibles para la fecha {fecha_buscada_formateada}.", 'info')
            else:
                 flash(f"Se encontraron {len(resultados)} guías disponibles para el {fecha_buscada_formateada}.", 'success')

    return render_template(
        'buscar_guia.html', 
        idiomas=idiomas, 
        resultados=resultados, 
        fecha_buscada=fecha_buscada, 
        fecha_buscada_formateada=fecha_buscada_formateada,
        idioma_id=idioma_id,
        fecha_actual=fecha_actual_str 
    )

# --------------------------------------------------------------------------
# Rutas de Paneles Principales
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
# --------------------------------------------------------------------------

@app.route('/panel_guia')
@login_required
def panel_guia():
<<<<<<< HEAD
    if session.get('user_rol') == 'admin':
        return redirect(url_for('panel_admin')) 
        
=======
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    return render_template('panel_guia.html')

@app.route('/panel_admin')
@login_required
<<<<<<< HEAD
@admin_required
def panel_admin():
    return render_template('panel_admin.html') 

@app.route('/editar_mi_perfil', methods=['GET', 'POST'])
@login_required
def editar_mi_perfil():
    licencia = session.get('user_licencia')
    guia_info_tuple = get_guia_data(licencia, all_data=True) 

    if not guia_info_tuple:
        flash('Error: No se pudo cargar la información del perfil.', 'error')
        return redirect(url_for('panel_guia'))

    # Crear el diccionario 'guia' que la plantilla espera
    perfil_data = {
        'licencia': guia_info_tuple[0], 
        'nombre': guia_info_tuple[1], 
        'telefono': guia_info_tuple[5] if guia_info_tuple[5] else '', 
        'email': guia_info_tuple[6] if guia_info_tuple[6] else '',
        'bio': guia_info_tuple[7] if guia_info_tuple[7] else ''
    }
    
    idiomas_catalogo = obtener_todos_los_idiomas()
    idiomas_seleccionados_ids = obtener_idiomas_de_guia(licencia)

    if request.method == 'POST':
        # 1. Obtener datos del formulario
        nuevo_nombre = request.form.get('nombre')
        nuevo_telefono = request.form.get('telefono')
        nuevo_email = request.form.get('email')
        nueva_bio = request.form.get('bio')
        idiomas_elegidos = request.form.getlist('idiomas')
        
        # 2. Actualizar datos básicos
        if actualizar_perfil_db(licencia, nuevo_nombre, nuevo_telefono, nuevo_email, nueva_bio):
            flash('Datos del perfil actualizados correctamente.', 'success')
        else:
            flash('Error al actualizar los datos básicos.', 'error')

        # 3. Actualizar idiomas
        if actualizar_idiomas_de_guia(licencia, idiomas_elegidos):
            flash('Idiomas actualizados correctamente.', 'success')
        else:
            flash('Error al actualizar los idiomas.', 'error')
            
        return redirect(url_for('editar_mi_perfil'))

    # Método GET: Renderizar plantilla
    return render_template('editar_perfil.html', 
                            guia=perfil_data, # Pasa el objeto 'guia'
                            idiomas_catalogo=idiomas_catalogo, 
                            idiomas_seleccionados_ids=idiomas_seleccionados_ids)

@app.route('/actualizar_password', methods=['POST'])
@login_required
def actualizar_password():
    licencia = session.get('user_licencia')
    actual_password = request.form.get('actual_password') # Se requiere la actual para la verificación
    nueva_password = request.form.get('nueva_password')
    
    guia_data = get_guia_data(licencia, all_data=False)
    
    if not guia_data or not check_password_hash(guia_data[0], actual_password):
        flash('Contraseña actual incorrecta.', 'error')
    elif len(nueva_password) < 6:
        flash('La nueva contraseña debe tener al menos 6 caracteres.', 'error')
    elif actualizar_password_db(licencia, nueva_password):
        session.clear() 
        flash('Contraseña actualizada correctamente. Por favor, inicie sesión de nuevo.', 'success')
        return redirect(url_for('login'))
    else:
        flash('Error al actualizar la contraseña.', 'error')

    return redirect(url_for('editar_mi_perfil'))
=======
def panel_admin():
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo administradores.', 'error')
        return redirect(url_for('panel_guia'))
        
    return render_template('panel_admin.html')

# --------------------------------------------------------------------------
# Rutas de Gestión de Perfil
# --------------------------------------------------------------------------

@app.route('/cambiar_contrasena', methods=['GET', 'POST'])
@login_required
def cambiar_contrasena():
    if request.method == 'POST':
        licencia = session.get('user_licencia')
        actual_password = request.form.get('actual_password')
        nueva_password = request.form.get('nueva_password')
            
        guia_data = get_guia_data(licencia)
        
        if guia_data and check_password_hash(guia_data[0], actual_password):
            if actualizar_password_db(licencia, nueva_password):
                flash('Contraseña actualizada con éxito. Por favor, vuelva a iniciar sesión.', 'success')
                session.clear()
                return redirect(url_for('login_guia'))
            else:
                flash('Error al intentar actualizar la contraseña.', 'error')
        else:
            flash('Contraseña actual incorrecta.', 'error')
            
    return render_template('cambiar_contrasena.html')

@app.route('/editar_mi_perfil', methods=['GET', 'POST'])
@login_required
def editar_mi_perfil():
    licencia = session.get('user_licencia')
    guia_info = get_guia_data(licencia, all_data=True)

    if not guia_info:
        flash('Error al cargar la información del perfil.', 'error')
        return redirect(url_for('panel_guia'))
    
    perfil_data = {'nombre': guia_info[1], 'telefono': guia_info[5], 'email': guia_info[6], 'bio': guia_info[7]}
    
    if request.method == 'POST':
        nuevo_nombre = request.form.get('nombre')
        nuevo_telefono = request.form.get('telefono')
        nuevo_email = request.form.get('email')
        nueva_bio = request.form.get('bio')
        
        if actualizar_perfil_db(licencia, nuevo_nombre, nuevo_telefono, nuevo_email, nueva_bio):
            flash('Perfil actualizado con éxito.', 'success')
            return redirect(url_for('panel_admin') if session.get('user_rol') == 'admin' else url_for('panel_guia'))
        else:
            flash('Error al actualizar el perfil.', 'error')
            perfil_data.update({'nombre': nuevo_nombre, 'telefono': nuevo_telefono, 'email': nuevo_email, 'bio': nueva_bio})
            return render_template('editar_perfil.html', **perfil_data)
    
    return render_template('editar_perfil.html', **perfil_data)

@app.route('/gestion_mis_idiomas', methods=['GET', 'POST'])
@login_required
def gestion_mis_idiomas():
    licencia = session.get('user_licencia')
    
    if request.method == 'POST':
        idiomas_seleccionados_ids = request.form.getlist('idiomas_seleccionados')
        
        if actualizar_idiomas_de_guia(licencia, idiomas_seleccionados_ids):
            flash('Sus idiomas han sido actualizados con éxito.', 'success')
        else:
            flash('Error al actualizar sus idiomas.', 'error')
            
        return redirect(url_for('panel_admin') if session.get('user_rol') == 'admin' else url_for('panel_guia'))

    todos_los_idiomas = obtener_todos_los_idiomas()
    idiomas_actuales_ids = obtener_idiomas_de_guia(licencia)
    
    idiomas_para_plantilla = []
    for id_idioma, nombre_idioma in todos_los_idiomas:
        idiomas_para_plantilla.append({
            'id': id_idioma,
            'nombre': nombre_idioma,
            'seleccionado': id_idioma in idiomas_actuales_ids
        })

    return render_template(
        'gestion_mis_idiomas.html', 
        idiomas_disponibles=idiomas_para_plantilla
    )

@app.route('/ver_quejas_comunidad')
@login_required
def ver_quejas_comunidad():
    rol = session.get('user_rol')
    if rol == 'admin':
        flash('Acceso denegado. Use el panel de administración para gestionar las quejas.', 'error')
        return redirect(url_for('gestion_quejas'))
    
    if rol != 'guia':
        flash('Acceso denegado: Solo para guías registrados.', 'error')
        return redirect(url_for('menu_principal'))

    quejas = obtener_todas_las_quejas_para_guias()
    
    licencia_actual = session.get('user_licencia')
    
    return render_template('ver_quejas_comunidad.html', 
                           quejas=quejas, 
                           licencia_actual=licencia_actual)

# --------------------------------------------------------------------------
# Rutas de Gestión de Disponibilidad
# --------------------------------------------------------------------------
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)

@app.route('/gestionar_disponibilidad', methods=['GET'])
@login_required
def gestionar_disponibilidad():
    licencia = session.get('user_licencia')
    
<<<<<<< HEAD
    fechas_especificas = obtener_disponibilidad_fechas(licencia) 
    
    datos_fechas = []
    for fecha_data in fechas_especificas:
        fecha_obj = datetime.strptime(str(fecha_data['fecha']), '%Y-%m-%d')
=======
    fechas_especificas = obtener_disponibilidad_fechas(licencia)
    
    datos_fechas = []
    for fecha_data in fechas_especificas:
        fecha_obj = datetime.strptime(fecha_data['fecha'], '%Y-%m-%d')
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
        fecha_formateada = fecha_obj.strftime('%A, %d de %B').title()
        
        datos_fechas.append({
            'id': fecha_data['id'],
            'fecha': fecha_formateada,
            'inicio': fecha_data['inicio'],
            'fin': fecha_data['fin']
        })
        
    fecha_actual_str = datetime.now().strftime('%Y-%m-%d')

    return render_template(
        'gestionar_disponibilidad.html', 
        fechas_especificas=datos_fechas,
<<<<<<< HEAD
        fecha_actual=fecha_actual_str 
=======
        fecha_actual=fecha_actual_str
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    )

@app.route('/agregar_fecha_disponible', methods=['POST'])
@login_required
def agregar_fecha_disponible():
    licencia = session.get('user_licencia')
    fecha = request.form.get('fecha')
    hora_inicio = request.form.get('hora_inicio')
    hora_fin = request.form.get('hora_fin')

    if not (fecha and hora_inicio and hora_fin):
        flash('Debe seleccionar una fecha, hora de inicio y hora de fin.', 'error')
    elif agregar_disponibilidad_fecha(licencia, fecha, hora_inicio, hora_fin):
        flash(f'Disponibilidad añadida para el {fecha}.', 'success')
    else:
<<<<<<< HEAD
        flash(f'Error: Ya existe una disponibilidad para el {fecha} o la fecha no es válida.', 'error')
=======
        # LÍNEA CORREGIDA DEL SYNTAXERROR
        flash(f'Error: Ya existe una disponibilidad para el {fecha} o la fecha no es válida.', 'error') 
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
        
    return redirect(url_for('gestionar_disponibilidad'))

@app.route('/eliminar_fecha_disponible/<int:fecha_id>', methods=['POST'])
@login_required
def eliminar_fecha_disponible(fecha_id):
    licencia = session.get('user_licencia')

    if eliminar_disponibilidad_fecha(fecha_id, licencia):
        flash('Fecha de disponibilidad eliminada con éxito.', 'info')
    else:
        flash('Error al eliminar la fecha de disponibilidad. (ID no encontrado o no autorizado)', 'error')

    return redirect(url_for('gestionar_disponibilidad'))

<<<<<<< HEAD

@app.route('/ver_quejas_comunidad')
@login_required
def ver_quejas_comunidad():
    if session.get('user_rol') == 'admin':
        flash('Acceso denegado. Use el panel de administración para gestionar las quejas.', 'error')
        return redirect(url_for('panel_admin'))

    quejas = obtener_todas_las_quejas_para_guias()
    
    licencia_actual = session.get('user_licencia') 
    
    return render_template('ver_quejas_comunidad.html', 
                            quejas=quejas, 
                            licencia_actual=licencia_actual)

=======
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
# --------------------------------------------------------------------------
# Rutas de Gestión del Administrador (Guías, Idiomas, Quejas)
# --------------------------------------------------------------------------

@app.route('/gestion_guias')
@login_required
<<<<<<< HEAD
@admin_required
def gestion_guias():
=======
def gestion_guias():
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo administradores.', 'error')
        return redirect(url_for('panel_guia'))
        
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    guias = obtener_todos_los_guias()
    return render_template('gestion_guias.html', guias=guias)

@app.route('/toggle_aprobacion/<licencia>/<int:estado>', methods=['POST'])
@login_required
<<<<<<< HEAD
@admin_required
def toggle_aprobacion(licencia, estado):
=======
def toggle_aprobacion(licencia, estado):
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo administradores.', 'error')
        return redirect(url_for('panel_guia'))
    
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    if cambiar_aprobacion(licencia, estado):
        accion = "aprobada" if estado == 1 else "desaprobada"
        flash(f'La cuenta {licencia} ha sido {accion} con éxito.', 'success')
    else:
        flash(f'Error al cambiar el estado de aprobación de {licencia}.', 'error')
        
    return redirect(url_for('gestion_guias'))

@app.route('/promover_guia/<licencia>', methods=['POST'])
@login_required
<<<<<<< HEAD
@admin_required
def promover_guia(licencia):
=======
def promover_guia(licencia):
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo los administradores pueden promover guías.', 'error')
        return redirect(url_for('panel_admin'))

>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    if promover_a_admin(licencia):
        flash(f'La licencia {licencia} ha sido promovida a Administrador.', 'success')
    else:
        flash(f'Error al promover la licencia {licencia}. (Podría ya ser administrador)', 'error')

    return redirect(url_for('gestion_guias'))

@app.route('/degradar_guia/<licencia>', methods=['POST'])
@login_required
<<<<<<< HEAD
@admin_required
def degradar_guia(licencia):
=======
def degradar_guia(licencia):
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo los administradores pueden degradar guías.', 'error')
        return redirect(url_for('panel_admin'))

>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    if degradar_a_guia(licencia):
        flash(f'La licencia {licencia} ha sido degradada a Guía regular.', 'success')
    else:
        flash(f'Error al degradar la licencia {licencia}. (Podría ser ADMIN001 o ya era Guía)', 'error')

    return redirect(url_for('gestion_guias'))

@app.route('/eliminar_guia/<licencia>', methods=['POST'])
@login_required
<<<<<<< HEAD
@admin_required
def eliminar_guia_ruta(licencia):
=======
def eliminar_guia_ruta(licencia):
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo administradores.', 'error')
        return redirect(url_for('panel_guia'))
        
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    if licencia == 'ADMIN001':
        flash('Error de seguridad: No se puede eliminar la cuenta del Administrador Principal (ADMIN001).', 'error')
        return redirect(url_for('gestion_guias'))

    if eliminar_guia(licencia):
        flash(f'La cuenta {licencia} ha sido eliminada con éxito.', 'success')
    else:
        flash(f'Error al eliminar la cuenta {licencia}.', 'error')
        
    return redirect(url_for('gestion_guias'))
    
@app.route('/gestion_idiomas')
@login_required
<<<<<<< HEAD
@admin_required
def gestion_idiomas():
    idiomas = obtener_todos_los_idiomas()
        
    return render_template('gestion_idiomas.html', idiomas=idiomas) 

@app.route('/agregar_idioma', methods=['POST'])
@login_required
@admin_required
def agregar_idioma():
=======
def gestion_idiomas():
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo administradores.', 'error')
        return redirect(url_for('panel_guia'))
    
    idiomas = obtener_todos_los_idiomas()
        
    return render_template('gestion_idiomas.html', idiomas=idiomas)

@app.route('/agregar_idioma', methods=['POST'])
@login_required
def agregar_idioma():
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo administradores.', 'error')
        return redirect(url_for('panel_admin'))
        
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    nombre_idioma = request.form.get('nombre_idioma').strip()
    
    if not nombre_idioma:
        flash('El nombre del idioma no puede estar vacío.', 'error')
    elif agregar_idioma_db(nombre_idioma):
        flash(f'El idioma "{nombre_idioma}" ha sido agregado con éxito.', 'success')
    else:
        flash(f'Error: El idioma "{nombre_idioma}" ya existe o hubo un error.', 'error')
        
    return redirect(url_for('gestion_idiomas'))

@app.route('/editar_idioma/<int:idioma_id>', methods=['POST'])
@login_required
<<<<<<< HEAD
@admin_required
def editar_idioma(idioma_id):
=======
def editar_idioma(idioma_id):
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo administradores.', 'error')
        return redirect(url_for('panel_admin'))
        
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    nuevo_nombre = request.form.get('nombre_idioma_edit').strip()
    
    if not nuevo_nombre:
        flash('El nombre del idioma no puede estar vacío.', 'error')
    elif actualizar_idioma_db(idioma_id, nuevo_nombre):
        flash(f'El idioma ha sido actualizado a "{nuevo_nombre}" con éxito.', 'success')
    else:
        flash(f'Error al actualizar el idioma. (El nombre podría ya existir).', 'error')
        
    return redirect(url_for('gestion_idiomas'))

@app.route('/eliminar_idioma/<int:idioma_id>', methods=['POST'])
@login_required
<<<<<<< HEAD
@admin_required
def eliminar_idioma(idioma_id):
=======
def eliminar_idioma(idioma_id):
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo administradores.', 'error')
        return redirect(url_for('panel_admin'))
        
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    if eliminar_idioma_db(idioma_id):
        flash('Idioma eliminado con éxito.', 'success')
    else:
        flash('Error al intentar eliminar el idioma.', 'error')
        
    return redirect(url_for('gestion_idiomas'))

@app.route('/gestion_quejas')
@login_required
<<<<<<< HEAD
@admin_required
def gestion_quejas():
    quejas = obtener_todas_las_quejas()
    return render_template('gestion_quejas.html', quejas=quejas)

@app.route('/toggle_estado_queja/<int:queja_id>/<string:estado>', methods=['POST'])
@login_required
@admin_required
def toggle_estado_queja(queja_id, estado):
    if actualizar_estado_queja(queja_id, estado):
        flash(f'El estado de la queja {queja_id} se actualizó a "{estado}".', 'success')
    else:
        flash('Error al actualizar el estado de la queja.', 'error')
=======
def gestion_quejas():
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo administradores.', 'error')
        return redirect(url_for('panel_guia'))
        
    quejas = obtener_todas_las_quejas()
    estados_posibles = ['pendiente', 'en revision', 'resuelta']
    
    return render_template('gestion_quejas.html', 
                           quejas=quejas,
                           estados_posibles=estados_posibles)

@app.route('/actualizar_estado_queja/<int:queja_id>/<nuevo_estado>', methods=['POST'])
@login_required
def actualizar_estado(queja_id, nuevo_estado):
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo administradores pueden cambiar el estado.', 'error')
        return redirect(url_for('gestion_quejas'))
        
    if nuevo_estado not in ['pendiente', 'en revision', 'resuelta']:
        flash('Estado no válido.', 'error')
        return redirect(url_for('gestion_quejas'))
        
    if actualizar_estado_queja(queja_id, nuevo_estado):
        flash(f'El estado de la queja #{queja_id} se actualizó a "{nuevo_estado}".', 'success')
    else:
        flash(f'Error al actualizar el estado de la queja #{queja_id}.', 'error')
        
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    return redirect(url_for('gestion_quejas'))

@app.route('/eliminar_queja/<int:queja_id>', methods=['POST'])
@login_required
<<<<<<< HEAD
@admin_required
def eliminar_queja_ruta(queja_id):
    if eliminar_queja_db(queja_id):
        flash(f'Queja {queja_id} eliminada con éxito.', 'success')
    else:
        flash('Error al eliminar la queja.', 'error')
=======
def eliminar_queja(queja_id):
    if session.get('user_rol') != 'admin':
        flash('Acceso denegado: Solo administradores pueden eliminar quejas.', 'error')
        return redirect(url_for('gestion_quejas'))
        
    if eliminar_queja_db(queja_id):
        flash(f'La queja #{queja_id} ha sido eliminada permanentemente.', 'success')
    else:
        flash(f'Error al intentar eliminar la queja #{queja_id}.', 'error')
        
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
    return redirect(url_for('gestion_quejas'))


# --------------------------------------------------------------------------
<<<<<<< HEAD
# INICIO DE LA APLICACIÓN (CRÍTICO: SOLUCIONA EL ERROR DE PUERTO)
# --------------------------------------------------------------------------

if __name__ == '__main__':
    # Esta línea soluciona el error de "Port scan timeout" en Render.
    # Obtiene el puerto asignado por Render (os.environ.get('PORT')) o usa 5000 por defecto.
    port = int(os.environ.get('PORT', 5000))  
    app.run(debug=True, host='0.0.0.0', port=port)
=======
# Inicialización (Modificado para usar SQLAlchemy y manejo de contexto)
# --------------------------------------------------------------------------

if __name__ == '__main__':
    with app.app_context():
        # Crea tablas si no existen e inicializa ADMIN001 e idiomas
        db.create_all() 
        db_inicializar_admin_y_idiomas(db) 
        
    # El servidor Gunicorn ignora este bloque, solo se usa para desarrollo local
    app.run(debug=True)
>>>>>>> 4838b2a (Migración a SQLAlchemy completada y listo para despliegue)
