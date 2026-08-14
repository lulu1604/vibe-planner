-- =====================================================================
-- VibePlanner v2 - schema_v2.sql
-- MODULO A (Nucleo) - Piero Calderon
-- Coordinado con Jose Cabrera, dueno unico del esquema.
--
-- ALCANCE DE ESTE ARCHIVO -- leer antes de anadir nada:
--   Aqui viven SOLO las 5 tablas de identidad. Es deliberado.
--   Este esquema se mergea a `main` mientras la v1 sigue en produccion, asi
--   que tiene que ser ESTRICTAMENTE ADITIVO: anadir `user_id NOT NULL` a
--   `tasks` hoy tumbaria add_task(), que no lo envia, y con el las 5 rutas
--   de la v1. Las tablas de los modulos B (tasks v2), C (events) y D
--   (habits) las anade Jose el dia de la migracion coordinada, cuando todos
--   borran su vibe_planner.db a la vez.
--
-- Arreglos de REVISION_BD_ESCALABILIDAD.md ya aplicados:
--   H1  COLLATE NOCASE en username y email
--   H3  updated_at + trigger (SQLite no tiene ON UPDATE CURRENT_TIMESTAMP)
--   H4  las escrituras usan ON CONFLICT ... DO NOTHING (portable a PostgreSQL)
--
-- OJO: las FOREIGN KEY de este archivo solo se respetan si la conexion trae
-- `PRAGMA foreign_keys = ON`. No es persistente: hay que ponerlo en CADA
-- conexion. Sin el, SQLite las ignora en silencio.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. Cuentas
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    -- H1: sin COLLATE NOCASE, 'Piero' y 'piero' serian dos cuentas distintas.
    username      TEXT      NOT NULL UNIQUE COLLATE NOCASE,
    email         TEXT      NOT NULL UNIQUE COLLATE NOCASE,
    -- Nunca la contrasena: solo su hash. Ver config.PASSWORD_HASH_METHOD.
    password_hash TEXT      NOT NULL,
    full_name     TEXT      NOT NULL DEFAULT '',
    -- Desactivar NO es borrar: las tareas y eventos de la cuenta sobreviven.
    is_active     INTEGER   NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ---------------------------------------------------------------------
-- 2. Catalogo de roles  (v2.1: solo `usuario` y `admin`)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT      NOT NULL UNIQUE COLLATE NOCASE,  -- 'usuario', 'admin'
    name        TEXT      NOT NULL,                        -- 'Usuario', 'Administrador'
    description TEXT      NOT NULL DEFAULT '',
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ---------------------------------------------------------------------
-- 3. Catalogo de permisos
--    Los decoradores comprueban ESTOS codigos, nunca nombres de rol.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS permissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE COLLATE NOCASE,  -- 'usuario.listar'
    module      TEXT NOT NULL,                        -- 'nucleo', 'planner', ...
    description TEXT NOT NULL DEFAULT ''
);


-- ---------------------------------------------------------------------
-- 4. Que puede hacer cada rol
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id       INTEGER NOT NULL REFERENCES roles(id)       ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    -- La clave primaria compuesta es tambien el destino del ON CONFLICT (H4).
    PRIMARY KEY (role_id, permission_id)
);


-- ---------------------------------------------------------------------
-- 5. Que roles lleva cada cuenta  -- AQUI VIVE EL MODELO AGREGATIVO
--    Un usuario puede tener varias filas aqui. Sus permisos son la UNION.
--    Por eso el administrador es tambien un usuario normal: lleva los dos.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_roles (
    user_id    INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id    INTEGER   NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    -- Quien lo concedio. SET NULL: si esa cuenta se borra, el rol sigue.
    granted_by INTEGER            REFERENCES users(id) ON DELETE SET NULL,
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);


-- ---------------------------------------------------------------------
-- 6. Indices
--    Los UNIQUE de username/email ya crean su indice: no se repiten aqui.
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_user_roles_role       ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS ix_role_permissions_perm ON role_permissions(permission_id);
CREATE INDEX IF NOT EXISTS ix_users_active          ON users(is_active);


-- ---------------------------------------------------------------------
-- 7. H3: updated_at automatico
--     SQLite no tiene ON UPDATE CURRENT_TIMESTAMP. El guard `WHEN` evita que
--     el trigger se dispare a si mismo si alguien activa recursive_triggers.
-- ---------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_users_updated
AFTER UPDATE ON users FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
