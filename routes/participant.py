"""
Rutas del panel del participante.
Gestión de pronósticos y visualización de ranking.
"""
from functools import wraps
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user

from models import Partido, Pronostico, Resultado, Puntuacion
from extensions import db
from utils import get_ranking

participant_bp = Blueprint('participant', __name__)

# Etiquetas legibles para cada valor de pronóstico/resultado
LABELS = {
    'equipo_a': lambda p: p.equipo_a,
    'empate': lambda p: 'Empate',
    'equipo_b': lambda p: p.equipo_b,
}


def participant_required(f):
    """Decorador que exige rol participante y cuenta activa."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.es_admin:
            return redirect(url_for('admin.dashboard'))
        if not current_user.activo:
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'warning')
            return redirect(url_for('auth.logout'))
        return f(*args, **kwargs)
    return decorated


@participant_bp.route('/dashboard')
@participant_required
def dashboard():
    ahora = datetime.now()

    # Partidos futuros (disponibles para pronosticar), ordenados por proximidad
    proximos = (
        Partido.query
        .filter(Partido.fecha_hora > ahora)
        .order_by(Partido.fecha_hora.asc())
        .all()
    )

    # Partidos iniciados pero sin resultado registrado aún
    en_curso = (
        Partido.query
        .filter(Partido.fecha_hora <= ahora)
        .outerjoin(Resultado, Partido.id == Resultado.partido_id)
        .filter(Resultado.id.is_(None))
        .order_by(Partido.fecha_hora.desc())
        .all()
    )

    # Partidos con resultado registrado (últimos 15)
    finalizados = (
        Partido.query
        .join(Resultado, Partido.id == Resultado.partido_id)
        .order_by(Partido.fecha_hora.desc())
        .limit(15)
        .all()
    )

    # Mapa partido_id → Pronostico del usuario actual
    mis_pronosticos = {
        p.partido_id: p
        for p in Pronostico.query.filter_by(usuario_id=current_user.id).all()
    }

    puntuacion = Puntuacion.query.filter_by(usuario_id=current_user.id).first()

    return render_template(
        'participant/dashboard.html',
        proximos=proximos,
        en_curso=en_curso,
        finalizados=finalizados,
        mis_pronosticos=mis_pronosticos,
        puntuacion=puntuacion,
        ahora=ahora,
        labels=LABELS,
    )


@participant_bp.route('/pronostico/<int:partido_id>', methods=['POST'])
@participant_required
def guardar_pronostico(partido_id):
    partido = Partido.query.get_or_404(partido_id)

    # Verificar bloqueo por tiempo
    if partido.esta_bloqueado:
        return jsonify({
            'success': False,
            'message': 'El partido ya comenzó. No se pueden modificar pronósticos.'
        }), 403

    pronostico_val = request.form.get('pronostico', '').strip()
    if pronostico_val not in ('equipo_a', 'empate', 'equipo_b'):
        return jsonify({'success': False, 'message': 'Valor de pronóstico inválido.'}), 400

    # Crear o actualizar pronóstico
    pronostico = Pronostico.query.filter_by(
        usuario_id=current_user.id,
        partido_id=partido_id
    ).first()

    if pronostico is None:
        pronostico = Pronostico(
            usuario_id=current_user.id,
            partido_id=partido_id,
            pronostico=pronostico_val,
        )
        db.session.add(pronostico)
    else:
        pronostico.pronostico = pronostico_val
        pronostico.fecha_registro = datetime.now()

    db.session.commit()

    label = LABELS[pronostico_val](partido)
    return jsonify({
        'success': True,
        'message': f'Pronóstico guardado: {label}',
        'pronostico': pronostico_val,
        'label': label,
    })


@participant_bp.route('/ranking')
@login_required
def ranking():
    data = get_ranking()
    return render_template('ranking.html', ranking=data, is_admin=False)
