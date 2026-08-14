"""
VibePlanner v2 - Repositorio de identidad (repo_users.py)
---------------------------------------------------------
DUENO DE ESTE ARCHIVO: Piero Calderon (Modulo A - Nucleo)

UNICO componente que toca las tablas `users`, `roles`, `permissions`,
`role_permissions` y `user_roles`. Si alguien escribe SQL sobre ellas fuera de
aqui, la regla del ultimo administrador y la normalizacion de usuarios dejan de
valer, porque viven en este archivo y en ningun otro.

CONTRATO PUBLICO - avisar al grupo antes de cambiar una firma:
    get_by_username(username)                       -> dict | None
    get_by_id(user_id)                              -> dict | None
    list_users(search, limit, offset)               -> list[dict]  (con 'roles')
    count_users(search)                             -> int
    get_permissions(user_id)                        -> set[str]
    get_roles(user_id)                              -> list[dict]
    count_admins()                                  -> int
    exists_username(username, excluir_id)           -> bool
    exists_email(email, excluir_id)                 -> bool
    create_user(datos, role_codes, granted_by)      -> int | None
    assign_roles(user_id, role_codes, granted_by)   -> bool
    set_active(user_id, is_active)                  -> bool
    set_password(user_id, password)                 -> bool
    verify_password(usuario, password)              -> bool

Todas aceptan `conn=` opcional para poder correr fuera de una peticion Flask
(seed.py y las pruebas, que no tienen `g`).
"""

import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

import config
from database import get_db


class SinAdministradores(Exception):
    """
    La operacion habria dejado el sistema sin ningun administrador activo.

    Se lanza DESDE DENTRO de la transaccion, despues de aplicar el cambio y
    contar: asi la comprobacion y la escritura son atomicas. Comprobar antes y
    escribir despues deja una carrera real -- dos administradores quitandose el
    rol a la vez leen ambos "quedan 2" y el sistema se queda sin ninguno.
    """


# Hash de una contrasena que nadie tiene. Sirve para gastar el mismo tiempo
# cuando el usuario no existe: sin esto, la respuesta llega antes y se pueden
# enumerar las cuentas validas cronometrando el login.
_HASH_SENUELO = generate_password_hash("cuenta-inexistente", method=config.PASSWORD_HASH_METHOD)


def _conn(conn=None):
    """La conexion de la peticion, o la que nos pasen (seed.py, pruebas)."""
    return conn if conn is not None else get_db()


def _fila(row):
    return dict(row) if row is not None else None


def _patron_like(texto):
    """
    Prepara el texto para un LIKE. Sin escapar, un usuario que busca "100%"
    hace que el patron case con TODO, y un "_" casa con cualquier caracter.
    """
    escapado = (texto or "").replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


# --------------------------------------------------------------------------
# Lectura
# --------------------------------------------------------------------------
def get_by_username(username, conn=None):
    fila = _conn(conn).execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    return _fila(fila)


def get_by_email(email, conn=None):
    fila = _conn(conn).execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    return _fila(fila)


def get_by_id(user_id, conn=None):
    fila = _conn(conn).execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return _fila(fila)


def get_permissions(user_id, conn=None):
    """
    ESTA CONSULTA ES EL REQUISITO US6.

    Los permisos efectivos son la UNION de los permisos de todos los roles que
    lleva la cuenta. No hay jerarquia ni herencia: el rol es una bolsa de
    permisos que se carga, y llevar dos bolsas es tener el contenido de ambas.
    Por eso `admin` no repite los permisos de `usuario` en la semilla: se suman
    solos porque el administrador tiene los dos roles.
    """
    filas = _conn(conn).execute(
        """
        SELECT DISTINCT p.code
        FROM   user_roles       ur
        JOIN   role_permissions rp ON rp.role_id       = ur.role_id
        JOIN   permissions      p  ON p.id             = rp.permission_id
        WHERE  ur.user_id = ?
        """,
        (user_id,),
    ).fetchall()
    return {f["code"] for f in filas}


def get_roles(user_id, conn=None):
    filas = _conn(conn).execute(
        """
        SELECT r.id, r.code, r.name, r.description
        FROM   user_roles ur
        JOIN   roles      r ON r.id = ur.role_id
        WHERE  ur.user_id = ?
        ORDER BY r.code
        """,
        (user_id,),
    ).fetchall()
    return [dict(f) for f in filas]


def list_roles(conn=None):
    """
    El catalogo de roles con su nombre legible y su descripcion.

    Lo consumen los formularios de asignacion: la casilla muestra
    "Administrador - Gestiona cuentas y ve las metricas del sistema", no el
    codigo `admin`. La descripcion sale de la BASE, no del HTML, para que no
    haya dos versiones del mismo texto.
    """
    filas = _conn(conn).execute(
        "SELECT id, code, name, description FROM roles ORDER BY code"
    ).fetchall()
    return [dict(f) for f in filas]


def list_users(search=None, limit=None, offset=0, conn=None):
    """
    H2 de REVISION_BD_ESCALABILIDAD: SIEMPRE con LIMIT. Era la unica consulta
    del sistema sin acotar, y con 500 cuentas devolveria las 500.

    Cada dict trae `roles`: la lista de codigos ya partida.
    """
    limit = config.USUARIOS_POR_PAGINA if limit is None else limit
    parametros = []

    filtro = ""
    if search:
        patron = _patron_like(search)
        filtro = """
            WHERE u.username  LIKE ? ESCAPE '\\'
               OR u.email     LIKE ? ESCAPE '\\'
               OR u.full_name LIKE ? ESCAPE '\\'
        """
        parametros += [patron, patron, patron]

    parametros += [limit, offset]

    # GROUP_CONCAT es de SQLite; en PostgreSQL seria string_agg(r.code, ','].
    # Queda aislado aqui a proposito (H4): es el unico sitio que habria que
    # tocar si el proyecto migrara de motor.
    filas = _conn(conn).execute(
        f"""
        SELECT u.id, u.username, u.email, u.full_name, u.is_active,
               u.created_at, GROUP_CONCAT(r.code, ',') AS roles_csv
        FROM       users      u
        LEFT JOIN  user_roles ur ON ur.user_id = u.id
        LEFT JOIN  roles      r  ON r.id       = ur.role_id
        {filtro}
        GROUP BY u.id
        ORDER BY u.username
        LIMIT ? OFFSET ?
        """,
        parametros,
    ).fetchall()

    usuarios = []
    for fila in filas:
        usuario = dict(fila)
        csv = usuario.pop("roles_csv") or ""
        usuario["roles"] = sorted(c for c in csv.split(",") if c)
        usuarios.append(usuario)
    return usuarios


def count_users(search=None, conn=None):
    """El total para la paginacion. Mismo filtro que list_users o los numeros mienten."""
    if search:
        patron = _patron_like(search)
        fila = _conn(conn).execute(
            """
            SELECT COUNT(*) AS total FROM users
            WHERE username  LIKE ? ESCAPE '\\'
               OR email     LIKE ? ESCAPE '\\'
               OR full_name LIKE ? ESCAPE '\\'
            """,
            (patron, patron, patron),
        ).fetchone()
    else:
        fila = _conn(conn).execute("SELECT COUNT(*) AS total FROM users").fetchone()
    return fila["total"]


def count_admins(conn=None):
    """Administradores ACTIVOS. Una cuenta desactivada no puede administrar nada."""
    return _contar_admins(_conn(conn))


def _contar_admins(db):
    fila = db.execute(
        """
        SELECT COUNT(DISTINCT u.id) AS total
        FROM   users      u
        JOIN   user_roles ur ON ur.user_id = u.id
        JOIN   roles      r  ON r.id       = ur.role_id
        WHERE  r.code = 'admin' AND u.is_active = 1
        """
    ).fetchone()
    return fila["total"]


def exists_username(username, excluir_id=None, conn=None):
    """`excluir_id` evita que una cuenta choque consigo misma al editarse."""
    fila = _conn(conn).execute(
        "SELECT 1 FROM users WHERE username = ? AND id IS NOT ?", (username, excluir_id)
    ).fetchone()
    return fila is not None


def exists_email(email, excluir_id=None, conn=None):
    fila = _conn(conn).execute(
        "SELECT 1 FROM users WHERE email = ? AND id IS NOT ?", (email, excluir_id)
    ).fetchone()
    return fila is not None


# --------------------------------------------------------------------------
# Escritura
# --------------------------------------------------------------------------
def _vincular_roles(db, user_id, role_codes, granted_by=None):
    """
    H4: ON CONFLICT ... DO NOTHING en vez de INSERT OR IGNORE, que es sintaxis
    exclusiva de SQLite. Un rol que no existe en el catalogo se ignora.
    """
    for code in role_codes:
        db.execute(
            """
            INSERT INTO user_roles (user_id, role_id, granted_by)
            SELECT ?, r.id, ? FROM roles r WHERE r.code = ?
            ON CONFLICT (user_id, role_id) DO NOTHING
            """,
            (user_id, granted_by, code),
        )


def create_user(datos, role_codes, granted_by=None, conn=None):
    """
    Crea la cuenta Y sus roles en la MISMA transaccion.

    No es un detalle de estilo: una cuenta sin roles es una cuenta sin ningun
    permiso, imposible de usar y que ademas no aparece como rota. Si la
    segunda mitad falla, no debe quedar la primera.

    Devuelve el id, o None si el usuario o el correo ya existian.
    """
    db = _conn(conn)
    try:
        db.execute("BEGIN IMMEDIATE")
        cursor = db.execute(
            """
            INSERT INTO users (username, email, password_hash, full_name)
            VALUES (?, ?, ?, ?)
            """,
            (
                datos["username"],
                datos["email"],
                generate_password_hash(datos["password"], method=config.PASSWORD_HASH_METHOD),
                datos.get("full_name", ""),
            ),
        )
        user_id = cursor.lastrowid
        _vincular_roles(db, user_id, role_codes, granted_by)
        db.commit()
        return user_id
    except sqlite3.IntegrityError:
        # Choque con el UNIQUE de username o email. La ruta lo traduce a un 409.
        db.rollback()
        return None
    except Exception:
        db.rollback()
        raise


def assign_roles(user_id, role_codes, granted_by=None, conn=None):
    """
    Reemplaza el juego de roles de una cuenta.

    Se aplica el cambio y DESPUES se cuenta, todo dentro de la transaccion: si
    el resultado deja el sistema sin administradores activos, se deshace y se
    lanza SinAdministradores. Comprobar antes de escribir seria adivinar; esto
    es mirar el resultado real (TC-10).
    """
    db = _conn(conn)
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
        _vincular_roles(db, user_id, role_codes, granted_by)

        if _contar_admins(db) == 0:
            db.rollback()
            raise SinAdministradores()

        db.commit()
        return True
    except SinAdministradores:
        raise
    except Exception:
        db.rollback()
        raise


def set_active(user_id, is_active, conn=None):
    """
    Activa o desactiva. Desactivar NO es borrar: las tareas y los eventos de la
    cuenta siguen existiendo y vuelven en cuanto se reactiva (TC-05).
    """
    db = _conn(conn)
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id))

        if _contar_admins(db) == 0:
            db.rollback()
            raise SinAdministradores()

        db.commit()
        return True
    except SinAdministradores:
        raise
    except Exception:
        db.rollback()
        raise


def set_password(user_id, password, conn=None):
    """Asigna una contrasena nueva. La anterior no se puede leer ni recuperar."""
    db = _conn(conn)
    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(password, method=config.PASSWORD_HASH_METHOD), user_id),
    )
    db.commit()
    return True


def update_profile(user_id, full_name, email, conn=None):
    """Los dos unicos campos que una cuenta puede cambiarse a si misma."""
    db = _conn(conn)
    try:
        db.execute(
            "UPDATE users SET full_name = ?, email = ? WHERE id = ?",
            (full_name, email, user_id),
        )
        db.commit()
        return True
    except sqlite3.IntegrityError:
        db.rollback()
        return False


def verify_password(usuario, password):
    """
    Comprueba la contrasena gastando el mismo tiempo exista o no la cuenta.

    El `else` no es decorativo: si se saliera antes cuando `usuario` es None,
    la respuesta a un usuario inexistente llegaria medibles milisegundos antes
    que la de uno real, y eso permite enumerar las cuentas del sistema con un
    cronometro. Es el mismo motivo por el que el mensaje de error es identico
    en los dos casos.
    """
    if usuario is None:
        check_password_hash(_HASH_SENUELO, password or "")
        return False
    return check_password_hash(usuario["password_hash"], password or "")
