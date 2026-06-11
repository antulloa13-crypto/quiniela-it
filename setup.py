# -*- coding: utf-8 -*-
"""
Script de inicializacion y datos de ejemplo.
Ejecutar UNA SOLA VEZ antes de iniciar la aplicacion:

    python setup.py

Crea tablas, usuario administrador y datos de prueba.
"""
import os
import sys
from datetime import datetime, timedelta

# Forzar UTF-8 en la salida de consola (Windows)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app import app
from extensions import db
from models import User, Partido, Pronostico, Resultado, Puntuacion
from utils import calcular_puntuaciones


def init_db():
    with app.app_context():
        print("Creando tablas en la base de datos...")
        db.create_all()

        # Verificar si ya existe el admin
        if User.query.filter_by(username='admin').first():
            print("La base de datos ya tiene datos. Abortando para no duplicar.")
            print("Si deseas reiniciar, elimina el archivo instance/quiniela.db primero.")
            return

        # --- Crear administrador ---
        admin = User(
            username='admin',
            nombre='Administrador',
            apellido='Sistema',
            rol='admin',
            activo=True,
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("  [OK] Administrador creado: admin / admin123")

        # --- Crear participantes de ejemplo ---
        participantes_data = [
            ('Juan',   'Perez',   'Juan_Perez',   'perez123'),
            ('Maria',  'Lopez',   'Maria_Lopez',  'lopez123'),
            ('Carlos', 'Mejia',   'Carlos_Mejia', 'mejia123'),
            ('Ana',    'Torres',  'Ana_Torres',   'torres123'),
            ('Luis',   'Ramirez', 'Luis_Ramirez', 'ramirez123'),
        ]
        participantes = []
        for nombre, apellido, username, pwd in participantes_data:
            u = User(nombre=nombre, apellido=apellido, username=username, rol='participante')
            u.set_password(pwd)
            db.session.add(u)
            participantes.append(u)
            print(f"  [OK] Participante: {username} / {pwd}")

        db.session.flush()

        # Crear puntuaciones iniciales para cada participante
        for p in participantes:
            db.session.add(Puntuacion(usuario_id=p.id))

        # --- Crear partidos de ejemplo ---
        ahora = datetime.now()

        partidos_data = [
            # Futuros (disponibles para pronosticar)
            ('Barcelona',       'Real Madrid',  ahora + timedelta(days=1, hours=2),      'pendiente'),
            ('Manchester City',  'Chelsea',      ahora + timedelta(days=2, hours=4),      'pendiente'),
            ('Bayern Munich',    'Dortmund',     ahora + timedelta(days=3),               'pendiente'),
            ('PSG',              'Marseille',    ahora + timedelta(hours=36),             'pendiente'),
            # Muy proximo (menos de 2 horas)
            ('Atletico Madrid',  'Sevilla',      ahora + timedelta(hours=1, minutes=30),  'pendiente'),
            # Finalizados con resultado
            ('Brasil',           'Argentina',    ahora - timedelta(days=3),               'finalizado'),
            ('Mexico',           'Colombia',     ahora - timedelta(days=5),               'finalizado'),
            ('Uruguay',          'Chile',        ahora - timedelta(days=7),               'finalizado'),
            # En curso (sin resultado aun)
            ('Italia',           'Francia',      ahora - timedelta(hours=1),              'en_juego'),
        ]

        partidos = []
        for ea, eb, fh, estado in partidos_data:
            partido = Partido(equipo_a=ea, equipo_b=eb, fecha_hora=fh, estado=estado)
            db.session.add(partido)
            partidos.append(partido)
        db.session.flush()
        print(f"  [OK] {len(partidos)} partidos creados")

        # --- Registrar resultados para partidos finalizados ---
        resultados_data = [
            (partidos[5], 'equipo_a'),   # Brasil gana
            (partidos[6], 'empate'),     # Mexico - Colombia empate
            (partidos[7], 'equipo_b'),   # Chile gana
        ]
        for partido, res in resultados_data:
            db.session.add(Resultado(partido_id=partido.id, resultado=res))
        print(f"  [OK] {len(resultados_data)} resultados registrados")

        # --- Crear pronosticos de ejemplo ---
        import random
        random.seed(42)
        opciones = ['equipo_a', 'empate', 'equipo_b']

        count = 0
        for participante in participantes:
            for partido in partidos:
                # Pronosticar partidos futuros y finalizados (no el en_juego que esta bloqueado)
                if partido.estado in ('pendiente', 'finalizado'):
                    opcion = random.choice(opciones)
                    db.session.add(Pronostico(
                        usuario_id=participante.id,
                        partido_id=partido.id,
                        pronostico=opcion,
                    ))
                    count += 1
        print(f"  [OK] {count} pronosticos de ejemplo creados")

        db.session.commit()

        # Calcular puntuaciones iniciales
        calcular_puntuaciones()
        print("  [OK] Puntuaciones calculadas")

        print("")
        print("=" * 55)
        print("  BASE DE DATOS INICIALIZADA CORRECTAMENTE")
        print("=" * 55)
        print("")
        print("  Credenciales de acceso:")
        print("  +-------------------------------------------+")
        print("  | ADMIN:  admin          / admin123         |")
        print("  | USER:   Juan_Perez     / perez123         |")
        print("  | USER:   Maria_Lopez    / lopez123         |")
        print("  | USER:   Carlos_Mejia   / mejia123         |")
        print("  | USER:   Ana_Torres     / torres123        |")
        print("  | USER:   Luis_Ramirez   / ramirez123       |")
        print("  +-------------------------------------------+")
        print("")
        print("  Inicia el servidor con: python app.py")
        print("  Abre en tu navegador:   http://localhost:5000")
        print("")


if __name__ == '__main__':
    init_db()
