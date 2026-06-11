"""
Inicialización de la base de datos en producción.
Ejecutar UNA SOLA VEZ en el servidor antes de iniciar la app:

    python init_db.py

Crea las tablas y el usuario administrador si no existen.
Para cargar datos de prueba adicionales usar setup.py en su lugar.
"""
import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('FLASK_CONFIG', 'production')

from app import create_app
from extensions import db
from models import User, Puntuacion

app = create_app('production')

with app.app_context():
    print("Creando tablas...")
    db.create_all()

    if User.query.filter_by(username='admin').first():
        print("La base de datos ya existe. No se modificó nada.")
        print("Para reiniciar: eliminá el archivo instance/quiniela.db y volvé a ejecutar.")
        sys.exit(0)

    admin = User(
        username='admin',
        nombre='Administrador',
        apellido='Sistema',
        rol='admin',
        activo=True,
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.flush()
    db.session.add(Puntuacion(usuario_id=admin.id))
    db.session.commit()

    print("")
    print("=" * 45)
    print("  BASE DE DATOS INICIALIZADA")
    print("=" * 45)
    print("  Usuario admin: admin")
    print("  Contraseña:    admin123")
    print("")
    print("  IMPORTANTE: cambiá la contraseña del")
    print("  administrador luego del primer login.")
    print("=" * 45)
