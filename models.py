"""
Modelos de base de datos.
Usa SQLAlchemy ORM — compatible con SQLite, MySQL y PostgreSQL sin cambios.
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), default='participante', nullable=False)
    activo = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    pronosticos = db.relationship(
        'Pronostico', backref='usuario', lazy='dynamic',
        cascade='all, delete-orphan'
    )
    puntuacion = db.relationship(
        'Puntuacion', backref='usuario', uselist=False,
        cascade='all, delete-orphan'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def es_admin(self):
        return self.rol == 'admin'

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"

    def __repr__(self):
        return f'<User {self.username}>'


class Partido(db.Model):
    __tablename__ = 'partidos'

    id = db.Column(db.Integer, primary_key=True)
    equipo_a = db.Column(db.String(100), nullable=False)
    equipo_b = db.Column(db.String(100), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(20), default='pendiente', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    pronosticos = db.relationship(
        'Pronostico', backref='partido', lazy='dynamic',
        cascade='all, delete-orphan'
    )
    resultado = db.relationship(
        'Resultado', backref='partido', uselist=False,
        cascade='all, delete-orphan'
    )

    @property
    def esta_bloqueado(self):
        """True cuando la hora de inicio ya pasó — bloquea pronósticos."""
        return datetime.now() >= self.fecha_hora

    @property
    def segundos_restantes(self):
        diff = (self.fecha_hora - datetime.now()).total_seconds()
        return max(0, int(diff))

    def __repr__(self):
        return f'<Partido {self.equipo_a} vs {self.equipo_b}>'


class Pronostico(db.Model):
    __tablename__ = 'pronosticos'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    partido_id = db.Column(db.Integer, db.ForeignKey('partidos.id'), nullable=False)
    # Valores: 'equipo_a' | 'empate' | 'equipo_b'
    pronostico = db.Column(db.String(20), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint('usuario_id', 'partido_id', name='uq_pronostico_usuario_partido'),
    )

    def __repr__(self):
        return f'<Pronostico user={self.usuario_id} partido={self.partido_id} {self.pronostico}>'


class Resultado(db.Model):
    __tablename__ = 'resultados'

    id = db.Column(db.Integer, primary_key=True)
    partido_id = db.Column(
        db.Integer, db.ForeignKey('partidos.id'), unique=True, nullable=False
    )
    # Valores: 'equipo_a' | 'empate' | 'equipo_b'
    resultado = db.Column(db.String(20), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Resultado partido={self.partido_id} {self.resultado}>'


class Puntuacion(db.Model):
    __tablename__ = 'puntuaciones'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey('usuarios.id'), unique=True, nullable=False
    )
    puntos = db.Column(db.Integer, default=0, nullable=False)
    total_aciertos = db.Column(db.Integer, default=0, nullable=False)
    total_fallos = db.Column(db.Integer, default=0, nullable=False)
    racha_actual = db.Column(db.Integer, default=0, nullable=False)
    mejor_racha = db.Column(db.Integer, default=0, nullable=False)

    def __repr__(self):
        return f'<Puntuacion user={self.usuario_id} pts={self.puntos}>'
