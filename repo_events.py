"""
VibePlanner v2 - Repositorio de Eventos e Invitaciones (repo_events.py)
------------------------------------------------------------------------
DUEÑO DE ESTE ARCHIVO: Jose Cabrera (Módulo C - Calendario e Invitaciones)

CONTRATO CONGELADO - MÓDULO C:
    list_month(user_id, year, month)      -> list[dict]   # propios + aceptados
    list_day(user_id, date_iso)           -> list[dict]   # lo consume el Módulo D
    get_owned(event_id, user_id)          -> dict | None
    get_by_id(event_id)                   -> dict | None
    create(data, owner_id)                -> int
    update_owned(event_id, user_id, data) -> bool
    delete_owned(event_id, user_id)       -> bool
    create_invitation(event_id)           -> str          # token urlsafe
    get_event_by_token(token)             -> dict | None
    accept_invitation(token, user_id)     -> bool         # idempotente
    count_attendees(event_id)             -> int
"""

import calendar
import secrets
import sqlite3

import database


# Marca de las filas que solo registran "esta persona asiste", frente a las que
# son un enlace de invitacion de verdad. Ver get_event_by_token.
PREFIJO_ASISTENCIA = "asistencia:"


def _dict_from_row(row):
    return dict(row) if row else None


def list_month(user_id, year, month):
    """
    Devuelve los eventos propios del usuario Y los aceptados como invitado
    en el mes (year, month).
    Rango: YYYY-MM-01 00:00 hasta el primer día del mes siguiente.
    """
    if month < 1 or month > 12:
        return []

    first_day = f"{year:04d}-{month:02d}-01 00:00"
    if month == 12:
        next_first_day = f"{year + 1:04d}-01-01 00:00"
    else:
        next_first_day = f"{year:04d}-{month + 1:02d}-01 00:00"

    db = database.get_db()
    sql = """
        SELECT e.id, e.owner_id, e.title, e.description, e.start_at, e.end_at,
               e.color, e.status, e.created_at, 'propio' AS origen, NULL AS anfitrion
        FROM   events e
        WHERE  e.owner_id = ? AND e.start_at >= ? AND e.start_at < ?
        UNION
        SELECT e.id, e.owner_id, e.title, e.description, e.start_at, e.end_at,
               e.color, e.status, e.created_at, 'invitado' AS origen, u.username AS anfitrion
        FROM   events e
        JOIN   event_invitations i ON i.event_id = e.id
        JOIN   users u             ON u.id       = e.owner_id
        WHERE  i.invited_user_id = ? AND i.status = 'accepted'
           AND e.start_at >= ? AND e.start_at < ?
        ORDER  BY start_at ASC
    """
    rows = db.execute(sql, (user_id, first_day, next_first_day, user_id, first_day, next_first_day)).fetchall()
    return [dict(r) for r in rows]


def list_day(user_id, date_iso):
    """
    Devuelve todos los eventos propios y aceptados para una fecha específica 'YYYY-MM-DD'.
    Lo consume el Módulo D para correlación de hábitos y agenda.
    """
    start_day = f"{date_iso} 00:00"
    end_day = f"{date_iso} 23:59:59"

    db = database.get_db()
    sql = """
        SELECT e.id, e.owner_id, e.title, e.description, e.start_at, e.end_at,
               e.color, e.status, e.created_at, 'propio' AS origen, NULL AS anfitrion
        FROM   events e
        WHERE  e.owner_id = ? AND e.start_at >= ? AND e.start_at <= ?
        UNION
        SELECT e.id, e.owner_id, e.title, e.description, e.start_at, e.end_at,
               e.color, e.status, e.created_at, 'invitado' AS origen, u.username AS anfitrion
        FROM   events e
        JOIN   event_invitations i ON i.event_id = e.id
        JOIN   users u             ON u.id       = e.owner_id
        WHERE  i.invited_user_id = ? AND i.status = 'accepted'
           AND e.start_at >= ? AND e.start_at <= ?
        ORDER  BY start_at ASC
    """
    rows = db.execute(sql, (user_id, start_day, end_day, user_id, start_day, end_day)).fetchall()
    return [dict(r) for r in rows]


def get_owned(event_id, user_id):
    """Verifica pertenencia del evento (owner_id == user_id)."""
    db = database.get_db()
    row = db.execute(
        "SELECT * FROM events WHERE id = ? AND owner_id = ?",
        (event_id, user_id)
    ).fetchone()
    return _dict_from_row(row)


def get_by_id(event_id):
    """Obtiene un evento por su id."""
    db = database.get_db()
    row = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    return _dict_from_row(row)


def create(data, owner_id):
    """Crea un nuevo evento asociándolo a owner_id."""
    db = database.get_db()
    cur = db.execute(
        """
        INSERT INTO events (owner_id, title, description, start_at, end_at, color, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            owner_id,
            data["title"],
            data.get("description", ""),
            data["start_at"],
            data["end_at"],
            data.get("color", "#567C8D"),
            data.get("status", "confirmado")
        )
    )
    db.commit()
    return cur.lastrowid


def update_owned(event_id, user_id, data):
    """Actualiza un evento existente si pertenece al usuario (owner_id)."""
    db = database.get_db()
    cur = db.execute(
        """
        UPDATE events
        SET title = ?, description = ?, start_at = ?, end_at = ?, color = ?, status = ?
        WHERE id = ? AND owner_id = ?
        """,
        (
            data["title"],
            data.get("description", ""),
            data["start_at"],
            data["end_at"],
            data.get("color", "#567C8D"),
            data.get("status", "confirmado"),
            event_id,
            user_id
        )
    )
    db.commit()
    return cur.rowcount > 0


def delete_owned(event_id, user_id):
    """Elimina un evento si pertenece al usuario (owner_id)."""
    db = database.get_db()
    cur = db.execute("DELETE FROM events WHERE id = ? AND owner_id = ?", (event_id, user_id))
    db.commit()
    return cur.rowcount > 0


def create_invitation(event_id):
    """
    Genera un token seguro criptográficamente para invitar usuarios a un evento.
    Nunca se usa un ID incremental.
    """
    token = secrets.token_urlsafe(32)
    db = database.get_db()
    db.execute(
        "INSERT INTO event_invitations (event_id, token, status) VALUES (?, ?, 'pending')",
        (event_id, token)
    )
    db.commit()
    return token


def get_event_by_token(token):
    """
    Devuelve los datos del evento asociado a una invitación activa por token.
    Si la invitación no existe o está revocada, devuelve None.
    """
    # Las filas de asistencia llevan un token sintético `asistencia:evento:user`
    # solo porque la columna es UNIQUE NOT NULL. Ese valor es ADIVINABLE -- son
    # dos enteros pequeños -- así que se descarta aquí: no es un enlace de
    # invitación y no puede comportarse como si lo fuera.
    if not token or token.startswith(PREFIJO_ASISTENCIA):
        return None

    db = database.get_db()
    sql = """
        SELECT e.id AS event_id, e.title, e.description, e.start_at, e.end_at, e.color,
               e.owner_id, u.username AS anfitrion, u.full_name AS anfitrion_nombre,
               i.id AS invitation_id, i.token, i.status AS invitation_status
        FROM   event_invitations i
        JOIN   events e ON e.id = i.event_id
        JOIN   users u  ON u.id = e.owner_id
        WHERE  i.token = ? AND i.status != 'revoked'
    """
    row = db.execute(sql, (token,)).fetchone()
    return _dict_from_row(row)


def accept_invitation(token, user_id):
    """
    Acepta una invitación asociando `invited_user_id = user_id`.
    Es IDEMPOTENTE: si el usuario ya aceptó, devuelve True sin duplicar ni lanzar error.
    """
    db = database.get_db()
    inv = db.execute(
        "SELECT * FROM event_invitations WHERE token = ? AND status != 'revoked'",
        (token,)
    ).fetchone()

    if not inv:
        return False

    event_id = inv["event_id"]

    # El anfitrión no necesita aceptar su propio evento
    event = get_by_id(event_id)
    if event and event["owner_id"] == user_id:
        return True

    # Verificar si el usuario ya aceptó previamente
    existing = db.execute(
        """
        SELECT 1 FROM event_invitations
        WHERE event_id = ? AND invited_user_id = ? AND status = 'accepted'
        """,
        (event_id, user_id)
    ).fetchone()

    if existing:
        return True

    # Si la fila actual de la invitación no tiene invitado asignado, la actualiza
    if inv["invited_user_id"] is None:
        db.execute(
            "UPDATE event_invitations SET invited_user_id = ?, status = 'accepted' WHERE id = ?",
            (user_id, inv["id"])
        )
    else:
        # La invitacion original ya la uso otra persona. Se guarda la
        # asistencia de esta con un token PROPIO E INSERVIBLE, no con uno nuevo
        # de `token_urlsafe`.
        #
        # Antes se acunaba un token valido en cada aceptacion: cada persona que
        # entraba por el link generaba otro link vivo que nadie habia decidido
        # crear, y el numero de accesos validos crecia solo. La columna es
        # UNIQUE NOT NULL, asi que hace falta un valor: se usa uno con prefijo
        # marcado, imposible de adivinar como enlace porque no es un token.
        try:
            db.execute(
                "INSERT INTO event_invitations (event_id, token, invited_user_id, status) "
                "VALUES (?, ?, ?, 'accepted')",
                (event_id, "%s%d:%d" % (PREFIJO_ASISTENCIA, event_id, user_id), user_id)
            )
        except sqlite3.IntegrityError:
            pass

    db.commit()
    return True


def count_attendees(event_id):
    """
    Invitados que ACEPTARON. No incluye al anfitrión.

    Antes devolvía `1 + invitados`, sumándose el anfitrión a sí mismo, y eso
    contradice el plan de pruebas: TC-29 dice "el panel de piero muestra
    1 asistente confirmado" tras aceptar ana, y TC-32 dice "el contador sigue
    en 1" al aceptar dos veces. Con el anfitrión dentro mostraba 2.
    """
    db = database.get_db()
    return db.execute(
        """
        SELECT COUNT(*) FROM event_invitations
        WHERE event_id = ? AND status = 'accepted' AND invited_user_id IS NOT NULL
        """,
        (event_id,)
    ).fetchone()[0]
