"""
VibePlanner v2 - Blueprint de Calendario e Invitaciones (calendar_bp.py)
-------------------------------------------------------------------------
DUEÑO DE ESTE ARCHIVO: Jose Cabrera (Módulo C - Calendario e Invitaciones)

RUTAS:
    GET  /calendario                            -> Redirige al mes actual (YYYY/MM)
    GET  /calendario/<year>/<month>             -> Cuadrícula mensual (US11)
    GET  /eventos/nuevo                         -> Formulario de alta de evento
    POST /eventos/nuevo                         -> Procesa la creación
    GET  /eventos/<id>/editar                   -> Formulario de edición
    POST /eventos/<id>/editar                   -> Procesa la edición
    POST /eventos/<id>/eliminar                 -> Elimina evento propio
    POST /eventos/<id>/invitar                  -> Genera link de invitación
    GET  /invitacion/<token>                    -> Pantalla de aceptación (US12)
    POST /invitacion/<token>/aceptar            -> Procesa la aceptación del invitado
"""

import calendar
from datetime import datetime, timedelta

from flask import (Blueprint, abort, flash, jsonify, redirect, render_template,
                   request, session, url_for)

import config
import fechas
import repo_events
import security
import validators

calendar_bp = Blueprint("calendar_bp", __name__)

ALLOWED_COLORS = getattr(config, "ALLOWED_COLORS", ("#2F4156", "#567C8D", "#C8D9E6", "#D7707F", "#9DA3A4", "#4C4D53"))
DEFAULT_COLOR = "#567C8D"

# Lista blanca de estados. Tiene que coincidir con el CHECK de `events` en
# schema_v2.sql: si un valor de fuera llega al UPDATE, SQLite lanza
# IntegrityError y el usuario ve un 500 en vez de un mensaje.
ALLOWED_STATUS = ("tentativo", "confirmado", "cancelado")
DEFAULT_STATUS = "confirmado"

# El unico formato que entra a la base. Parsear con el rechaza '2026-13-45' y
# '25:99', y formatear con el garantiza que '2026-9-10' se guarde como
# '2026-09-10' -- si no, el evento desaparece de la cuadricula del mes.
FORMATO_FECHA_HORA = "%Y-%m-%d %H:%M"

# Los topes salen de validators.py, que es la fuente unica para los tres
# modulos. Antes el calendario no tenia ninguno.
TITULO_MAX = validators.TITULO_MAX
DESCRIPCION_MAX = validators.DESCRIPCION_MAX


def _current_local_year_month():
    # Hora de LIMA, no del servidor: PythonAnywhere corre en UTC y a partir de
    # las 19:00 hora local ya es "manana" para el. El 31 a las 19:01 este
    # calendario abria directamente en el mes siguiente.
    return fechas.anio_mes_local()


@calendar_bp.route("/calendario")
@security.requires("calendario.ver")
def index():
    year, month = _current_local_year_month()
    return redirect(url_for("calendar_bp.month_view", year=year, month=month))


@calendar_bp.route("/calendario/<int:year>/<int:month>")
@security.requires("calendario.ver")
def month_view(year, month):
    if month < 1 or month > 12 or year < 2000 or year > 2100:
        year, month = _current_local_year_month()
        return redirect(url_for("calendar_bp.month_view", year=year, month=month))

    user_id = security.current_user_id()
    events = repo_events.list_month(user_id, year, month)

    # Agrupar eventos por fecha ISO 'YYYY-MM-DD'
    events_by_date = {}
    for ev in events:
        date_key = ev["start_at"].split(" ")[0]
        events_by_date.setdefault(date_key, []).append(ev)

    # Cálculo del mes anterior y siguiente (Cruces de año TC-26)
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    # Generación de la cuadrícula mensual de 6 semanas (Lunes a Domingo)
    first_weekday, num_days = calendar.monthrange(year, month)  # 0=Lunes
    calendar.setfirstweekday(calendar.MONDAY)
    month_cal = calendar.monthcalendar(year, month)

    # Nombres de los meses en español
    meses_es = [
        "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    return render_template(
        "calendario/mes.html",
        year=year,
        month=month,
        month_name=meses_es[month],
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        month_cal=month_cal,
        events_by_date=events_by_date,
        allowed_colors=ALLOWED_COLORS,
        # Para marcar la celda de hoy. Se calcula aqui y no en la plantilla:
        # cero logica de negocio dentro de {{ }}. En hora de Lima, o despues de
        # las 19:00 se resaltaria la celda de manana.
        hoy=fechas.hoy_iso(),
        seccion_activa="calendario",
    )


def _validar_evento(form):
    """
    Valida el formulario de evento. La usan CREAR y EDITAR, las dos.

    Antes eran el mismo codigo copiado, y ahi nacieron dos defectos que solo
    tenia una de las copias. Con una funcion, arreglar uno arregla los dos.

    Lo importante es que las fechas se PARSEAN, no se comparan como cadenas.
    Con `start_date='abc'` la version anterior construia 'abc 09:00', la
    comparacion 'abc 10:00' <= 'abc 09:00' daba False -- asi que pasaba la
    validacion -- la fila SE GUARDABA, y el 500 llegaba despues, al hacer
    int('abc') para el redirect. El CHECK (end_at > start_at) del esquema
    tampoco frenaba nada, porque en SQLite tambien es comparacion de texto.

    Y fechas plausibles pero no canonicas ('2026-9-10') se guardaban tal cual:
    el evento desaparecia de los doce meses, porque el rango del mes compara
    contra 'YYYY-MM-DD'. Un evento bueno quedaba invisible al editarlo.

    Devuelve (datos, errores). `datos` trae start_at y end_at ya en forma
    canonica y un objeto datetime `inicio` para calcular el redirect sin
    volver a trocear cadenas.
    """
    errores = []

    title = (form.get("title") or "").strip()
    if not title:
        errores.append("El titulo del evento es obligatorio.")
    elif len(title) > TITULO_MAX:
        errores.append("El titulo no puede pasar de %d caracteres." % TITULO_MAX)

    description = (form.get("description") or "").strip()
    if len(description) > DESCRIPCION_MAX:
        errores.append("La descripcion no puede pasar de %d caracteres." % DESCRIPCION_MAX)

    start_date = (form.get("start_date") or "").strip()
    start_time = (form.get("start_time") or "09:00").strip()
    end_date = (form.get("end_date") or start_date).strip()
    end_time = (form.get("end_time") or "10:00").strip()

    inicio = _parsear(start_date, start_time, "fecha u hora de inicio", errores)
    fin = _parsear(end_date, end_time, "fecha u hora de fin", errores)

    if inicio and fin and fin <= inicio:
        errores.append("La hora de fin debe ser posterior a la de inicio.")

    # Color y estado: lo que no este en la lista blanca cae al valor por
    # defecto en silencio. No es un error del usuario -- el formulario solo
    # ofrece valores validos -- asi que solo puede venir de una manipulacion.
    color = (form.get("color") or DEFAULT_COLOR).strip()
    if color not in ALLOWED_COLORS:
        color = DEFAULT_COLOR

    status = (form.get("status") or DEFAULT_STATUS).strip()
    if status not in ALLOWED_STATUS:
        status = DEFAULT_STATUS

    if errores:
        return None, errores

    return {
        "title": title,
        "description": description,
        # Siempre la forma canonica que produce strptime, nunca la cadena que
        # escribio el navegador: asi la base solo recibe 'YYYY-MM-DD HH:MM'.
        "start_at": inicio.strftime(FORMATO_FECHA_HORA),
        "end_at": fin.strftime(FORMATO_FECHA_HORA),
        "color": color,
        "status": status,
        "inicio": inicio,
    }, []


def _parsear(fecha, hora, etiqueta, errores):
    """Convierte fecha + hora en datetime, o anota el error y devuelve None."""
    if not fecha:
        errores.append("Debes indicar la %s." % etiqueta)
        return None
    try:
        return datetime.strptime("%s %s" % (fecha, hora), FORMATO_FECHA_HORA)
    except ValueError:
        errores.append("La %s no es valida. Usa el selector del formulario." % etiqueta)
        return None


@calendar_bp.route("/eventos/nuevo", methods=["GET", "POST"])
@security.requires("evento.crear")
def create_event():
    user_id = security.current_user_id()

    if request.method == "POST":
        datos, errores = _validar_evento(request.form)

        if errores:
            for err in errores:
                flash(err, "error")
            # `form=request.form` conserva lo que la persona ya habia escrito.
            return render_template("calendario/evento_form.html",
                                   allowed_colors=ALLOWED_COLORS, form=request.form)

        inicio = datos.pop("inicio")
        repo_events.create(datos, user_id)
        flash("Evento creado.", "ok")
        return redirect(url_for("calendar_bp.month_view",
                                year=inicio.year, month=inicio.month))

    default_date = request.args.get("date", fechas.hoy_iso())
    return render_template("calendario/evento_form.html",
                           allowed_colors=ALLOWED_COLORS, default_date=default_date)


@calendar_bp.route("/eventos/<int:event_id>/editar", methods=["GET", "POST"])
@security.requires("evento.editar")
def edit_event(event_id):
    user_id = security.current_user_id()
    event = repo_events.get_owned(event_id, user_id)
    if not event:
        abort(404)

    if request.method == "POST":
        datos, errores = _validar_evento(request.form)

        if errores:
            for err in errores:
                flash(err, "error")
            # `form` ademas de `event`: sin el, un error borraba de la pantalla
            # todo lo que la persona acababa de teclear y la dejaba mirando los
            # valores viejos, sin entender que se habia perdido.
            return render_template("calendario/evento_form.html", event=event,
                                   allowed_colors=ALLOWED_COLORS, form=request.form)

        inicio = datos.pop("inicio")
        repo_events.update_owned(event_id, user_id, datos)
        flash("Evento actualizado.", "ok")
        return redirect(url_for("calendar_bp.month_view",
                                year=inicio.year, month=inicio.month))

    return render_template("calendario/evento_form.html", event=event,
                           allowed_colors=ALLOWED_COLORS)


@calendar_bp.route("/eventos/<int:event_id>/eliminar", methods=["POST"])
@security.requires("evento.eliminar")
def delete_event(event_id):
    user_id = security.current_user_id()

    # Misma regla que editar e invitar: si no es tuyo, 404. Antes esta ruta
    # respondia 302 con un flash, asi que un evento ajeno y un evento
    # inexistente se distinguian del propio por el comportamiento.
    if repo_events.get_owned(event_id, user_id) is None:
        abort(404)

    repo_events.delete_owned(event_id, user_id)
    flash("Evento eliminado.", "ok")
    year, month = _current_local_year_month()
    return redirect(url_for("calendar_bp.month_view", year=year, month=month))


@calendar_bp.route("/eventos/<int:event_id>/invitar", methods=["POST"])
@security.requires("evento.editar")
def generate_invite_link(event_id):
    """Invitar es gestionar TU evento: por eso pide `evento.editar`."""
    user_id = security.current_user_id()
    event = repo_events.get_owned(event_id, user_id)
    if not event:
        # 404, no 403. Un 403 confirmaria que ese evento existe y permitiria
        # recorrer los ids ajenos preguntando uno por uno. Para quien pregunta,
        # lo que no es suyo simplemente no existe.
        return jsonify({"error": "No encontrado"}), 404

    token = repo_events.create_invitation(event_id)
    invite_url = url_for("calendar_bp.view_invitation", token=token, _external=True)
    return jsonify({"token": token, "invite_url": invite_url})


@calendar_bp.route("/invitacion/<token>")
@security.requires("invitacion.responder")
def view_invitation(token):
    # @requires aplica @login_required por dentro, asi que TC-31 sigue en pie:
    # el decorador guarda session["next"] y auth.login devuelve aqui despues
    # de entrar. No hay que reimplementar nada de eso.
    invitation = repo_events.get_event_by_token(token)
    if not invitation:
        # TC-30: Token inválido no revela nada del evento ni del anfitrión
        return render_template("calendario/invitacion.html", error="Esta invitación no es válida o fue cancelada.")

    user_id = security.current_user_id()
    attendees_count = repo_events.count_attendees(invitation["event_id"])
    return render_template(
        "calendario/invitacion.html",
        invitation=invitation,
        attendees_count=attendees_count,
        token=token
    )


@calendar_bp.route("/invitacion/<token>/aceptar", methods=["POST"])
@security.requires("invitacion.responder")
def accept_invitation(token):
    user_id = security.current_user_id()
    invitation = repo_events.get_event_by_token(token)
    if not invitation:
        flash("La invitación no es válida.", "error")
        return redirect(url_for("calendar_bp.index"))

    success = repo_events.accept_invitation(token, user_id)
    if success:
        flash("¡Has aceptado la invitación al evento!", "ok")
        start_date = invitation["start_at"].split(" ")[0]
        year, month = int(start_date.split("-")[0]), int(start_date.split("-")[1])
        return redirect(url_for("calendar_bp.month_view", year=year, month=month))
    else:
        flash("No se pudo procesar la invitación.", "error")
        return redirect(url_for("calendar_bp.index"))
