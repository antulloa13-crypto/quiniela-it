"""
Punto de entrada WSGI para IIS / wfastcgi.
IIS referencia este archivo via WSGI_HANDLER=wsgi.app en web.config.
"""
import os
os.environ.setdefault('FLASK_CONFIG', 'production')

from app import app  # noqa: E402  (create_app() se llama al importar)
