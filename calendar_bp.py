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
import repo_events
import security

calendar_bp = Blueprint("calendar_bp", __name__)

ALLOWED_COLORS = getattr(config, "ALLOWED_COLORS", ("#2F4156", "#567C8D", "#C8D9E6", "#D7707F", "#9DA3A4", "#4C4D53"))


def _current_local_year_month():
    now = datetime.now()
    return now.year, now.month


@calendar_bp.route("/calendario")
@security.login_required
def index():
    year, month = _current_local_year_month()
    return redirect(url_for("calendar_bp.month_view", year=year, month=month))


@calendar_bp.route("/calendario/<int:year>/<int:month>")
@security.login_required
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
        allowed_colors=ALLOWED_COLORS
    )


@calendar_bp.route("/eventos/nuevo", methods=["GET", "POST"])
@security.login_required
def create_event():
    user_id = security.current_user_id()

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        start_date = (request.form.get("start_date") or "").strip()
        start_time = (request.form.get("start_time") or "09:00").strip()
        end_date = (request.form.get("end_date") or start_date).strip()
        end_time = (request.form.get("end_time") or "10:00").strip()
        color = (request.form.get("color") or "#567C8D").strip()

        start_at = f"{start_date} {start_time}"
        end_at = f"{end_date} {end_time}"

        # Validaciones de servidor
        errores = []
        if not title:
            errores.append("El título del evento es obligatorio.")
        if not start_date or not end_date:
            errores.append("Debes especificar las fechas de inicio y fin.")
        if end_at <= start_at:
            errores.append("La hora de fin debe ser posterior a la de inicio.")
        if color not in ALLOWED_COLORS:
            color = "#567C8D"

        if errores:
            for err in errores:
                flash(err, "error")
            return render_template("calendario/evento_form.html", allowed_colors=ALLOWED_COLORS, form=request.form)

        data = {
            "title": title,
            "description": description,
            "start_at": start_at,
            "end_at": end_at,
            "color": color,
            "status": "confirmado"
        }
        event_id = repo_events.create(data, user_id)
        flash("Evento creado exitosamente.", "ok")

        year = int(start_date.split("-")[0])
        month = int(start_date.split("-")[1])
        return redirect(url_for("calendar_bp.month_view", year=year, month=month))

    default_date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    return render_template("calendario/evento_form.html", allowed_colors=ALLOWED_COLORS, default_date=default_date)


@calendar_bp.route("/eventos/<int:event_id>/editar", methods=["GET", "POST"])
@security.login_required
def edit_event(event_id):
    user_id = security.current_user_id()
    event = repo_events.get_owned(event_id, user_id)
    if not event:
        abort(404)

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        start_date = (request.form.get("start_date") or "").strip()
        start_time = (request.form.get("start_time") or "09:00").strip()
        end_date = (request.form.get("end_date") or start_date).strip()
        end_time = (request.form.get("end_time") or "10:00").strip()
        color = (request.form.get("color") or "#567C8D").strip()

        start_at = f"{start_date} {start_time}"
        end_at = f"{end_date} {end_time}"

        if end_at <= start_at:
            flash("La hora de fin debe ser posterior a la de inicio.", "error")
            return render_template("calendario/evento_form.html", event=event, allowed_colors=ALLOWED_COLORS)

        if color not in ALLOWED_COLORS:
            color = "#567C8D"

        data = {
            "title": title,
            "description": description,
            "start_at": start_at,
            "end_at": end_at,
            "color": color,
            "status": request.form.get("status", "confirmado")
        }
        repo_events.update_owned(event_id, user_id, data)
        flash("Evento actualizado.", "ok")
        year = int(start_date.split("-")[0])
        month = int(start_date.split("-")[1])
        return redirect(url_for("calendar_bp.month_view", year=year, month=month))

    return render_template("calendario/evento_form.html", event=event, allowed_colors=ALLOWED_COLORS)


@calendar_bp.route("/eventos/<int:event_id>/eliminar", methods=["POST"])
@security.login_required
def delete_event(event_id):
    user_id = security.current_user_id()
    if repo_events.delete_owned(event_id, user_id):
        flash("Evento eliminado.", "ok")
    else:
        flash("No se pudo eliminar el evento.", "error")
    year, month = _current_local_year_month()
    return redirect(url_for("calendar_bp.month_view", year=year, month=month))


@calendar_bp.route("/eventos/<int:event_id>/invitar", methods=["POST"])
@security.login_required
def generate_invite_link(event_id):
    user_id = security.current_user_id()
    event = repo_events.get_owned(event_id, user_id)
    if not event:
        return jsonify({"error": "No tienes permiso sobre este evento"}), 403

    token = repo_events.create_invitation(event_id)
    invite_url = url_for("calendar_bp.view_invitation", token=token, _external=True)
    return jsonify({"token": token, "invite_url": invite_url})


@calendar_bp.route("/invitacion/<token>")
@security.login_required
def view_invitation(token):
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
@security.login_required
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
