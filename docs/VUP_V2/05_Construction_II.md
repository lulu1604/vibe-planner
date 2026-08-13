# 📋 VUP Phase 5: Construction Phase II Document

**Project Name:** VibePlanner — Multi-User Activity Planner with Transparent Prioritization
**Version:** 2.0 (Update — Multiusuario, Roles y Permisos)
**Phase:** Construction Phase II (Code Base & Technical Specification)

> Este documento contiene el **código del Módulo A (Núcleo)** completo y listo
> para ejecutar, más los **contratos congelados** que los módulos B, C y D deben
> respetar. El núcleo va completo porque **bloquea a todos los demás**: hasta que
> `security.py` y `schema_v2.sql` no estén en `main`, nadie más puede avanzar de
> verdad.

---

## 🗄️ 1. `schema_v2.sql` — fuente única de verdad del esquema

> **Dueño único: Jose Cabrera.** Si este archivo cambia, lo cambia él y **avisa al
> grupo**, porque todos deben borrar su `vibe_planner.db` local y regenerarlo.

```sql
-- =====================================================================
-- VibePlanner v2.0 - Esquema completo
-- Toda fecha se guarda como TEXT ISO:  'YYYY-MM-DD'  o  'YYYY-MM-DD HH:MM'
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- MÓDULO A: identidad, roles agregativos y permisos
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    full_name     TEXT    DEFAULT '',
    is_active     INTEGER NOT NULL DEFAULT 1,      -- 1 activo | 0 desactivado
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,              -- 'usuario' | 'lider' | 'admin'
    name        TEXT NOT NULL,
    description TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS permissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,              -- 'planner.crear', 'usuario.listar'…
    module      TEXT NOT NULL,                     -- 'planner' | 'admin' | 'calendario'…
    description TEXT DEFAULT ''
);

-- Tabla puente: qué permisos aporta cada rol
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id       INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id)       REFERENCES roles(id)       ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- Tabla puente: qué roles tiene cada usuario.  AQUÍ vive lo "agregativo":
-- varias filas para el mismo user_id = varios roles = unión de permisos.
CREATE TABLE IF NOT EXISTS user_roles (
    user_id    INTEGER NOT NULL,
    role_id    INTEGER NOT NULL,
    granted_by INTEGER,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id)    REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id)    REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- MÓDULO B: tareas, planner diario y Kanban
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tasks (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL,            -- DUEÑO de la tarea
    assigned_by       INTEGER,                     -- quién la asignó (US10), NULL si es propia
    title             TEXT    NOT NULL,
    description       TEXT    DEFAULT '',
    category          TEXT    DEFAULT 'General',   -- Trabajo | Personal | Actividades | …
    priority_level    INTEGER NOT NULL DEFAULT 2,  -- 1 Alta, 2 Media, 3 Baja
    due_date          TEXT    NOT NULL,            -- 'YYYY-MM-DD'
    start_time        TEXT,                        -- 'HH:MM'  (US8: horario del día)
    end_time          TEXT,                        -- 'HH:MM'
    color             TEXT    DEFAULT '#567C8D',
    estimated_minutes INTEGER NOT NULL DEFAULT 30,
    kanban_column     TEXT    NOT NULL DEFAULT 'todo',
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (kanban_column IN ('backlog','todo','ongoing','done')),
    CHECK (priority_level BETWEEN 1 AND 3),
    CHECK (estimated_minutes BETWEEN 1 AND 480),
    FOREIGN KEY (user_id)     REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- MÓDULO C: calendario e invitaciones
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id    INTEGER NOT NULL,
    title       TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    start_at    TEXT    NOT NULL,                  -- 'YYYY-MM-DD HH:MM'
    end_at      TEXT    NOT NULL,
    color       TEXT    DEFAULT '#567C8D',
    status      TEXT    NOT NULL DEFAULT 'confirmado',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('tentativo','confirmado','cancelado')),
    CHECK (end_at > start_at),
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event_invitations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        INTEGER NOT NULL,
    token           TEXT    NOT NULL UNIQUE,       -- secrets.token_urlsafe(32)
    invited_user_id INTEGER,                       -- NULL hasta que alguien acepta
    status          TEXT    NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('pending','accepted','declined','revoked')),
    FOREIGN KEY (event_id)        REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (invited_user_id) REFERENCES users(id)  ON DELETE CASCADE
);

-- Un usuario no puede aceptar dos veces el mismo evento (TC 12.4).
CREATE UNIQUE INDEX IF NOT EXISTS ux_invitation_event_user
    ON event_invitations(event_id, invited_user_id)
    WHERE invited_user_id IS NOT NULL;

-- ---------------------------------------------------------------------
-- MÓDULO D: hábitos
-- ---------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS habits (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    name         TEXT    NOT NULL,
    habit_type   TEXT    NOT NULL DEFAULT 'general',
    target_value REAL    DEFAULT 1,
    unit         TEXT    DEFAULT 'vez',            -- 'horas' | 'minutos' | 'vasos' | 'vez'
    is_active    INTEGER NOT NULL DEFAULT 1,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (habit_type IN ('dieta','ejercicio','relajacion','sueno','general')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS habit_logs (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    log_date TEXT    NOT NULL,                     -- 'YYYY-MM-DD'
    value    REAL    DEFAULT 0,
    done     INTEGER NOT NULL DEFAULT 0,
    UNIQUE (habit_id, log_date),                   -- idempotencia del registro (TC 13.2)
    FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- Índices: exactamente las columnas por las que filtra cada petición
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_user_roles_user   ON user_roles(user_id);
CREATE INDEX IF NOT EXISTS ix_tasks_user_due    ON tasks(user_id, due_date);
CREATE INDEX IF NOT EXISTS ix_tasks_user_column ON tasks(user_id, kanban_column);
CREATE INDEX IF NOT EXISTS ix_events_owner_start ON events(owner_id, start_at);
CREATE INDEX IF NOT EXISTS ix_habits_user       ON habits(user_id);
CREATE INDEX IF NOT EXISTS ix_habit_logs_date   ON habit_logs(habit_id, log_date);
```

**Nota sobre `CHECK` en SQLite:** las restricciones `CHECK` sí se aplican, pero
`PRAGMA foreign_keys = ON` hay que activarlo **en cada conexión** — no es
persistente. Por eso vive en `database.py` y no solo aquí.

---

## ⚙️ 2. `config.py`

```python
"""VibePlanner v2 - Configuración."""
import os

SECRET_KEY = os.environ.get("VIBEPLANNER_SECRET", "dev-only-no-usar-en-produccion")

DEFAULT_AVAILABLE_MINUTES = 120
MIN_PASSWORD_LENGTH = 8

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

KANBAN_COLUMNS = ("backlog", "todo", "ongoing", "done")
KANBAN_LABELS = {
    "backlog": "Backlog",
    "todo": "Por hacer",
    "ongoing": "En curso",
    "done": "Hecho",
}

# Colores permitidos para eventos y actividades (paleta del design system)
ALLOWED_COLORS = ("#2F4156", "#567C8D", "#C8D9E6", "#D7707F", "#9DA3A4", "#4C4D53")
```

---

## 🔌 3. `database.py` — conexión y arranque

```python
"""
VibePlanner v2 - Capa de conexión (database.py)
-----------------------------------------------------
DUEÑO: Jose Cabrera (dueño único del esquema)

Este archivo NO contiene SQL de negocio. Solo abre, cierra e inicializa.
El SQL de cada módulo vive en su repositorio (repo_users, repo_tasks, ...).
"""

import os
import sqlite3

from flask import g

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "vibe_planner.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema_v2.sql")


def _configure(conn):
    """PRAGMAs que NO son persistentes: hay que ponerlos en cada conexión."""
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")    # sin esto los FOREIGN KEY se ignoran
    conn.execute("PRAGMA journal_mode = WAL")   # lecturas concurrentes (riesgo R8)
    return conn


def get_db():
    """Una conexión por petición. NUNCA una conexión global compartida."""
    if "db" not in g:
        g.db = _configure(sqlite3.connect(DB_PATH, timeout=10.0))
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Crea el esquema si no existe. Idempotente: se puede llamar siempre."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        schema_sql = fh.read()
    conn = _configure(sqlite3.connect(DB_PATH))
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()


def raw_connection():
    """Conexión fuera del contexto Flask (para seed.py y los tests)."""
    return _configure(sqlite3.connect(DB_PATH, timeout=10.0))
```

---

## 👥 4. `repo_users.py` — el corazón de los roles agregativos

```python
"""
VibePlanner v2 - Repositorio de identidad (repo_users.py)
--------------------------------------------------------------
DUEÑO: Piero Calderón (Módulo A)

ÚNICO componente autorizado a tocar las tablas:
    users · roles · permissions · role_permissions · user_roles

CONTRATOS CONGELADOS - no cambiar estas firmas sin avisar al grupo:
    create_user(data, role_codes, granted_by=None) -> int | None
    get_by_username(username)                      -> dict | None
    get_by_id(user_id)                             -> dict | None
    list_users()                                   -> list[dict]
    get_permissions(user_id)                       -> set[str]
    get_roles(user_id)                             -> list[dict]
    assign_roles(user_id, role_codes, granted_by)  -> bool
    set_active(user_id, is_active)                 -> bool
    count_admins()                                 -> int
"""

import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db


# ----------------------------------------------------------------------
# Lectura
# ----------------------------------------------------------------------

def get_by_username(username):
    row = get_db().execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    return dict(row) if row else None


def get_by_id(user_id):
    row = get_db().execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return dict(row) if row else None


def list_users():
    """Todas las cuentas con sus roles concatenados, para el panel de admin."""
    rows = get_db().execute(
        """
        SELECT u.id, u.username, u.email, u.full_name, u.is_active, u.created_at,
               COALESCE(GROUP_CONCAT(r.code, ','), '') AS role_codes
        FROM   users u
        LEFT   JOIN user_roles ur ON ur.user_id = u.id
        LEFT   JOIN roles      r  ON r.id       = ur.role_id
        GROUP  BY u.id
        ORDER  BY u.username
        """
    ).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        item["roles"] = [c for c in item.pop("role_codes").split(",") if c]
        out.append(item)
    return out


def get_permissions(user_id):
    """
    ===================================================================
    ESTA CONSULTA *ES* LA DEFINICIÓN DE "ROLES AGREGATIVOS" (US6).
    Un usuario con dos roles recibe la UNIÓN de ambos conjuntos.
    DISTINCT elimina los permisos que ambos roles comparten.
    ===================================================================
    """
    rows = get_db().execute(
        """
        SELECT DISTINCT p.code
        FROM   user_roles       ur
        JOIN   role_permissions rp ON rp.role_id       = ur.role_id
        JOIN   permissions      p  ON p.id             = rp.permission_id
        WHERE  ur.user_id = ?
        """,
        (user_id,),
    ).fetchall()
    return {row["code"] for row in rows}


def get_roles(user_id):
    rows = get_db().execute(
        """
        SELECT r.id, r.code, r.name
        FROM   user_roles ur
        JOIN   roles      r ON r.id = ur.role_id
        WHERE  ur.user_id = ?
        ORDER  BY r.id
        """,
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def count_admins():
    """Cuántas cuentas ACTIVAS tienen el rol admin (para TC 7.3)."""
    row = get_db().execute(
        """
        SELECT COUNT(DISTINCT u.id) AS n
        FROM   users      u
        JOIN   user_roles ur ON ur.user_id = u.id
        JOIN   roles      r  ON r.id       = ur.role_id
        WHERE  r.code = 'admin' AND u.is_active = 1
        """
    ).fetchone()
    return row["n"] if row else 0


# ----------------------------------------------------------------------
# Escritura
# ----------------------------------------------------------------------

def create_user(data, role_codes, granted_by=None):
    """
    Crea la cuenta y le asigna los roles indicados, TODO en una transacción:
    una cuenta sin roles sería una cuenta sin ningún permiso, imposible de usar.

    Devuelve el id nuevo, o None si el usuario/correo ya existía.
    """
    db = get_db()
    try:
        cursor = db.execute(
            """INSERT INTO users (username, email, password_hash, full_name, is_active)
               VALUES (?, ?, ?, ?, ?)""",
            (
                data["username"].strip().lower(),
                data["email"].strip().lower(),
                generate_password_hash(data["password"]),   # NUNCA en claro
                data.get("full_name", "").strip(),
                int(data.get("is_active", 1)),
            ),
        )
        user_id = cursor.lastrowid
        _link_roles(db, user_id, role_codes, granted_by)
        db.commit()
        return user_id
    except sqlite3.IntegrityError:
        db.rollback()
        return None          # username o email duplicado (TC 5.2)


def assign_roles(user_id, role_codes, granted_by=None):
    """Reemplaza el conjunto de roles del usuario por el indicado."""
    db = get_db()
    db.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
    _link_roles(db, user_id, role_codes, granted_by)
    db.commit()
    return True


def set_active(user_id, is_active):
    db = get_db()
    cursor = db.execute(
        "UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id)
    )
    db.commit()
    return cursor.rowcount > 0


def set_password(user_id, raw_password):
    db = get_db()
    cursor = db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(raw_password), user_id),
    )
    db.commit()
    return cursor.rowcount > 0


def verify_password(user_row, raw_password):
    return check_password_hash(user_row["password_hash"], raw_password)


def _link_roles(db, user_id, role_codes, granted_by):
    """Inserta un par (user, role) por cada código. Ignora códigos inexistentes."""
    for code in role_codes:
        role = db.execute("SELECT id FROM roles WHERE code = ?", (code,)).fetchone()
        if role is None:
            continue
        db.execute(
            """INSERT OR IGNORE INTO user_roles (user_id, role_id, granted_by)
               VALUES (?, ?, ?)""",
            (user_id, role["id"], granted_by),
        )
```

---

## 🛡️ 5. `security.py` — el único lugar donde se decide quién pasa

```python
"""
VibePlanner v2 - Guardia de seguridad (security.py)
---------------------------------------------------------
DUEÑO: Piero Calderón (Módulo A)

CONTRATO CONGELADO EN EL HITO H2. Los módulos B, C y D solo usan:
    current_user()        -> dict | None
    current_user_id()     -> int  | None
    @login_required
    @requires("permiso.codigo")
    has_permission("permiso.codigo") -> bool     (también disponible en Jinja2)

REGLA DE LAS DOS LLAVES:
    @requires() comprueba el PERMISO.  La PROPIEDAD del registro la comprueba
    el repositorio con user_id dentro del WHERE.  Hacen falta las dos.
"""

from functools import wraps

from flask import abort, g, redirect, request, session, url_for

import repo_users


# ----------------------------------------------------------------------
# Identidad
# ----------------------------------------------------------------------

def current_user():
    """
    Usuario de la petición actual, o None.
    Se cachea en `g` (dura una sola petición), NUNCA en la sesión:
    si guardáramos los permisos en la cookie, quitarle un rol a alguien
    no tendría efecto hasta que cerrara sesión (TC 6.3).
    """
    if "current_user" not in g:
        user_id = session.get("user_id")
        user = repo_users.get_by_id(user_id) if user_id else None
        if user and not user["is_active"]:
            session.clear()          # desactivado a mitad de sesión → fuera
            user = None
        g.current_user = user
    return g.current_user


def current_user_id():
    user = current_user()
    return user["id"] if user else None


def effective_permissions():
    """Unión de los permisos de TODOS los roles del usuario (US6)."""
    if "permissions" not in g:
        user_id = current_user_id()
        g.permissions = repo_users.get_permissions(user_id) if user_id else set()
    return g.permissions


def has_permission(code):
    return code in effective_permissions()


# ----------------------------------------------------------------------
# Decoradores
# ----------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            # Guardamos el destino para volver solos tras el login (TC 12.3)
            session["next"] = request.full_path
            return redirect(url_for("auth.login_route"))
        return view(*args, **kwargs)
    return wrapped


def requires(*permission_codes):
    """
    Exige TODOS los permisos indicados.
    Comprueba PERMISOS, nunca nombres de rol: si mañana se crea el rol
    'soporte' con el mismo permiso, la ruta funciona sin tocar el código.
    """
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            perms = effective_permissions()
            if not all(code in perms for code in permission_codes):
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def register_template_helpers(app):
    """Expone las ayudas a Jinja2 para ocultar botones sin permiso.

    Ocultar el botón es cortesía visual, NO seguridad:
    la ruta sigue protegida por @requires en el servidor.
    """
    app.jinja_env.globals["current_user"] = current_user
    app.jinja_env.globals["has_permission"] = has_permission
```

---

## 🔐 6. `auth.py` — registro, login, logout

```python
"""
VibePlanner v2 - Autenticación (auth.py)
----------------------------------------------
DUEÑO: Piero Calderón (Módulo A)
"""

from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)

import config
import repo_users
from security import current_user

auth = Blueprint("auth", __name__)

# ======================================================================
# REGLA DE ORO DE ESTE ARCHIVO (riesgo R2 de Inception):
# El registro público SIEMPRE otorga exactamente ["usuario"].
# La constante está aquí, fija, y NO se lee del formulario. Un `role`
# enviado desde el navegador se ignora por completo (TC 5.3).
# ======================================================================
PUBLIC_REGISTRATION_ROLES = ["usuario"]


@auth.route("/register", methods=["GET", "POST"])
def register_route():
    if current_user():
        return redirect(url_for("planner.day_route"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()

        errors = _validate_registration(username, email, password)
        if errors:
            return render_template("auth/register.html", errors=errors,
                                   form=request.form), 400

        user_id = repo_users.create_user(
            {"username": username, "email": email,
             "password": password, "full_name": full_name},
            role_codes=PUBLIC_REGISTRATION_ROLES,   # <-- NO viene del formulario
        )
        if user_id is None:
            return render_template(
                "auth/register.html",
                errors=["Ese usuario o correo ya está registrado."],
                form=request.form,
            ), 409

        session.clear()
        session["user_id"] = user_id
        return redirect(url_for("planner.day_route"))

    return render_template("auth/register.html", errors=[], form={})


@auth.route("/login", methods=["GET", "POST"])
def login_route():
    if current_user():
        return redirect(url_for("planner.day_route"))

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = repo_users.get_by_username(username)

        # Mensaje idéntico en los dos fallos: no revelamos si el usuario existe.
        if user is None or not repo_users.verify_password(user, password):
            return render_template(
                "auth/login.html",
                errors=["Usuario o contraseña incorrectos."],
            ), 401

        if not user["is_active"]:
            return render_template(
                "auth/login.html",
                errors=["Tu cuenta está desactivada. Contacta al administrador."],
            ), 403

        destination = session.pop("next", None)
        session.clear()
        session["user_id"] = user["id"]
        return redirect(destination or url_for("planner.day_route"))

    return render_template("auth/login.html", errors=[])


@auth.route("/logout", methods=["POST"])
def logout_route():
    session.clear()
    return redirect(url_for("auth.login_route"))


def _validate_registration(username, email, password):
    errors = []
    if len(username) < 3:
        errors.append("El usuario debe tener al menos 3 caracteres.")
    if "@" not in email or "." not in email.split("@")[-1]:
        errors.append("Escribe un correo válido.")
    if len(password) < config.MIN_PASSWORD_LENGTH:
        errors.append(
            f"La contraseña debe tener al menos {config.MIN_PASSWORD_LENGTH} caracteres."
        )
    return errors
```

---

## 🧑‍💼 7. `admin.py` — gestión de usuarios y métricas del sistema

```python
"""
VibePlanner v2 - Administración (admin.py)
------------------------------------------------
DUEÑO: Piero Calderón (Módulo A)
"""

from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for)

import metrics
import repo_users
from security import current_user_id, requires

admin = Blueprint("admin", __name__, url_prefix="/admin")

ASSIGNABLE_ROLES = ["usuario", "admin"]   # v2.1: el rol "lider" pasó al backlog v3


@admin.route("/usuarios")
@requires("usuario.listar")
def list_users_route():
    return render_template("admin/usuarios.html",
                           users=repo_users.list_users(),
                           roles=ASSIGNABLE_ROLES)


@admin.route("/usuarios", methods=["POST"])
@requires("usuario.crear")
def create_user_route():
    # Aquí SÍ se leen los roles del formulario, porque quien llega hasta esta
    # línea ya demostró tener 'usuario.crear'. Es lo contrario del registro
    # público, donde el rol es una constante del servidor.
    role_codes = [c for c in request.form.getlist("roles") if c in ASSIGNABLE_ROLES]
    if "usuario" not in role_codes:
        role_codes.append("usuario")     # todos son usuarios: los roles se suman

    user_id = repo_users.create_user(
        {
            "username": request.form.get("username", ""),
            "email": request.form.get("email", ""),
            "password": request.form.get("password", ""),
            "full_name": request.form.get("full_name", ""),
        },
        role_codes=role_codes,
        granted_by=current_user_id(),
    )
    flash("Cuenta creada." if user_id else "Ese usuario o correo ya existe.")
    return redirect(url_for("admin.list_users_route"))


@admin.route("/usuarios/<int:user_id>/roles", methods=["POST"])
@requires("rol.asignar")
def assign_roles_route(user_id):
    role_codes = [c for c in request.form.getlist("roles") if c in ASSIGNABLE_ROLES]
    if "usuario" not in role_codes:
        role_codes.append("usuario")

    # TC 7.3: el sistema nunca se queda sin administradores.
    if _would_remove_last_admin(user_id, role_codes):
        flash("No puedes dejar el sistema sin administradores.")
        return redirect(url_for("admin.list_users_route"))

    repo_users.assign_roles(user_id, role_codes, granted_by=current_user_id())
    flash("Roles actualizados.")
    return redirect(url_for("admin.list_users_route"))


@admin.route("/usuarios/<int:user_id>/estado", methods=["POST"])
@requires("usuario.desactivar")
def toggle_active_route(user_id):
    activate = request.form.get("is_active") == "1"

    if not activate and _would_remove_last_admin(user_id, []):
        flash("No puedes dejar el sistema sin administradores.")
        return redirect(url_for("admin.list_users_route"))

    # Desactivar NO es borrar: las tareas y eventos siguen existiendo (TC 7.2).
    repo_users.set_active(user_id, activate)
    flash("Cuenta actualizada.")
    return redirect(url_for("admin.list_users_route"))


@admin.route("/metricas")
@requires("metrica.sistema.ver")
def system_metrics_route():
    # Solo agregados: nunca el contenido de las tareas de nadie (TC 15.2).
    return render_template("admin/metricas.html", data=metrics.system_metrics())


def _would_remove_last_admin(user_id, new_role_codes):
    """True si la operación dejaría al sistema sin ningún admin activo."""
    is_admin_now = any(r["code"] == "admin" for r in repo_users.get_roles(user_id))
    keeps_admin = "admin" in new_role_codes
    return is_admin_now and not keeps_admin and repo_users.count_admins() <= 1
```

---

## 🌱 8. `seed.py` — roles, permisos y administrador semilla

```python
"""
VibePlanner v2 - Semilla del sistema (seed.py)
----------------------------------------------------
DUEÑO: Piero Calderón (Módulo A)

Ejecutar UNA VEZ tras crear la base:
    python seed.py

Es idempotente: se puede volver a ejecutar sin duplicar nada.

NO EXISTE registro público de administrador. El primer admin nace aquí,
y todos los demás los crea él desde /admin/usuarios.
"""

import os
import sys

from werkzeug.security import generate_password_hash

import database

# ----------------------------------------------------------------------
# Catálogo de permisos: (código, módulo, descripción)
# Un permiso que se usa en un decorador pero no está en esta lista
# es un 403 permanente que nadie sabrá explicar.
# ----------------------------------------------------------------------
PERMISSIONS = [
    ("perfil.ver",           "perfil",     "Ver su propio perfil"),
    ("perfil.editar",        "perfil",     "Editar su propio perfil"),

    ("planner.ver",          "planner",    "Ver su planner diario"),
    ("planner.crear",        "planner",    "Crear actividades"),
    ("planner.editar",       "planner",    "Editar sus actividades"),
    ("planner.eliminar",     "planner",    "Eliminar sus actividades"),
    ("kanban.ver",           "planner",    "Ver su tablero Kanban"),
    ("kanban.mover",         "planner",    "Mover tarjetas entre columnas"),

    ("evento.ver",           "calendario", "Ver su calendario"),
    ("evento.crear",         "calendario", "Crear eventos"),
    ("evento.editar",        "calendario", "Editar sus eventos"),
    ("evento.eliminar",      "calendario", "Eliminar sus eventos"),
    ("evento.invitar",       "calendario", "Generar links de invitación"),

    ("habito.ver",           "habitos",    "Ver sus hábitos"),
    ("habito.crear",         "habitos",    "Crear hábitos"),
    ("habito.registrar",     "habitos",    "Registrar el cumplimiento diario"),
    ("metrica.propia.ver",   "metricas",   "Ver sus propias métricas"),

    ("usuario.listar",       "admin",      "Listar todas las cuentas"),
    ("usuario.crear",        "admin",      "Crear cuentas"),
    ("usuario.editar",       "admin",      "Editar cuentas"),
    ("usuario.desactivar",   "admin",      "Activar y desactivar cuentas"),
    ("rol.asignar",          "admin",      "Asignar roles a las cuentas"),
    ("metrica.sistema.ver",  "admin",      "Ver las métricas del sistema"),
]

# ----------------------------------------------------------------------
# ALCANCE v2.1: solo DOS roles. El rol "lider" (asignar tareas a otros,
# historia US10) pasó al backlog v3 por tiempo. Volver a añadirlo es una
# entrada en este diccionario, no un refactor: eso es lo que compra tener
# los permisos en tablas.
#
# Roles AGREGATIVOS: cada uno aporta SOLO lo suyo.
# Un administrador real tiene los roles ['usuario', 'admin'] y por tanto
# la UNIÓN de ambos conjuntos. Por eso 'admin' no repite los permisos
# de 'usuario': se suman solos.
# ----------------------------------------------------------------------
ROLES = {
    "usuario": {
        "name": "Usuario",
        "description": "Usa la aplicación: su planner, su calendario, sus hábitos.",
        "permissions": [
            "perfil.ver", "perfil.editar",
            "planner.ver", "planner.crear", "planner.editar", "planner.eliminar",
            "kanban.ver", "kanban.mover",
            "evento.ver", "evento.crear", "evento.editar", "evento.eliminar",
            "evento.invitar",
            "habito.ver", "habito.crear", "habito.registrar",
            "metrica.propia.ver",
        ],
    },
    "admin": {
        "name": "Administrador",
        "description": "Aporta la gestión de cuentas y las métricas del sistema.",
        "permissions": [
            "usuario.listar", "usuario.crear", "usuario.editar",
            "usuario.desactivar", "rol.asignar", "metrica.sistema.ver",
        ],
    },
}


def seed():
    database.init_db()
    conn = database.raw_connection()

    # 1. Permisos
    for code, module, description in PERMISSIONS:
        conn.execute(
            """INSERT INTO permissions (code, module, description) VALUES (?, ?, ?)
               ON CONFLICT(code) DO UPDATE SET module = excluded.module,
                                               description = excluded.description""",
            (code, module, description),
        )

    # 2. Roles y sus vínculos
    for code, spec in ROLES.items():
        conn.execute(
            """INSERT INTO roles (code, name, description) VALUES (?, ?, ?)
               ON CONFLICT(code) DO UPDATE SET name = excluded.name,
                                               description = excluded.description""",
            (code, spec["name"], spec["description"]),
        )
        role_id = conn.execute(
            "SELECT id FROM roles WHERE code = ?", (code,)
        ).fetchone()["id"]

        conn.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
        for perm_code in spec["permissions"]:
            perm = conn.execute(
                "SELECT id FROM permissions WHERE code = ?", (perm_code,)
            ).fetchone()
            conn.execute(
                "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                (role_id, perm["id"]),
            )

    # 3. Administrador semilla: usuario + admin (roles agregativos en acción)
    admin_user = os.environ.get("VIBEPLANNER_ADMIN_USER", "admin")
    admin_mail = os.environ.get("VIBEPLANNER_ADMIN_EMAIL", "admin@vibeplanner.local")
    admin_pass = os.environ.get("VIBEPLANNER_ADMIN_PASS", "CambiarEsto2026!")

    existing = conn.execute(
        "SELECT id FROM users WHERE username = ?", (admin_user,)
    ).fetchone()

    if existing is None:
        cursor = conn.execute(
            """INSERT INTO users (username, email, password_hash, full_name, is_active)
               VALUES (?, ?, ?, ?, 1)""",
            (admin_user, admin_mail, generate_password_hash(admin_pass),
             "Administrador del sistema"),
        )
        admin_id = cursor.lastrowid
        for role_code in ("usuario", "admin"):
            role_id = conn.execute(
                "SELECT id FROM roles WHERE code = ?", (role_code,)
            ).fetchone()["id"]
            conn.execute(
                "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (admin_id, role_id),
            )
        print(f"Administrador semilla creado: {admin_user}")
        if admin_pass == "CambiarEsto2026!":
            print("  ⚠️  ESTÁ USANDO LA CONTRASEÑA POR DEFECTO. Cámbiala al desplegar.")
    else:
        print(f"El administrador '{admin_user}' ya existía. No se toca.")

    conn.commit()
    conn.close()
    print(f"Semilla lista: {len(PERMISSIONS)} permisos, {len(ROLES)} roles.")


if __name__ == "__main__":
    seed()
```

---

## 🚀 9. `app.py` — solo ensambla

```python
"""
VibePlanner v2 - Aplicación Flask (app.py)
------------------------------------------------
DUEÑO: Piero Calderón (Módulo A)

Este archivo NO contiene lógica de negocio ni SQL. Crea `app`, la configura
y registra los blueprints. Nada más.

La instancia se llama EXACTAMENTE `app` a nivel de módulo porque
PythonAnywhere ejecuta `from app import app`. Sin application factory.
"""

from flask import Flask, render_template

import config
import database
import security
from admin import admin
from auth import auth
from calendar_bp import calendario
from habits import habitos
from planner import planner

app = Flask(__name__)
app.config.from_object(config)
app.secret_key = config.SECRET_KEY

database.init_db()

app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(planner)
app.register_blueprint(calendario)
app.register_blueprint(habitos)

security.register_template_helpers(app)


@app.teardown_appcontext
def _close_db(exception=None):
    database.close_db(exception)


@app.errorhandler(403)
def _forbidden(error):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def _not_found(error):
    return render_template("errors/404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
```

---

## 🔄 10. `migrate_v1_to_v2.py` — no perder los datos de v1

```python
"""
VibePlanner - Migración v1 → v2
---------------------------------------
Las bases de datos de v1 no tienen usuarios y usan status pending/in_progress/
completed. Este script crea el esquema v2, siembra roles y permisos, y adopta
las tareas huérfanas asignándolas a una cuenta.

    python migrate_v1_to_v2.py --owner admin

Haz una copia de vibe_planner.db antes de ejecutarlo.
"""

import argparse

import database
import seed

STATUS_MAP = {
    "pending": "todo",
    "in_progress": "ongoing",
    "completed": "done",
}


def migrate(owner_username):
    seed.seed()                       # crea el esquema v2 + roles + permisos + admin
    conn = database.raw_connection()

    owner = conn.execute(
        "SELECT id FROM users WHERE username = ?", (owner_username,)
    ).fetchone()
    if owner is None:
        raise SystemExit(f"No existe el usuario '{owner_username}'. Ejecuta seed.py primero.")

    columns = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}

    # Caso 1: base v1 pura (tasks sin user_id) → adoptar las filas
    if "user_id" not in columns:
        raise SystemExit(
            "La tabla `tasks` es de v1. Renómbrala a tasks_v1, ejecuta seed.py\n"
            "para crear el esquema nuevo, y vuelve a lanzar este script."
        )

    # Caso 2: tasks_v1 presente → copiar mapeando los estados
    tables = {row["name"] for row in
              conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "tasks_v1" in tables:
        rows = conn.execute("SELECT * FROM tasks_v1").fetchall()
        for row in rows:
            conn.execute(
                """INSERT INTO tasks (user_id, title, category, priority_level,
                                      due_date, estimated_minutes, kanban_column)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    owner["id"],
                    row["title"],
                    row["category"],
                    row["priority_level"],
                    row["due_date"],
                    row["estimated_minutes"],
                    STATUS_MAP.get(row["status"], "todo"),
                ),
            )
        print(f"{len(rows)} tareas de v1 adoptadas por '{owner_username}'.")

    conn.commit()
    conn.close()
    print("Migración completada.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default="admin",
                        help="usuario que adopta las tareas huérfanas de v1")
    migrate(parser.parse_args().owner)
```

---

## 📜 11. Contratos congelados para los módulos B, C y D

> Estas firmas se publican en el hito **H2**. Los tres módulos las programan
> contra ellas sin esperar a que el otro termine. Cambiar una firma después de H2
> requiere avisar al grupo.

### 11.1 `repo_tasks.py` — Módulo B

```python
def get_owned(task_id, user_id)                      -> dict | None
def list_by_user(user_id, column=None)               -> list[dict]
def list_by_day(user_id, date_iso)                   -> list[dict]
def list_board(user_id)                              -> dict[str, list[dict]]
def list_assigned_by(leader_id)                      -> list[dict]
def create(data, owner_id, assigned_by=None)         -> int
def update_owned(task_id, user_id, data)             -> bool
def move_column(task_id, user_id, column)            -> bool
def delete_owned(task_id, user_id)                   -> bool
def daily_progress(user_id, date_iso)                -> {"total", "completed", "percent"}
```

**Regla no negociable:** toda función que reciba `user_id` lo pone **dentro del
`WHERE`**, nunca filtra en Python después de traer las filas.

### 11.2 `repo_events.py` — Módulo C

```python
def list_month(user_id, year, month)                 -> list[dict]   # propios + aceptados
def list_day(user_id, date_iso)                      -> list[dict]
def get_owned(event_id, user_id)                     -> dict | None
def create(data, owner_id)                           -> int
def update_owned(event_id, user_id, data)            -> bool
def delete_owned(event_id, user_id)                  -> bool
def create_invitation(event_id)                      -> str          # token
def get_event_by_token(token)                        -> dict | None
def accept_invitation(token, user_id)                -> bool         # idempotente
def count_attendees(event_id)                        -> int
```

### 11.3 `repo_habits.py` y `metrics.py` — Módulo D

```python
# repo_habits.py
def list_by_user(user_id)                            -> list[dict]
def get_owned(habit_id, user_id)                     -> dict | None
def create(data, user_id)                            -> int
def upsert_log(habit_id, date_iso, value, done)      -> bool         # UNIQUE(habit_id, log_date)
def logs_range(habit_id, from_iso, to_iso)           -> list[dict]

# metrics.py
def daily_summary(user_id, date_iso)                 -> dict         # por sección + %
def habit_streak(habit_id, today_iso)                -> int          # días consecutivos
def system_metrics()                                 -> dict         # solo agregados
```

### 11.4 `scoring.py` — sin cambios de fórmula

```python
def calculate_score(task, available_minutes)         -> (total, breakdown)
def rank_tasks(tasks, available_minutes)             -> list[dict]
```

**La fórmula es la misma de v1.** Prioridad 50/30/10 · Urgencia 40/20/10/5 ·
Ajuste de tiempo +15/0. Lo único que cambia es que la lista `tasks` que recibe ya
viene filtrada por `user_id` desde `repo_tasks`.

---

## 🧪 12. `test_v2.py` — asserts de los casos críticos

```python
"""
VibePlanner v2 - Suite de verificación automática
-------------------------------------------------------
    python test_v2.py

Ejecuta los casos Given-When-Then de Elaboration I contra el cliente de
pruebas de Flask, sobre una base temporal. No toca vibe_planner.db.
"""

import os
import tempfile

os.environ["VIBEPLANNER_SECRET"] = "test-secret"

import database                                       # noqa: E402

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
database.DB_PATH = _tmp.name                          # base aislada

import seed                                           # noqa: E402
seed.seed()

from app import app                                   # noqa: E402
import repo_users                                     # noqa: E402

app.config["TESTING"] = True
PASSED = []


def check(name, condition):
    assert condition, f"❌ {name}"
    PASSED.append(name)
    print(f"✅ {name}")


# ---------------------------------------------------------------- TC 5.1
with app.test_client() as client:
    client.post("/register", data={
        "username": "piero", "email": "piero@esan.pe",
        "password": "Vibe2026!", "full_name": "Piero"})
    with app.app_context():
        user = repo_users.get_by_username("piero")
        check("TC 5.1 - la cuenta se crea activa", user and user["is_active"] == 1)
        check("TC 5.1 - la contraseña NO se guarda en claro",
              "Vibe2026!" not in user["password_hash"])
        roles = [r["code"] for r in repo_users.get_roles(user["id"])]
        check("TC 5.1 - el registro otorga exactamente ['usuario']", roles == ["usuario"])

# ---------------------------------------------------------------- TC 5.2
with app.test_client() as client:
    response = client.post("/register", data={
        "username": "piero", "email": "piero@esan.pe", "password": "Otra2026!"})
    check("TC 5.2 - usuario duplicado rechazado", response.status_code == 409)

# ---------------------------------------------------------------- TC 5.3 ⚠️
with app.test_client() as client:
    client.post("/register", data={
        "username": "atacante", "email": "atacante@esan.pe",
        "password": "Hack2026!", "role": "admin", "roles": "admin"})
    with app.app_context():
        user = repo_users.get_by_username("atacante")
        roles = [r["code"] for r in repo_users.get_roles(user["id"])]
        check("TC 5.3 ⚠️ - el campo role del formulario se ignora", roles == ["usuario"])

# ---------------------------------------------------------------- TC 6.1
with app.app_context():
    admin_user = repo_users.get_by_username("admin")
    perms = repo_users.get_permissions(admin_user["id"])
    check("TC 6.1 - el admin conserva los permisos de usuario", "planner.ver" in perms)
    check("TC 6.1 - y suma los de admin", "usuario.listar" in perms)
    check("TC 6.1 - la unión no tiene duplicados", len(perms) == len(set(perms)))

# ---------------------------------------------------------------- TC 6.2
with app.test_client() as client:
    client.post("/login", data={"username": "piero", "password": "Vibe2026!"})
    response = client.get("/admin/usuarios")
    check("TC 6.2 - sin permiso la ruta responde 403", response.status_code == 403)

# ---------------------------------------------------------------- TC 5.5
with app.app_context():
    victim = repo_users.get_by_username("atacante")
    repo_users.set_active(victim["id"], False)
with app.test_client() as client:
    response = client.post("/login", data={
        "username": "atacante", "password": "Hack2026!"})
    check("TC 5.5 - una cuenta desactivada no inicia sesión",
          response.status_code == 403)

# ---------------------------------------------------------------- TC 5.4
with app.test_client() as client:
    response = client.post("/login", data={
        "username": "piero", "password": "incorrecta"})
    check("TC 5.4 - contraseña incorrecta rechazada", response.status_code == 401)

print(f"\n{len(PASSED)}/{len(PASSED)} verificaciones del Núcleo en verde.")
os.unlink(_tmp.name)
```

> Los módulos B, C y D **añaden sus propios bloques a este archivo** siguiendo el
> mismo formato: un `check()` por criterio Given-When-Then, con el código del caso
> en el nombre. Al final del sprint, `python test_v2.py` es la evidencia completa
> de la fase de Testing.
