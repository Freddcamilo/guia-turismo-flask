from extensions import db

# Tabla de asociación para la relación muchos a muchos Guia-Idioma
guia_idioma = db.Table('guia_idioma',
    db.Column('guia_id', db.Integer, db.ForeignKey('guia.id'), primary_key=True),
    db.Column('idioma_id', db.Integer, db.ForeignKey('idioma.id'), primary_key=True)
)

class Guia(db.Model):
    __tablename__ = 'guia'
    id = db.Column(db.Integer, primary_key=True)
    licencia = db.Column(db.String(80), unique=True, nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    rol = db.Column(db.String(20), default='guia') # 'guia' o 'admin'
    aprobado = db.Column(db.Boolean, default=False)
    
    # Campos de perfil adicionales
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(120))
    bio = db.Column(db.Text)

    # Relaciones
    quejas = db.relationship('Queja', backref='guia', lazy=True)
    disponibilidad = db.relationship('DisponibilidadFecha', backref='guia', lazy=True)
    
    # Relación muchos a muchos con Idioma
    idiomas_asociados = db.relationship('GuiaIdioma', back_populates='guia')

    def __repr__(self):
        return f'<Guia {self.licencia}>'

class Idioma(db.Model):
    __tablename__ = 'idioma'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    # Relación muchos a muchos con Guia
    guias_asociados = db.relationship('GuiaIdioma', back_populates='idioma')

    def __repr__(self):
        return f'<Idioma {self.nombre}>'

class GuiaIdioma(db.Model):
    __tablename__ = 'guia_idioma_asociacion'
    guia_id = db.Column(db.Integer, db.ForeignKey('guia.id'), primary_key=True)
    idioma_id = db.Column(db.Integer, db.ForeignKey('idioma.id'), primary_key=True)

    # Relaciones para acceder a los objetos
    guia = db.relationship('Guia', back_populates='idiomas_asociados')
    idioma = db.relationship('Idioma', back_populates='guias_asociados')
    
class Queja(db.Model):
    __tablename__ = 'queja'
    id = db.Column(db.Integer, primary_key=True)
    licencia_guia = db.Column(db.String(80), db.ForeignKey('guia.licencia'), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_registro = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(20), default='pendiente') # 'pendiente', 'en_revision', 'resuelta'
    reportado_por = db.Column(db.String(120), default='Público') # Para identificar quién la reportó
    
    def __repr__(self):
        return f'<Queja {self.id} - Guia {self.licencia_guia}>'

class DisponibilidadFecha(db.Model):
    __tablename__ = 'disponibilidad_fecha'
    id = db.Column(db.Integer, primary_key=True)
    licencia = db.Column(db.String(80), db.ForeignKey('guia.licencia'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.String(10), nullable=False)
    hora_fin = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Disponibilidad {self.licencia} - {self.fecha}>'
