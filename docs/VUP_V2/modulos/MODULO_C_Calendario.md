# 📅 MÓDULO C — Calendario, horario e invitaciones

**Dueño propuesto:** Jose Cabrera *(sigue siendo el dueño único del esquema SQL)*
**Historias:** US11 (horario mensual) · US12 (invitación por link)
**Depende de:** Módulo A — arranca en cuanto `security.py` esté en `main` (hito H2)

---

## 🎯 Qué construyes

El módulo para proyectarse: una cuadrícula mensual navegable donde el usuario crea
eventos con nombre, descripción, horario y color, y un sistema de invitaciones que
funciona **sin enviar un solo correo** — el anfitrión genera un link, lo copia y
lo comparte por donde quiera. PythonAnywhere free tier no permite SMTP saliente, y
esta es la solución que cumple el requisito sin red externa.

**Doble responsabilidad:** además de este módulo, sigues siendo el **dueño único
del esquema**. Si `schema_v2.sql` cambia, lo cambias tú y **avisas al grupo**,
porque todos tienen que borrar su `vibe_planner.db` local y regenerarlo.

---

## 📁 Archivos que te pertenecen

| Archivo | Qué contiene |
|---|---|
| `repo_events.py` | Único componente que toca `events` y `event_invitations` |
| `calendar_bp.py` | Blueprint: `/calendario`, `/eventos/*`, `/invitacion/<token>` |
| `templates/calendario/mes.html` | Cuadrícula mensual |
| `templates/calendario/evento_form.html` | Alta y edición |
| `templates/calendario/invitacion.html` | Pantalla de aceptación |
| `static/js/calendario.js` | Navegación entre meses |
| `schema_v2.sql` | 🔑 **Dueño único** — coordinado con Piero |

> 📌 El archivo se llama `calendar_bp.py`, **no** `calendar.py`. `calendar` es un
> módulo de la librería estándar de Python y llamarlo igual provoca un import
> circular difícil de diagnosticar.

---

## 📋 Pasos, en orden

### 1. `repo_events.py` — contrato congelado

```python
def list_month(user_id, year, month)      -> list[dict]   # propios + aceptados
def list_day(user_id, date_iso)           -> list[dict]   # lo consume el Módulo D
def get_owned(event_id, user_id)          -> dict | None
def create(data, owner_id)                -> int
def update_owned(event_id, user_id, data) -> bool
def delete_owned(event_id, user_id)       -> bool
def create_invitation(event_id)           -> str          # token
def get_event_by_token(token)             -> dict | None
def accept_invitation(token, user_id)     -> bool         # idempotente
def count_attendees(event_id)             -> int
```

`list_month()` devuelve **dos cosas a la vez**: los eventos propios y aquellos
cuya invitación el usuario aceptó. Es la única consulta del módulo con `UNION`:

```sql
SELECT e.*, 'propio' AS origen, NULL AS anfitrion
FROM   events e
WHERE  e.owner_id = ? AND e.start_at >= ? AND e.start_at < ?
UNION
SELECT e.*, 'invitado' AS origen, u.username AS anfitrion
FROM   events e
JOIN   event_invitations i ON i.event_id = e.id
JOIN   users u             ON u.id       = e.owner_id
WHERE  i.invited_user_id = ? AND i.status = 'accepted'
   AND e.start_at >= ? AND e.start_at < ?
ORDER  BY start_at;
```

El rango del mes se calcula con `'YYYY-MM-01'` inclusive y el primer día del mes
siguiente exclusive. **No uses `LIKE 'YYYY-MM%'`**: no aprovecha el índice
`ix_events_owner_start` y falla en cuanto el formato cambie.

### 2. `/calendario/<año>/<mes>` — la cuadrícula (US11)

- Semana de **lunes a domingo**.
- Rellena los días del mes anterior y siguiente para completar las 6 filas.
- Cada celda muestra hasta 3 eventos y "+N más" si hay más.
- Cada evento con su hora de inicio y su color.
- Navegación anterior / siguiente / hoy.

**El cruce de año es donde falla todo el mundo:** diciembre → siguiente = enero
del año siguiente; enero → anterior = diciembre del anterior. Pruébalo (TC-26).
Usa `calendar.monthrange()` de la librería estándar en vez de calcular los días a
mano.

### 3. Validación de eventos

```python
if end_at <= start_at:
    error = "La hora de fin debe ser posterior a la de inicio."
```

Valídalo **en el servidor**. El `CHECK (end_at > start_at)` del esquema es la
segunda barrera, no la primera: un `CHECK` que salta produce un error 500 feo, no
un mensaje útil (TC-27).

El color se valida contra `config.ALLOWED_COLORS`. Un color libre rompe la
coherencia visual del design system y permite inyectar CSS en el atributo `style`.

### 4. Invitaciones por link (US12)

```python
import secrets

def create_invitation(event_id):
    token = secrets.token_urlsafe(32)
    ...
```

**Nunca un id incremental.** Con `/invitacion/1`, `/invitacion/2` cualquiera
recorre todas las invitaciones del sistema. `secrets.token_urlsafe(32)` es
librería estándar y criptográficamente seguro.

Cuatro comportamientos obligatorios:

| Caso | Comportamiento | Test |
|---|---|---|
| Token inexistente o revocado | "Esta invitación no es válida o fue cancelada". **Sin revelar título, fecha ni anfitrión** | TC-30 |
| Visitante sin sesión | Se guarda el destino, va al login, y **vuelve solo** a la aceptación | TC-31 |
| Aceptar dos veces | Una sola fila; el contador de asistentes no sube | TC-32 |
| Aceptar correcto | El evento aparece en el calendario del invitado con "Invitado por \<anfitrión\>" | TC-29 |

El retorno automático tras el login ya está resuelto en `security.py`: el
decorador guarda `session["next"]` y `auth.login_route()` redirige ahí. **Tú solo
tienes que poner `@login_required` en la ruta de aceptación** y no reinventarlo.

### 5. Aceptación idempotente

```python
def accept_invitation(token, user_id):
    inv = _get_by_token(token)
    if inv is None or inv["status"] == "revoked":
        return False
    existing = db.execute(
        """SELECT 1 FROM event_invitations
           WHERE event_id = ? AND invited_user_id = ? AND status = 'accepted'""",
        (inv["event_id"], user_id),
    ).fetchone()
    if existing:
        return True          # ya estaba aceptada: éxito, sin insertar nada
    ...
```

El índice único `ux_invitation_event_user` te respalda, pero comprueba tú primero:
dejar que salte una `IntegrityError` funciona, pero convierte un caso normal en
una excepción.

---

## 🕳️ Trampas concretas de este módulo

1. **`calendar_bp.py`, no `calendar.py`.** Colisiona con la librería estándar.
2. **Cruce de año en la navegación.** Diciembre + 1 = enero del año siguiente.
3. **Meses de 28, 30 y 31 días.** Usa `calendar.monthrange()`, no aritmética manual.
4. **Rango del mes con `>=` y `<`, no con `LIKE`.** Aprovecha el índice.
5. **El token nunca es un id incremental.**
6. **La pantalla de token inválido no filtra nada** del evento (TC-30).
7. **Las dos llaves también aquí:** `get_owned(event_id, user_id)` con el
   `owner_id` dentro del `WHERE`. Editar un evento ajeno → 404.
8. **El calendario de otro no se ve nunca** (TC-28): `list_month()` solo devuelve
   propios y aceptados.
9. **Como dueño del esquema:** si cambias `schema_v2.sql`, avisa al grupo el mismo
   día. Todos borran y regeneran su base local.

---

## ✅ Listo cuando

- [ ] Un evento creado el 27 aparece en la celda del 27 con su hora y su color (TC-25)
- [ ] La navegación funciona entre meses **y entre años** (TC-26)
- [ ] Fin ≤ inicio se rechaza con mensaje útil, no con un 500 (TC-27)
- [ ] `ana` ve 0 eventos de `jose` (TC-28)
- [ ] `piero` invita, `ana` acepta, el evento sale en su calendario (TC-29)
- [ ] Un token inválido no revela nada del evento (TC-30)
- [ ] Sin sesión, el link lleva al login y **regresa solo** (TC-31)
- [ ] Aceptar dos veces no duplica ni sube el contador (TC-32)
- [ ] La cuadrícula se ve bien a 360 px, 768 px y 1280 px
- [ ] Tus asserts añadidos a `test_v2.py` pasan
