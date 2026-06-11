# Quiniela Deportiva

Aplicación web para administrar una quiniela deportiva. Desarrollada con Flask (Python), SQLite, Bootstrap 5 y JavaScript vanilla.

## Características

- **Autenticación** con usuario y contraseña (hashes seguros con Werkzeug)
- **Roles**: Administrador y Participante
- **Gestión de partidos**: crear, editar, eliminar, actualizar estado
- **Pronósticos**: bloqueo automático al llegar la hora de inicio del partido
- **Countdown en tiempo real** para cada partido
- **Registro de resultados**: calcula puntuaciones automáticamente
- **Ranking con desempate** por racha, aciertos y orden alfabético
- **Rachas**: racha actual y mejor racha histórica por participante
- **Protección CSRF** en todos los formularios
- **Diseño responsive** con Bootstrap 5
- **Fácil migración** a MySQL o PostgreSQL

## Requisitos

- Python 3.8 o superior
- pip

## Instalación rápida

```bash
# 1. Ir al directorio del proyecto
cd quiniela

# 2. (Recomendado) Crear entorno virtual
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar la base de datos con datos de ejemplo
python setup.py

# 5. Iniciar el servidor
python app.py
```

Abre en tu navegador: **http://localhost:5000**

## Credenciales de acceso (datos de ejemplo)

| Rol           | Usuario        | Contraseña  |
|---------------|----------------|-------------|
| Administrador | `admin`        | `admin123`  |
| Participante  | `Juan_Perez`   | `perez123`  |
| Participante  | `Maria_Lopez`  | `lopez123`  |
| Participante  | `Carlos_Mejia` | `mejia123`  |
| Participante  | `Ana_Torres`   | `torres123` |
| Participante  | `Luis_Ramirez` | `ramirez123`|

> **Importante:** Cambia la contraseña del administrador antes de poner en producción.

## Estructura del proyecto

```
quiniela/
├── app.py                  # Punto de entrada, factory de la app
├── config.py               # Configuración (SQLite / MySQL / PostgreSQL)
├── extensions.py           # Instancias de extensiones Flask
├── models.py               # Modelos de base de datos (SQLAlchemy)
├── utils.py                # Cálculo de puntuaciones y ranking
├── requirements.txt        # Dependencias Python
├── setup.py                # Script de inicialización y datos de ejemplo
├── routes/
│   ├── auth.py             # Login / logout
│   ├── admin.py            # Panel de administración
│   └── participant.py      # Panel del participante
├── templates/
│   ├── base.html           # Plantilla base con navbar
│   ├── login.html          # Pantalla de inicio de sesión
│   ├── ranking.html        # Tabla de posiciones (compartida)
│   ├── admin/              # Vistas del administrador
│   │   ├── dashboard.html
│   │   ├── partidos.html
│   │   ├── partido_form.html
│   │   ├── participantes.html
│   │   ├── participante_form.html
│   │   └── resultados.html
│   ├── participant/
│   │   └── dashboard.html  # Pronósticos del participante
│   └── errors/
│       ├── 403.html
│       └── 404.html
├── static/
│   ├── css/style.css       # Estilos personalizados
│   └── js/main.js          # JavaScript (contadores, AJAX, UI)
└── instance/
    └── quiniela.db         # Base de datos SQLite (se crea automáticamente)
```

## Migracion a MySQL

1. Instalar PyMySQL:
   ```bash
   pip install PyMySQL
   ```

2. Establecer la variable de entorno `DATABASE_URL`:
   ```bash
   # Windows
   set DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost:3306/quiniela

   # macOS / Linux
   export DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost:3306/quiniela
   ```

3. Crear la base de datos `quiniela` en MySQL, luego ejecutar `python setup.py`.

## Migración a PostgreSQL

1. Instalar psycopg2:
   ```bash
   pip install psycopg2-binary
   ```

2. Establecer `DATABASE_URL`:
   ```bash
   export DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/quiniela
   ```

3. Ejecutar `python setup.py`.

## Variables de entorno

| Variable       | Descripción                                         | Valor por defecto          |
|----------------|-----------------------------------------------------|----------------------------|
| `DATABASE_URL` | URL de conexión a la base de datos                  | SQLite en `instance/`      |
| `SECRET_KEY`   | Clave secreta para sesiones y CSRF                  | Valor de desarrollo (CAMBIAR) |
| `FLASK_CONFIG` | Perfil de configuración: `development`/`production` | `development`              |

## Seguridad en producción

- Cambia `SECRET_KEY` por una cadena aleatoria larga
- Usa HTTPS (con nginx o un proxy inverso)
- Cambia las contraseñas de todos los usuarios de ejemplo
- Considera usar PostgreSQL o MySQL en lugar de SQLite

## Solución de problemas

**Error: `ModuleNotFoundError: No module named 'flask'`**
→ Asegúrate de activar el entorno virtual e instalar dependencias: `pip install -r requirements.txt`

**Error: `sqlite3.OperationalError: no such table`**
→ Ejecuta `python setup.py` para crear las tablas.

**La base de datos ya existe y quiero reiniciar:**
→ Elimina el archivo `instance/quiniela.db` y ejecuta `python setup.py` nuevamente.
