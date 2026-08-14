# D6 — `/admin/metricas`: las métricas del sistema (US15)

**Objetivo:** el panel del administrador. Cuatro o cinco números agregados y
**ni un dato de nadie**. Es el paso donde se demuestra que el equipo entiende la
diferencia entre administrar un sistema y leer la vida privada de las personas.

**Archivos que salen de aquí:** vista `metricas_sistema` en `habits.py` ·
`templates/habitos/metricas_sistema.html`

**Tiempo estimado:** 1,5–2 horas

**Depende de:** D3 terminado (`system_metrics()`)

---

## 📋 El prompt

> Pega primero `00_CONTEXTO_BASE_ANA.md` completo, y después esto:

---

Construye el panel de métricas del sistema. Lee antes `templates/admin/usuarios.html`
para copiar el estilo del panel de administración que ya existe, y `metrics.py`
para consumir `system_metrics()` sin recalcular nada.

### 1. La ruta

```python
@habitos.route("/admin/metricas")
@security.requires("metrica.sistema.ver")
def metricas_sistema():
    return render_template("habitos/metricas_sistema.html",
                           metricas=metrics.system_metrics())
```

- El permiso es **`metrica.sistema.ver`**, que solo tiene el rol `admin` y ya
  está sembrado en `seed.py`. Sin él → **403** (TC-42).
- Nunca `@admin_required` ni `if 'admin' in roles`: el modelo es de permisos, no
  de nombres de rol. Mañana un rol `soporte` con ese permiso entra sin tocar esta
  línea.
- La ruta vive en el blueprint `habitos` aunque su URL empiece por `/admin`: el
  blueprint `admin` es de Piero y no hace falta tocar su archivo. El blueprint
  `admin` tiene `url_prefix="/admin"`, así que la regla `/admin/metricas` en otro
  blueprint no choca — pero **compruébalo** con `flask routes` y dímelo si hay
  colisión.

### 2. La pantalla

Extiende `base.html` con los bloques congelados y `{% set seccion_activa = "admin" %}`.

- **Cuatro o cinco tarjetas de cifra**, cada una con: el número grande en
  `--font-data`, la etiqueta en lenguaje humano y **una línea de qué significa
  exactamente**:

  | Cifra | Etiqueta | Qué significa |
  |---|---|---|
  | `usuarios_total` | Cuentas registradas | Todas las cuentas, activas o no |
  | `usuarios_activos` | Cuentas activas | Pueden iniciar sesión ahora mismo |
  | `eventos_total` | Eventos creados | En todo el histórico |
  | `habitos_total` | Hábitos activos | Rutinas que la gente sigue |
  | `usaron_hoy` | Usaron la app hoy | Personas distintas con actividad hoy |

  Esa tercera línea no es adorno: un número sin definición se interpreta mal y
  alguien lo va a citar en la presentación final.

- **Un enlace de vuelta** a `/admin/usuarios`, y desde el panel de usuarios uno
  hacia aquí — ese segundo enlace está en el archivo de Piero, así que **pídeselo,
  no lo edites tú**.

- **Estado vacío / sistema recién desplegado**: con 1 usuario y 0 de todo lo
  demás, la pantalla debe verse bien y decir algo sensato, no una fila de ceros
  sin contexto.

### 3. 🔒 La regla que hace este paso distinto de todos los demás

> **Nunca el contenido de nadie.** Ni títulos de tareas, ni nombres de eventos,
> ni el correo de un usuario concreto, ni "los 5 usuarios más activos" — tampoco
> escondido en el HTML "por si acaso" o en un `data-` attribute (TC-41).

Después de generar la plantilla, **revísala tú mismo** y dime explícitamente qué
datos salen a la página. Si alguno es una cadena escrita por una persona, está
mal. Los agregados son números; los números no identifican a nadie.

Comenta en el archivo por qué esta decisión es del producto y no una limitación
técnica: administrar el sistema no es leer la vida privada de las personas.

### 4. Los números se calculan, no se estiman

Nada de "aproximadamente", nada de muestreos, nada de cachés. Cada cifra viene de
un `COUNT(*)` real en `system_metrics()`, para que el TC-40 (contrastar con
`SELECT COUNT(*)` a mano) dé exactamente lo mismo.

---

## 🎯 Heurísticas que este paso debe cumplir

| Heurística | Cómo se comprueba aquí |
|---|---|
| **H1** Visibilidad del estado | El estado del sistema, en una pantalla |
| **H2** Idioma del usuario | "Cuentas activas", no `is_active = 1` |
| **H4** Consistencia | Mismas tarjetas y tokens que `/metricas` |
| **H8** Minimalismo | Cinco cifras que importan, no un panel de veinte |
| **H10** Ayuda | Cada cifra explica qué cuenta exactamente |

---

## 🕳️ Revisa esto antes de aceptar el código

1. **¿Aparece algún nombre, correo, título o dato de una persona concreta?**
   Recházalo. Revisa también el HTML fuente y los atributos `data-`.
2. **¿Añadió un "top 5 de usuarios más activos"?** Es exactamente lo prohibido,
   y es lo que la IA propone con más entusiasmo en este paso.
3. **¿Protegió la ruta con el nombre del rol en vez del permiso?** Debe ser
   `@requires("metrica.sistema.ver")`.
4. **¿La ruta choca con el blueprint `admin` de Piero?** Compruébalo con
   `flask routes`.
5. **¿Estimó algún número o lo cacheó?** Cada cifra es un `COUNT(*)`.
6. **¿Metió un gráfico de librería?** Sin dependencias externas.
7. **¿Se ve bien con el sistema vacío?** Un panel de ceros sin explicación parece
   roto.

---

## ✅ Verificación del paso

```bash
sqlite3 vibe_planner.db "SELECT COUNT(*) FROM users;"
sqlite3 vibe_planner.db "SELECT COUNT(*) FROM users WHERE is_active = 1;"
sqlite3 vibe_planner.db "SELECT COUNT(*) FROM events;"
```

- [ ] Los cuatro números del panel coinciden **exactamente** con esos `COUNT(*)` (TC-40)
- [ ] Reviso el HTML fuente (Ctrl+U) y **no hay** ni un título, ni un nombre, ni
      un correo (TC-41)
- [ ] Como usuario sin el permiso, `/admin/metricas` responde **403** (TC-42)
- [ ] Sin sesión, redirige a login
- [ ] A 360 px las tarjetas se apilan, sin scroll horizontal
- [ ] Todos los números usan `--font-data`

---

## 🤝 Al cerrar este paso

> Piero: `/admin/metricas` ya existe con el permiso `metrica.sistema.ver`.
> ¿Puedes añadir el enlace desde `templates/admin/usuarios.html`? Es tu archivo y
> prefiero no tocarlo.
