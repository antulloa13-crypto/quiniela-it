"""
Configuración de la aplicación.
Soporta SQLite (por defecto), MySQL y PostgreSQL.
"""
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-secreta-quiniela-2024-CAMBIAR-en-produccion'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hora


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or
        'sqlite:///' + os.path.join(basedir, 'instance', 'quiniela.db')
    )


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL') or
        'sqlite:///' + os.path.join(basedir, 'instance', 'quiniela.db')
    )


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}

# =============================================================================
# Para migrar a MySQL:
#   Instalar: pip install PyMySQL
#   Establecer: DATABASE_URL=mysql+pymysql://user:password@localhost:3306/quiniela
#
# Para migrar a PostgreSQL:
#   Instalar: pip install psycopg2-binary
#   Establecer: DATABASE_URL=postgresql://user:password@localhost:5432/quiniela
#
# Las tablas se crean automáticamente con db.create_all() en ambos motores.
# =============================================================================
