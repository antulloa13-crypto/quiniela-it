"""
Rutas de autenticación: login, registro y logout.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Puntuacion

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.es_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('participant.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.es_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('participant.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Ingresa tu usuario y contraseña.', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Usuario o contraseña incorrectos.', 'danger')
            return render_template('login.html')

        if not user.activo:
            flash('Tu cuenta está desactivada. Contacta al administrador.', 'warning')
            return render_template('login.html')

        login_user(user, remember=False)
        flash(f'¡Bienvenido, {user.nombre}!', 'success')

        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)

        if user.es_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('participant.dashboard'))

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.es_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('participant.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        password = request.form.get('password', '').strip()
        password2 = request.form.get('password2', '').strip()

        errors = []
        if not all([username, nombre, apellido, password, password2]):
            errors.append('Completá todos los campos.')
        elif password != password2:
            errors.append('Las contraseñas no coinciden.')
        elif len(password) < 6:
            errors.append('La contraseña debe tener al menos 6 caracteres.')

        if not errors and User.query.filter_by(username=username).first():
            errors.append('Ese nombre de usuario ya está en uso.')

        if errors:
            for msg in errors:
                flash(msg, 'danger')
            return render_template('login.html', active_tab='register')

        user = User(username=username, nombre=nombre, apellido=apellido)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        db.session.add(Puntuacion(usuario_id=user.id))
        db.session.commit()

        flash('¡Cuenta creada correctamente! Ya podés iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('login.html', active_tab='register')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))
