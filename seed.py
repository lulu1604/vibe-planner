"""
VibePlanner v2 - Semilla (seed.py)
----------------------------------
DUENO DE ESTE ARCHIVO: Piero Calderon (Modulo A - Nucleo)

Siembra el catalogo de permisos, los roles y el administrador inicial.

    python seed.py

ES IDEMPOTENTE A PROPOSITO. Cada vez que un modulo anade un permiso nuevo, se
vuelve a ejecutar y queda sembrado sin duplicar nada. Un permiso que existe en
un decorador `@requires(...)` pero no en la tabla es un 403 permanente que
nadie sabra explicar -- por eso test_v2.py comprueba justamente eso.

NUNCA se ejecuta al importar. Sembrar es un acto manual y consciente: si
wsgi_pythonanywhere.py lo llamara solo, cada reinicio del servidor tocaria la
base de datos de produccion.
"""

import os
import sys

import config
import database
import repo_users

# --------------------------------------------------------------------------
# Los 23 permisos.  (codigo, modulo, descripcion)
# El codigo es lo que comprueban los decoradores; la descripcion es lo que se
# le ensena a una persona en el panel de administracion.
# --------------------------------------------------------------------------
PERMISOS = [
    # --- Perfil propio -----------------------------------------------------
    ("perfil.ver",            "nucleo",     "Ver su propio perfil"),
    ("perfil.editar",         "nucleo",     "Editar su perfil y su contrasena"),
    # --- Planner (Modulo B) ------------------------------------------------
    ("planner.ver",           "planner",    "Ver su plan del dia"),
    ("planner.crear",         "planner",    "Crear actividades"),
    ("planner.editar",        "planner",    "Editar sus actividades"),
    ("planner.eliminar",      "planner",    "Eliminar sus actividades"),
    ("kanban.ver",            "planner",    "Ver el tablero Kanban"),
    ("kanban.mover",          "planner",    "Mover actividades entre columnas"),
    ("tarea.asignar",         "planner",    "Asignar tareas a otros integrantes"),
    # --- Calendario (Modulo C) --------------------------------------------
    ("calendario.ver",        "calendario", "Ver el calendario mensual"),
    ("evento.crear",          "calendario", "Crear eventos"),
    ("evento.editar",         "calendario", "Editar sus eventos"),
    ("evento.eliminar",       "calendario", "Eliminar sus eventos"),
    ("invitacion.responder",  "calendario", "Aceptar o rechazar invitaciones"),
    # --- Habitos y metricas propias (Modulo D) -----------------------------
    ("habito.ver",            "habitos",    "Ver sus habitos y rachas"),
    ("habito.crear",          "habitos",    "Crear habitos"),
    ("habito.registrar",      "habitos",    "Registrar el cumplimiento diario"),
    ("metrica.propia.ver",    "metricas",   "Ver sus propias metricas"),
    # --- Administracion (Modulo A) ----------------------------------------
    ("usuario.listar",        "admin",      "Ver la lista de cuentas"),
    ("usuario.crear",         "admin",      "Crear cuentas"),
    ("usuario.editar",        "admin",      "Editar cuentas y restablecer contrasenas"),
    ("usuario.desactivar",    "admin",      "Activar y desactivar cuentas"),
    ("rol.asignar",           "admin",      "Asignar roles a una cuenta"),
    ("metrica.sistema.ver",   "admin",      "Ver las metricas de todo el sistema"),
]

# --------------------------------------------------------------------------
# Los 2 roles.  (codigo, nombre visible, descripcion, permisos)
#
# OJO CON LO AGREGATIVO: `admin` NO repite los 17 permisos de `usuario`.
# Se suman solos, porque el administrador lleva LOS DOS roles. Repetirlos aqui
# funcionaria igual hoy y seria una mentira sobre como funciona el modelo.
# --------------------------------------------------------------------------
ROLES = [
    (
        "usuario",
        "Usuario",
        "Usa la aplicacion: su planner, calendario y habitos.",
        [c for c, m, _ in PERMISOS if m != "admin"],
    ),
    (
        "admin",
        "Administrador",
        "Gestiona cuentas y ve las metricas del sistema.",
        [c for c, m, _ in PERMISOS if m == "admin"],
    ),
]

ADMIN_POR_DEFECTO = {
    "username": os.environ.get("VIBEPLANNER_ADMIN_USER", "admin"),
    "email": os.environ.get("VIBEPLANNER_ADMIN_EMAIL", "admin@vibeplanner.local"),
    "password": os.environ.get("VIBEPLANNER_ADMIN_PASS", "CambiarEsto2026!"),
    "full_name": "Administrador del sistema",
}


def sembrar_permisos(db):
    for code, module, description in PERMISOS:
        db.execute(
            """
            INSERT INTO permissions (code, module, description) VALUES (?, ?, ?)
            ON CONFLICT (code) DO UPDATE SET module = excluded.module,
                                            description = excluded.description
            """,
            (code, module, description),
        )
    return len(PERMISOS)


def sembrar_roles(db):
    for code, name, description, permisos in ROLES:
        db.execute(
            """
            INSERT INTO roles (code, name, description) VALUES (?, ?, ?)
            ON CONFLICT (code) DO UPDATE SET name = excluded.name,
                                             description = excluded.description
            """,
            (code, name, description),
        )
        # Se reconstruye el juego de permisos del rol: asi, quitar un permiso
        # de la lista de arriba tambien lo quita de la base al re-sembrar.
        db.execute(
            "DELETE FROM role_permissions WHERE role_id = (SELECT id FROM roles WHERE code = ?)",
            (code,),
        )
        for permiso in permisos:
            db.execute(
                """
                INSERT INTO role_permissions (role_id, permission_id)
                SELECT r.id, p.id FROM roles r, permissions p
                WHERE  r.code = ? AND p.code = ?
                ON CONFLICT (role_id, permission_id) DO NOTHING
                """,
                (code, permiso),
            )
    return len(ROLES)


def sembrar_admin(db):
    """Crea el administrador inicial si no existe. Lleva los DOS roles."""
    existente = repo_users.get_by_username(ADMIN_POR_DEFECTO["username"], conn=db)
    if existente:
        return existente["id"], False

    user_id = repo_users.create_user(
        ADMIN_POR_DEFECTO, ["usuario", "admin"], granted_by=None, conn=db
    )
    return user_id, True


def main():
    database.init_db()
    db = database.raw_connection()
    try:
        n_permisos = sembrar_permisos(db)
        n_roles = sembrar_roles(db)
        db.commit()

        admin_id, creado = sembrar_admin(db)

        print(f"  {n_permisos} permisos sembrados")
        print(f"  {n_roles} roles sembrados (usuario, admin)")
        if creado:
            print(f"  administrador '{ADMIN_POR_DEFECTO['username']}' creado (id {admin_id})")
        else:
            print(f"  administrador '{ADMIN_POR_DEFECTO['username']}' ya existia (id {admin_id})")

        permisos_admin = repo_users.get_permissions(admin_id, conn=db)
        print(f"  permisos efectivos del administrador: {len(permisos_admin)} "
              f"(union de sus dos roles)")

        if ADMIN_POR_DEFECTO["password"] == "CambiarEsto2026!":
            print()
            print("  AVISO: se uso la contrasena por defecto del administrador.")
            print("  En produccion define VIBEPLANNER_ADMIN_PASS antes de sembrar,")
            print("  o cambiala desde el perfil nada mas entrar.")
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
