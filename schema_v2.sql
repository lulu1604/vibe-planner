-- =====================================================================
-- VibePlanner v2 - schema_v2.sql
-- MODULO A (Nucleo) - Piero Calderon & MODULO C (Calendario) - Jose Cabrera
-- Coordinado con Jose Cabrera, dueno unico del esquema.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. Cuentas
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT      NOT NULL UNIQUE COLLATE NOCASE,
    email         TEXT      NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT      NOT NULL,
    full_name     TEXT      NOT NULL DEFAULT '',
    is_active     INTEGER   NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ---------------------------------------------------------------------
-- 2. Catalogo de roles  (v2.1: solo `usuario` y `admin`)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT      NOT NULL UNIQUE COLLATE NOCASE,
    name        TEXT      NOT NULL,
    description TEXT      NOT NULL DEFAULT '',
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ---------------------------------------------------------------------
-- 3. Catalogo de permisos
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS permissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    module      TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT ''
);


-- ---------------------------------------------------------------------
-- 4. Que puede hacer cada rol
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id       INTEGER NOT NULL REFERENCES roles(id)       ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);


-- ---------------------------------------------------------------------
-- 5. Que roles lleva cada cuenta  -- MODELO AGREGATIVO
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_roles (
    user_id    INTEGER   NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id    INTEGER   NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    granted_by INTEGER            REFERENCES users(id) ON DELETE SET NULL,
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);


-- ---------------------------------------------------------------------
-- 6. MÓDULO C: Eventos e Invitaciones
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id    INTEGER NOT NULL,
    title       TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    start_at    TEXT    NOT NULL,                  -- 'YYYY-MM-DD HH:MM'
    end_at      TEXT    NOT NULL,                  -- 'YYYY-MM-DD HH:MM'
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


-- ---------------------------------------------------------------------
-- 7. MODULO B: Tareas del Planner y Kanban (Lucero Ayala)
--    Extiende la tabla `tasks` de la v1 con user_id y kanban_column.
--    CREATE TABLE IF NOT EXISTS es aditivo: no afecta la v1.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tasks_v2 (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL,
    title             TEXT    NOT NULL,
    description       TEXT    NOT NULL DEFAULT '',
    category          TEXT    NOT NULL DEFAULT 'General',
    priority_level    INTEGER NOT NULL DEFAULT 2,          -- 1 Alta, 2 Media, 3 Baja
    due_date          TEXT    NOT NULL,                    -- YYYY-MM-DD
    estimated_minutes INTEGER NOT NULL DEFAULT 30,
    kanban_column     TEXT    NOT NULL DEFAULT 'todo',     -- backlog|todo|ongoing|done
    start_time        TEXT    DEFAULT NULL,                -- HH:MM  (opcional, US8)
    end_time          TEXT    DEFAULT NULL,                -- HH:MM  (opcional, US8)
    assigned_by       INTEGER DEFAULT NULL,                -- user_id de quien asigno (US10)
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (kanban_column IN ('backlog','todo','ongoing','done')),
    CHECK (priority_level IN (1, 2, 3)),
    FOREIGN KEY (user_id)     REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- 8. Indices
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_user_roles_role        ON user_roles(role_id);
CREATE INDEX IF NOT EXISTS ix_role_permissions_perm  ON role_permissions(permission_id);
CREATE INDEX IF NOT EXISTS ix_users_active           ON users(is_active);
CREATE INDEX IF NOT EXISTS ix_events_owner_start     ON events(owner_id, start_at);
CREATE INDEX IF NOT EXISTS ix_tasks_v2_user_date     ON tasks_v2(user_id, due_date);
CREATE INDEX IF NOT EXISTS ix_tasks_v2_assigned_by   ON tasks_v2(assigned_by);

-- Un usuario no puede aceptar dos veces el mismo evento (TC-32).
CREATE UNIQUE INDEX IF NOT EXISTS ux_invitation_event_user
    ON event_invitations(event_id, invited_user_id)
    WHERE invited_user_id IS NOT NULL;


-- ---------------------------------------------------------------------
-- 8. Trigger updated_at automatico
-- ---------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_users_updated
AFTER UPDATE ON users FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
