"""
Funciones utilitarias: cálculo de puntuaciones, rachas y ranking.
"""
from models import User, Partido, Pronostico, Resultado, Puntuacion
from extensions import db


def calcular_puntuaciones():
    """
    Recalcula todas las puntuaciones, aciertos, fallos y rachas
    para cada participante activo.

    Se ejecuta cada vez que el admin registra un resultado.
    Las rachas se calculan en orden cronológico de fecha_hora del partido.
    """
    participantes = User.query.filter_by(rol='participante', activo=True).all()

    # Resultados ordenados cronológicamente por fecha del partido
    resultados = (
        Resultado.query
        .join(Partido, Resultado.partido_id == Partido.id)
        .order_by(Partido.fecha_hora.asc())
        .all()
    )

    for participante in participantes:
        puntos = 0
        total_aciertos = 0
        total_fallos = 0
        racha_actual = 0
        mejor_racha = 0

        for resultado in resultados:
            pronostico = Pronostico.query.filter_by(
                usuario_id=participante.id,
                partido_id=resultado.partido_id
            ).first()

            if pronostico is not None:
                if pronostico.pronostico == resultado.resultado:
                    puntos += 1
                    total_aciertos += 1
                    racha_actual += 1
                    if racha_actual > mejor_racha:
                        mejor_racha = racha_actual
                else:
                    total_fallos += 1
                    racha_actual = 0
            # Sin pronóstico: no suma ni resta, pero sí rompe la racha
            # (depende de la regla del negocio — aquí NO rompe racha si no pronosticó)

        # Crear o actualizar registro de puntuación
        p = Puntuacion.query.filter_by(usuario_id=participante.id).first()
        if p is None:
            p = Puntuacion(usuario_id=participante.id)
            db.session.add(p)

        p.puntos = puntos
        p.total_aciertos = total_aciertos
        p.total_fallos = total_fallos
        p.racha_actual = racha_actual
        p.mejor_racha = mejor_racha

    db.session.commit()


def get_ranking():
    """
    Retorna lista ordenada de participantes con sus estadísticas.

    Orden de desempate:
      1. Mayor cantidad de puntos (desc)
      2. Mejor racha histórica de aciertos (desc)
      3. Mayor cantidad de aciertos totales (desc)
      4. Orden alfabético por username (asc)
    """
    participantes = User.query.filter_by(rol='participante', activo=True).all()
    ranking = []

    for user in participantes:
        p = user.puntuacion
        ranking.append({
            'usuario': user,
            'puntos': p.puntos if p else 0,
            'total_aciertos': p.total_aciertos if p else 0,
            'total_fallos': p.total_fallos if p else 0,
            'racha_actual': p.racha_actual if p else 0,
            'mejor_racha': p.mejor_racha if p else 0,
        })

    ranking.sort(key=lambda x: (
        -x['puntos'],
        -x['mejor_racha'],
        -x['total_aciertos'],
        x['usuario'].username.lower()
    ))

    return ranking
