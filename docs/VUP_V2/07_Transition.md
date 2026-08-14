# 📋 VUP Phase 7: Transition Phase Document

**Project Name:** VibePlanner — Multi-User Activity Planner with Transparent Prioritization
**Version:** 2.0 (Update — Multiusuario, Roles y Permisos)
**Phase:** Transition Phase (Deployment, Verification & Hand-off)
**Deployment Platform:** PythonAnywhere (WSGI Linux Hosting, free tier)

---

## 🌐 1. Plataforma de despliegue

| Elemento | Valor |
|---|---|
| Proveedor | PythonAnywhere — WSGI Python Hosting |
| Entorno | Linux free tier · Python 3.10+ · SQLite3 local |
| Coste | **$0.00 / mes** — cero APIs externas, cero base de datos en la nube |
| URL de producción | `http://<usuario>.pythonanywhere.com` *(completar al desplegar)* |
| Restricción relevante | Sin red saliente fuera de la lista permitida → **sin CDN, sin SMTP**. Todo se auto-aloja |

**Por qué sigue siendo viable en la v2:** añadir cuentas, roles y permisos no
introduce ninguna dependencia de red. Las contraseñas se hashean en el propio
servidor con `werkzeug`, los tokens de invitación se generan con `secrets`, y las
fuentes viven en `static/fonts/`. El único componente que la v2 añade a la
infraestructura es una **variable de entorno**.

---

## ⚙️ 2. Instrucciones de despliegue

### 2.1 Primer despliegue

```bash
# 1. Clonar en una consola Bash de PythonAnywhere
git clone https://github.com/<org>/vibe-planner.git
cd ~/vibe-planner

# 2. Entorno virtual (recomendado sobre pip --user: aísla la versión de Flask)
python3 -m venv ~/.virtualenvs/vibeplanner
source ~/.virtualenvs/vibeplanner/bin/activate
pip install -r requirements.txt

# 3. Crear el esquema y sembrar roles, permisos y el administrador inicial
python seed.py
```

### 2.2 Variables de entorno — **el paso que no se puede saltar**

En el panel **Web → Environment variables** de PythonAnywhere:

| Variable | Valor | Por qué |
|---|---|---|
| `VIBEPLANNER_SECRET` | una cadena larga y aleatoria | Firma las cookies de sesión. Con el valor por defecto cualquiera puede falsificar una sesión |
| `VIBEPLANNER_ADMIN_USER` | el usuario del administrador | Se usa una sola vez, al sembrar |
| `VIBEPLANNER_ADMIN_EMAIL` | un correo real del equipo | Se usa una sola vez, al sembrar |
| `VIBEPLANNER_ADMIN_PASS` | una contraseña real | **Si se queda la de por defecto, la aplicación queda abierta** |

Generar el secreto:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

> ⚠️ **Las variables del panel Web no llegan a la consola Bash.** Como `seed.py` se
> ejecuta desde la consola, hay que exportarlas también ahí antes de sembrar, o el
> administrador se creará con los valores por defecto:
>
> ```bash
> export VIBEPLANNER_ADMIN_USER='admin'
> export VIBEPLANNER_ADMIN_EMAIL='vibeplanner@esan.pe'
> export VIBEPLANNER_ADMIN_PASS='la-que-pusiste-en-el-panel'
> ```

> ⚠️ Estas variables **nunca** se escriben en el repositorio. Lo que entra al
> historial de Git es público para siempre, aunque después se borre el archivo.
> Es el riesgo R10 de Inception.

### 2.3 Archivo WSGI

En `/var/www/<usuario>_pythonanywhere_com_wsgi.py`:

```python
import os
import sys

path = "/home/<usuario>/vibe-planner"
if path not in sys.path:
    sys.path.append(path)

# Respaldo por si las variables del panel no se propagan al proceso WSGI
os.environ.setdefault("VIBEPLANNER_SECRET", os.environ.get("VIBEPLANNER_SECRET", ""))

from app import app as application   # noqa: E402
```

**Por eso la instancia se llama `app` y no hay application factory:** este archivo
es el contrato con la plataforma, y no queremos depurarlo en producción — que es
justo donde el free tier no ofrece entorno de staging.

### 2.4 Reglas de la base de datos

- `vibe_planner.db` vive en la raíz del proyecto, **fuera de `/static`**, para que
  no se pueda descargar por HTTP. Un fichero SQLite servido públicamente entrega
  todos los hashes de contraseña de golpe.
- Está en `.gitignore`. Nunca se sube.
- `database.init_db()` se ejecuta al importar el módulo, así que un arranque en
  frío del WSGI garantiza el esquema.
- `PRAGMA journal_mode = WAL` queda activo desde la primera conexión y permite
  lecturas concurrentes mientras alguien escribe (riesgo R8).

### 2.5 Migrar una instalación v1 existente

```bash
cp vibe_planner.db vibe_planner_v1_backup.db      # copia ANTES de nada
sqlite3 vibe_planner.db "ALTER TABLE tasks RENAME TO tasks_v1;"
python seed.py
python migrate_v1_to_v2.py --owner admin
```

Los estados se mapean `pending → todo`, `in_progress → ongoing`,
`completed → done`, y las tareas huérfanas quedan adoptadas por la cuenta
indicada. **Todo el equipo borra y regenera su base local el mismo día**, con
aviso previo del dueño del esquema.

### 2.6 Redespliegue

```bash
cd ~/vibe-planner && git pull origin main
source ~/.virtualenvs/vibeplanner/bin/activate && pip install -r requirements.txt
python seed.py          # idempotente: actualiza permisos nuevos sin duplicar nada
# Botón "Reload" en la pestaña Web
```

`seed.py` es idempotente **a propósito**: cada vez que un módulo añade un permiso,
basta con volver a ejecutarlo para que exista en la tabla. Un permiso que se usa
en un decorador pero no está sembrado es un 403 permanente que nadie sabrá
explicar.

---

## 📚 3. Análisis del código generado (`codeAnalysis`)

### 3.1 Lo que la v2 cambió en la arquitectura

**De 4 componentes a 11, y por qué no es complejidad gratuita.** La v1 cabía en
tres archivos porque solo tenía un usuario y un caso de uso. En cuanto aparecen
cuentas, cada consulta necesita saber *de quién* son los datos. La respuesta fácil
—repartir `if session["user_id"]` por todo el código— es exactamente la que
produce agujeros. La respuesta que tomamos fue concentrar la decisión en un solo
archivo (`security.py`, menos de 150 líneas) y hacer que los repositorios lleven
el `user_id` **dentro del `WHERE`**.

**La regla de las dos llaves.** El aprendizaje técnico más transferible de esta
versión: *tener el permiso no es ser el dueño del dato*. Un `@requires("planner.editar")`
dice que la persona puede editar tareas; no dice **cuáles**. La segunda llave la
pone la consulta:

```python
SELECT * FROM tasks WHERE id = ? AND user_id = ?
```

Si la fila no es tuya, la base de datos no te la entrega y el controlador responde
**404** — no 403, porque un 403 confirmaría al atacante que ese id existe y le
permitiría enumerar los registros de los demás. Esta sugerencia vino de la IA y la
aceptamos: no se nos había ocurrido.

**Roles agregativos en una sola consulta.** Todo el requisito central de la v2 —
que un administrador sea también un usuario normal— se resuelve con:

```sql
SELECT DISTINCT p.code
FROM user_roles ur
JOIN role_permissions rp ON rp.role_id = ur.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE ur.user_id = ?;
```

La alternativa "simple" que la IA propuso primero —una columna `role` de texto en
`users`— habría hecho el requisito **imposible**: habría obligado a elegir entre
ser admin o ser usuario, o a crear cuentas duplicadas. Merece la pena repetirlo:
la decisión de modelado que parece más complicada al principio fue la que hizo el
resto del trabajo sencillo.

**Permisos resueltos por petición, no en la cookie.** Guardarlos en la sesión
"para ahorrar consultas" habría hecho que revocar un rol no tuviera efecto hasta
que la persona cerrara sesión. Se cachean en `flask.g`, que dura exactamente una
petición.

### 3.2 Línea de seguridad

| Medida | Implementación |
|---|---|
| Contraseñas | `werkzeug.security` (`scrypt`/`pbkdf2` con sal). Nunca en claro, nunca en logs |
| Inyección SQL | 100 % de las consultas con parámetros `?`. Cero concatenación de cadenas |
| Escalada vertical | El registro público otorga `["usuario"]` como **constante del servidor**; el campo del formulario se ignora |
| Escalada horizontal | La regla de las dos llaves + 404 en vez de 403 |
| Sesiones | Cookie firmada, `HttpOnly`, `SameSite=Lax`, secreto en variable de entorno |
| Tokens de invitación | `secrets.token_urlsafe(32)` — impracticable de adivinar y no enumerable |
| Fuga por métricas | El panel de administración muestra solo agregados, nunca contenido de nadie |
| Base de datos | Fuera de `/static`, fuera del repositorio |

### 3.3 Manejo defensivo de fechas

Heredado de la v1 y ampliado: `zoneinfo.ZoneInfo("America/Lima")` con respaldo a
`timezone(timedelta(hours=-5))`. El servidor corre en UTC; sin esto, después de
las 7 p.m. hora de Lima una tarea de hoy se marcaría como vencida y el ranking
mentiría todas las noches.

### 3.4 Límites conocidos y asumidos

1. **Concurrencia de SQLite.** El fichero se bloquea al escribir. WAL y un
   `timeout` de 10 s lo mitigan; para decenas de usuarios simultáneos habría que
   migrar a PostgreSQL. Aceptable y documentado para la escala del proyecto.
2. **Sin recuperación de contraseña.** Está fuera de alcance por diseño (no hay
   SMTP): la restablece un administrador.
3. **Sin auditoría de acciones.** Se sabe quién otorgó un rol (`granted_by`), pero
   no hay bitácora completa. Va al backlog v3.
4. **Invitaciones sin caducidad.** Un token es válido hasta que se revoca. v3.

---

## 🧪 4. Ejecución del plan de pruebas (`testingNotes`)

### 4.1 Verificación automática

```bash
python test_v2.py
```

Ejecuta los casos Given-When-Then sobre una base temporal, con el cliente de
pruebas de Flask. Cobertura por bloque:

| Bloque | Asserts automáticos | Qué verifican |
|---|---|---|
| Núcleo | TC 5.1 – 5.5, 6.1 – 6.4, 7.3 | Hash de contraseña, rol forzado en el registro, unión de permisos, 403 sin permiso, 404 sin propiedad |
| Planner | TC 1.3, 2.1, 2.2, 3.2, 4.2, 9.1, 9.3, 10.2 | Aislamiento entre cuentas, determinismo del ranking, columnas válidas |
| Calendario | TC 11.1, 11.3, 11.4, 12.2, 12.4 | Rango horario, privacidad, idempotencia de la invitación |
| Hábitos y métricas | TC 13.2 – 13.4, 14.1, 14.2, 15.1 | Registro idempotente, racha, división entre cero |

*(Completar con el resultado real: `__/__ verificaciones en verde`.)*

### 4.2 Plan manual

Los **45 casos** de Construction III, ejecutados **dos veces**: en local y contra
el despliegue. Un caso que pasa en local y falla en producción cuenta como
fallado.

*(Completar: `__/45 pasan · __ defectos abiertos`.)*

### 4.3 Los tres casos que bloquean el release

| Caso | Qué prueba | Estado |
|---|---|---|
| **TC-03** | Un `role=admin` enviado en el formulario de registro no otorga nada | ⬜ |
| **TC-08** | Tener `planner.editar` no permite editar la tarea de otro (404) | ⬜ |
| **TC-11** | Una cuenta ve exactamente sus datos y ninguno ajeno | ⬜ |

Si alguno falla, **no se despliega**. Son agujeros de seguridad, no defectos
cosméticos, y ninguno se arregla con un parche en la vista.

### 4.4 Defecto más importante encontrado y reparado

*(Completar durante la ejecución, con este formato — la rúbrica lo pide
explícitamente.)*

- **Síntoma:**
- **Caso que lo detectó:**
- **Causa raíz:**
- **Corrección aplicada:**
- **Reejecución del bloque completo:** ⬜

---

## 🚀 5. URL del despliegue (`deploymentUrl`)

```text
http://<usuario>.pythonanywhere.com
```

**Cuentas de demostración para la presentación**

| Cuenta | Roles | Qué demuestra en la demo |
|---|---|---|
| `admin` | `usuario` + `admin` | Los roles agregativos: planifica su día **y** administra el sistema en la misma sesión |
| `piero` | `usuario` | La experiencia normal: planner, Kanban, calendario, hábitos |
| `lucero` | `usuario` + `lider` | Asignación de tareas y vista de equipo |
| `ana` | `usuario` | Recibe la invitación y demuestra el aislamiento de datos |

> Antes de la presentación: sembrar datos de demostración con actividades a
> distintas horas, tareas en las cuatro columnas del Kanban, un mes con eventos de
> colores y varios días de rachas de hábitos. Un tablero vacío no se ve como un
> producto, se ve como un formulario.

---

## 💭 6. Notas de reflexión (`reflection`)

### Lo que confirmamos de la v1

**Congelar los números antes de programar sigue siendo lo que más ahorra.** En la
v1 fue la fórmula del puntaje; en la v2 fue el catálogo de permisos y el mapeo de
estados. Cuando el criterio está escrito con valores exactos, el asistente de IA
genera código correcto a la primera; cuando está escrito con adjetivos —
"priorizar inteligentemente", "gestionar usuarios"— genera algo plausible que hay
que rehacer.

**La propiedad exclusiva de archivos volvió a eliminar los conflictos de merge.**
Cuatro personas, una semana, cero conflictos serios, porque cada archivo tiene un
dueño y los contratos entre módulos se publicaron **por escrito** antes de que
nadie escribiera código.

### Lo que aprendimos nuevo en la v2

**La autorización es una decisión de arquitectura, no una capa que se añade
después.** Intentar meter permisos en una aplicación ya escrita habría significado
revisar cada consulta. Definirlos en Elaboration significó que cada repositorio
nació con `user_id` en el `WHERE`.

**"Simple" y "fácil" no son lo mismo.** La columna `role` de texto era más fácil
de escribir y habría hecho imposible el requisito central. Las cuatro tablas del
modelo de permisos parecen más complicadas y son las que hacen que todo lo demás
sea trivial: añadir un rol nuevo hoy es una entrada en `seed.py`, no un `if` en
veinte controladores.

**La IA es excelente proponiendo y pésima decidiendo.** De trece propuestas
registradas en Elaboration II, cinco se rechazaron, cuatro se cambiaron y cuatro
se aceptaron. Las rechazadas no eran código malo: eran soluciones correctas para
un proyecto distinto del nuestro —con más tiempo, más gente y presupuesto de
infraestructura. El criterio no lo pone el modelo; lo ponemos nosotros, y por eso
el registro de crítica es parte del entregable y no un trámite.

**Lo que la IA sí nos enseñó.** Responder 404 en vez de 403 para no confirmar la
existencia de un registro es una buena práctica real que ninguno del equipo
conocía. Vale la pena leer las sugerencias completas antes de descartarlas.

**El diseño accesible detecta errores de código.** Al verificar el contraste
descubrimos que el rosa de la paleta (`#D7707F`) da 3.20:1 sobre blanco y no llega
al mínimo de 4.5:1 para texto. La corrección —un tono derivado más oscuro para
texto, el original solo para rellenos— es exactamente el tipo de detalle que
distingue una interfaz que se ve bonita en la captura de una que se puede usar.

### Lo que haríamos distinto

1. **Sembrar datos de demostración desde el día uno.** Maquetar contra una base
   vacía es lento y engaña: los problemas de layout aparecen con datos reales.
2. **Escribir `test_v2.py` en paralelo al código, no al final.** Los casos que
   escribimos antes encontraron defectos; los que escribimos después solo
   confirmaron lo que ya funcionaba.
3. **Reservar medio día completo para el despliegue.** En la v1 se subestimó y en
   la v2 aparecen dos pasos nuevos —variables de entorno y semilla— que no existen
   en local y que son justo donde se pierde el tiempo.

---

## 📦 7. Entrega y hand-off

| Artefacto | Ubicación |
|---|---|
| Código fuente | `https://github.com/<org>/vibe-planner` rama `main` |
| Documentación VUP v2 | `docs/VUP_V2/01_Inception.md` … `07_Transition.md` |
| Design system | `docs/VUP_V2/00_Design_System.md` |
| Reparto por módulos | `docs/VUP_V2/modulos/MODULO_A…D.md` |
| Backlog v3 | `docs/VUP_V2/BACKLOG_v3.md` |
| Evidencia de prompts | `docs/prompts/` |
| Documentación v1 *(intacta)* | `docs/vup_deliverables/` |
| Aplicación desplegada | `http://<usuario>.pythonanywhere.com` |

**Para quien retome el proyecto:** empieza por `docs/VUP_V2/00_INDICE.md`, luego
`03_Elaboration_II.md` § 1 (arquitectura) y § 5 (mapa de módulos). Con eso sabes
qué archivo toca cada cosa y qué contratos no se pueden romper. Antes de escribir
una línea, lee las "Reglas que no se rompen" de `04_Construction_I.md` § 8.
