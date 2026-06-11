"""
Quiniela Deportiva — Punto de entrada principal.
Ejecutar con: python app.py
"""
import os
from datetime import datetime
from flask import Flask, render_template
from extensions import db, login_manager, csrf
from config import config

basedir = os.path.abspath(os.path.dirname(__file__))


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Crear directorio instance si no existe (necesario para SQLite)
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

    # Inicializar extensiones
    db.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para continuar.'
    login_manager.login_message_category = 'warning'

    # Cargar usuario para Flask-Login
    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.participant import participant_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(participant_bp)

    # Filtros de plantilla para formatear fechas
    @app.template_filter('fmt_datetime')
    def fmt_datetime(value, fmt='%d/%m/%Y %H:%M'):
        if value is None:
            return ''
        return value.strftime(fmt)

    @app.template_filter('fmt_date')
    def fmt_date(value, fmt='%d/%m/%Y'):
        if value is None:
            return ''
        return value.strftime(fmt)

    @app.template_filter('fmt_time')
    def fmt_time(value, fmt='%H:%M'):
        if value is None:
            return ''
        return value.strftime(fmt)

    @app.template_filter('to_timestamp_ms')
    def to_timestamp_ms(value):
        """Convierte datetime a Unix timestamp en milisegundos (hora local)."""
        import time
        return int(time.mktime(value.timetuple())) * 1000

    # Inyectar variables globales a todos los templates
    @app.context_processor
    def inject_globals():
        return {'now': datetime.now()}

    # Manejadores de error
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    return app


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
