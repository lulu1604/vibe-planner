"""
VibePlanner v2 - Blueprint de Hábitos y Métricas (habits.py)
------------------------------------------------------------------------
DUEÑA DE ESTE ARCHIVO: Ana Cusi (Módulo D - Hábitos, Métricas y Design System)

RUTAS QUE EXPONE:
    GET  /habitos                      -> lista de hábitos con racha (US13)
    POST /habitos                      -> crea un hábito
    POST /habitos/<id>/registro        -> marca o corrige el día de hoy
    GET  /metricas                     -> métricas propias (US14)
    GET  /admin/metricas               -> métricas del sistema (US15)

⚠️ EL NOMBRE DEL BLUEPRINT Y DE LAS VISTAS NO ES NEGOCIABLE.
`home.py` tiene reservadas las entradas del menú con los endpoints
`habitos.lista` y `habitos.metricas`. Si este blueprint se llamara `habits`, o
la vista `index` en vez de `lista`, `url_for` lanzaría BuildError, `home.py` lo
atraparía en `_url_o_none` y las dos entradas del menú aparecerían apagadas como
"Próximamente" PARA SIEMPRE, sin un solo error en consola. Quien venga después:
no las renombres.
"""

import math
from datetime import date, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import metrics
import repo_habits
import security

habitos = Blueprint("habitos", __name__)

# Orden de presentación de los grupos. No es el alfabético del repositorio: se
# empieza por el sueño porque es el hábito que sostiene a los demás.
ORDEN_TIPOS = ("sueno", "ejercicio", "dieta", "relajacion", "general")

# El valor se guarda sin tilde (evita problemas de codificación en la base) y se
# muestra con ella. La traducción vive aquí, no en la plantilla.
ETIQUETA_TIPO = {
    "sueno": "Sueño",
    "ejercicio": "Ejercicio",
    "dieta": "Dieta",
    "relajacion": "Relajación",
    "general": "General",
}

ETIQUETA_UNIDAD = {
    "horas": "horas",
    "minutos": "minutos",
    "vasos": "vasos",
    "veces": "veces",
    "vez": "vez",
}

DIAS_TIRA = 7

INICIAL_DIA = ("L", "M", "X", "J", "V", "S", "D")
NOMBRE_DIA = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
NOMBRE_MES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
              "agosto", "septiembre", "octubre", "noviembre", "diciembre")


def _meta_legible(habito):
    """
    "8 horas" en vez de target_value=8.0, unit='horas'.

    El usuario no lee nombres de columna: la traducción a lenguaje humano se
    hace aquí, donde se puede probar, y no dentro de un {{ }} de la plantilla.
    """
    meta = habito["target_value"] or 0
    if float(meta).is_integer():
        meta = int(meta)
    unidad = ETIQUETA_UNIDAD.get(habito["unit"], habito["unit"] or "vez")
    return "%s %s" % (meta, unidad)


def _tira_semana(cumplidos, hoy):
    """
    Los últimos 7 días como casillas, de más antiguo a hoy.

    Cada casilla lleva su `aria-label` completo ("Lunes 11 de agosto:
    cumplido"): la inicial sola no le dice nada a quien usa lector de pantalla.
    """
    casillas = []
    for atras in range(DIAS_TIRA - 1, -1, -1):
        dia = hoy - timedelta(days=atras)
        iso = dia.isoformat()
        cumplido = iso in cumplidos
        casillas.append({
            "fecha": iso,
            "inicial": INICIAL_DIA[dia.weekday()],
            "cumplido": cumplido,
            "es_hoy": atras == 0,
            "aria": "%s %d de %s: %s" % (
                NOMBRE_DIA[dia.weekday()], dia.day, NOMBRE_MES[dia.month - 1],
                "cumplido" if cumplido else "sin marcar",
            ),
        })
    return casillas


def _agrupar(habitos_usuario, registros_hoy, registros_ventana, hoy_iso):
    """
    Prepara los grupos que pinta la plantilla, ya con racha y tira de días.

    Todo el cálculo se hace aquí a propósito: la plantilla solo recorre listas.
    Llamar a `metrics.habit_streak` dentro del bucle de Jinja sería una consulta
    por hábito (N+1) además de lógica de negocio en el HTML.
    """
    hoy = date.fromisoformat(hoy_iso)
    por_tipo = {}

    for habito in habitos_usuario:
        filas = registros_ventana.get(habito["id"], [])
        cumplidos = {f["log_date"] for f in filas if f["done"]}
        registro_hoy = registros_hoy.get(habito["id"])

        tarjeta = dict(habito)
        tarjeta["meta_legible"] = _meta_legible(habito)
        tarjeta["tipo_etiqueta"] = ETIQUETA_TIPO.get(habito["habit_type"], "General")
        tarjeta["racha"] = metrics.racha_desde_logs(cumplidos, hoy_iso)
        tarjeta["marcado_hoy"] = bool(registro_hoy and registro_hoy["done"])
        tarjeta["valor_hoy"] = registro_hoy["value"] if registro_hoy else habito["target_value"]
        tarjeta["semana"] = _tira_semana(cumplidos, hoy)
        por_tipo.setdefault(habito["habit_type"], []).append(tarjeta)

    # Los grupos vacíos no se pintan: un encabezado "Dieta" sobre la nada solo
    # ocupa pantalla.
    return [
        {"tipo": tipo, "etiqueta": ETIQUETA_TIPO[tipo], "habitos": por_tipo[tipo]}
        for tipo in ORDEN_TIPOS if tipo in por_tipo
    ]


@habitos.route("/habitos")
@security.requires("habito.ver")
def lista():
    """
    La pantalla de hábitos: exactamente TRES consultas, no una por hábito.

    La tercera cubre a la vez la tira de siete días y el cálculo de las rachas,
    porque la ventana de la racha ya contiene a la de la semana.
    """
    user_id = security.current_user_id()
    hoy = metrics.hoy_iso()
    desde = (date.fromisoformat(hoy) - timedelta(days=metrics.VENTANA_RACHA)).isoformat()

    habitos_usuario = repo_habits.list_by_user(user_id)                    # 1
    registros_hoy = repo_habits.logs_of_day_by_user(user_id, hoy)          # 2
    registros_ventana = repo_habits.logs_range_by_user(user_id, desde, hoy)  # 3

    grupos = _agrupar(habitos_usuario, registros_hoy, registros_ventana, hoy)

    return render_template(
        "habitos/lista.html",
        grupos=grupos,
        total_habitos=len(habitos_usuario),
        hoy=hoy,
        tipos=[(codigo, ETIQUETA_TIPO[codigo]) for codigo in ORDEN_TIPOS],
        unidades=list(ETIQUETA_UNIDAD.keys()),
    )


@habitos.route("/habitos", methods=["POST"])
@security.requires("habito.crear")
def crear():
    """
    Crea un hábito. El `user_id` sale de la sesión, jamás del formulario: si
    viniera de un campo oculto, cualquiera podría crear hábitos a nombre de otro.
    """
    user_id = security.current_user_id()
    datos = {
        "name": request.form.get("name", ""),
        "habit_type": request.form.get("habit_type", "general"),
        "target_value": request.form.get("target_value", 1),
        "unit": request.form.get("unit", "vez"),
    }

    try:
        repo_habits.create(datos, user_id)
    except ValueError as error:
        # El mensaje de ValueError ya está redactado para leerse tal cual.
        flash(str(error), "error")
        return redirect(url_for("habitos.lista"))

    flash("Hábito creado. Márcalo hoy para empezar la racha.", "ok")
    return redirect(url_for("habitos.lista"))


@habitos.route("/habitos/<int:habit_id>/registro", methods=["POST"])
@security.requires("habito.registrar")
def registrar(habit_id):
    """
    Marca o corrige el día de hoy.

    La regla de las dos llaves: el decorador comprueba el PERMISO y aquí se
    comprueba la PROPIEDAD. Si el hábito no es suyo -> 404, nunca 403: un 403
    confirmaría que ese id existe y es de otra persona.
    """
    user_id = security.current_user_id()
    if repo_habits.get_owned(habit_id, user_id) is None:
        abort(404)

    hoy = metrics.hoy_iso()
    marcar = request.form.get("done") == "1"

    try:
        valor = float(request.form.get("value", 0) or 0)
    except ValueError:
        flash("El valor del día debe ser un número. Por ejemplo: 8.", "error")
        return redirect(url_for("habitos.lista"))

    # 'nan' e 'inf' pasan por float() sin protestar, y NaN atraviesa las dos
    # comparaciones de rango de abajo porque cualquier comparación con NaN es
    # False. Terminaba guardado como NULL y la plantilla imprimía value="None".
    if not math.isfinite(valor):
        flash("El valor del día debe ser un número. Por ejemplo: 8.", "error")
        return redirect(url_for("habitos.lista"))

    # El rango se valida igual que la meta en repo_habits._validar. Sin esto,
    # `value=-5` o `value=999999` entraban tal cual: la tira de la semana y las
    # métricas mostrarían un número imposible que el usuario no puede corregir
    # desde ninguna pantalla.
    if valor < 0 or valor > repo_habits.META_MAXIMA:
        flash(
            "El valor del día debe estar entre 0 y %d. Revisa la unidad: "
            "quizá querías minutos y no horas." % repo_habits.META_MAXIMA,
            "error",
        )
        return redirect(url_for("habitos.lista"))

    # Corregir el valor de hoy actualiza la fila existente gracias al UNIQUE
    # (habit_id, log_date): nunca crea una segunda (TC-34).
    repo_habits.upsert_log(habit_id, hoy, valor, marcar)

    flash("Marcado de hoy actualizado." if marcar else "Registro de hoy desmarcado.", "ok")
    return redirect(url_for("habitos.lista"))


@habitos.route("/metricas")
@security.requires("metrica.propia.ver")
def metricas():
    """
    "¿Cómo me fue hoy?" -- ver D5.

    La fecha se valida aquí y no se confía a la plantilla: una fecha inválida
    cae a hoy con un aviso, no a un 400 que deja al usuario sin pantalla.
    """
    user_id = security.current_user_id()
    hoy = metrics.hoy_iso()
    pedida = request.args.get("fecha")

    fecha = hoy
    if pedida:
        try:
            elegida = date.fromisoformat(pedida)
        except ValueError:
            flash("Esa fecha no se entiende. Te muestro la de hoy.", "error")
            elegida = None
        if elegida is not None:
            # El futuro no tiene métricas que enseñar: se recorta a hoy.
            fecha = min(elegida.isoformat(), hoy)

    resumen = metrics.daily_summary(user_id, fecha)
    actual = date.fromisoformat(fecha)

    return render_template(
        "habitos/metricas.html",
        resumen=resumen,
        fecha=fecha,
        es_hoy=(fecha == hoy),
        dia_anterior=(actual - timedelta(days=1)).isoformat(),
        dia_siguiente=(actual + timedelta(days=1)).isoformat(),
        fecha_legible="%d de %s de %d" % (actual.day, NOMBRE_MES[actual.month - 1], actual.year),
    )


@habitos.route("/admin/metricas")
@security.requires("metrica.sistema.ver")
def metricas_sistema():
    """
    Métricas agregadas de todo el sistema (US15).

    Vive en el blueprint `habitos` y no en `admin` aunque su URL empiece por
    /admin: el blueprint `admin` es de Piero y tiene url_prefix="/admin".
    Meter aquí una ruta suya obligaría a coordinar dos dueños sobre el mismo
    archivo.
    """
    return render_template("habitos/metricas_sistema.html",
                           metricas=metrics.system_metrics())
