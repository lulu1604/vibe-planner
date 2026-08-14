# 📸 Evidencia del Módulo D — TC-43, TC-44 y TC-45

**Autora:** Ana Cusi · **Historias:** US16 (responsive y accesibilidad)

Los casos TC-33 … TC-42 están automatizados en `test_module_d.py` y no se
comprueban a mano. Los tres de aquí son **visuales**: ninguna prueba automática
sustituye a mirar la pantalla.

```bash
python test_module_d.py    # los 10 automatizados
python app.py              # y abrir http://127.0.0.1:5000
```

> Para redimensionar: DevTools (`F12`) → icono de dispositivo (`Ctrl+Shift+M`) →
> escribir el ancho a mano. Para escala de grises: DevTools → `Ctrl+Shift+P` →
> *"Emulate vision deficiencies"* → **Achromatopsia**.

---

## TC-43 · Móvil a 360 px

**Criterio:** ninguna de las 8 pantallas tiene scroll horizontal, la barra
inferior se ve, el Kanban se apila y todo lo pulsable llega a 44 × 44 px.

| # | Pantalla | Sin scroll horizontal | Barra inferior | Nada tapado | Captura |
|---|---|---|---|---|---|
| 1 | `/planner` (`/`) | ☐ | ☐ | ☐ | ☐ |
| 2 | `/kanban` | ☐ | ☐ | ☐ apilado en 1 columna | ☐ |
| 3 | `/calendario` | ☐ | ☐ | ☐ | ☐ |
| 4 | `/habitos` | ☐ | ☐ | ☐ tarjetas en 1 columna | ☐ |
| 5 | `/metricas` | ☐ | ☐ | ☐ | ☐ |
| 6 | `/admin/usuarios` | ☐ | ☐ | ☐ tabla → tarjetas | ☐ |
| 7 | `/login` | ☐ | n/a | ☐ | ☐ |
| 8 | `/register` | ☐ | n/a | ☐ | ☐ |

**Puntos que fallan primero en este módulo:**

- Las 7 casillas de la semana en `/habitos`: son lo más estrecho de la pantalla.
  Deben conservar `min-height: 44px` y no salirse de la tarjeta.
- El control "Hoy" de cada hábito: campo numérico + botón deben caber en una
  fila o envolverse limpiamente, sin desbordar.
- Las tarjetas de `/metricas`: una sola columna por debajo de 600 px.

---

## TC-44 · Tablet 768 px y escritorio 1280 px

| Ancho | Qué debe verse | ☐ |
|---|---|---|
| 768 px | Sidebar colapsado a iconos, con `title` y `aria-label` en cada uno | ☐ |
| 768 px | Rejilla de hábitos en 2 columnas (`auto-fit` desde 18 rem) | ☐ |
| 768 px | Sin saltos rotos al pasar de 599 a 600 px | ☐ |
| 1280 px | Sidebar fijo y con etiquetas de texto | ☐ |
| 1280 px | Contenido centrado y ≤ 1200 px (`--content-max`) | ☐ |
| 1280 px | Líneas de texto de ~75 caracteres, no de borde a borde | ☐ |

Capturas: ☐ 768 px · ☐ 1280 px

---

## TC-45 · Contraste y escala de grises

### Contraste — ya medido, queda confirmarlo en DevTools

Los ratios están calculados en
[`auditoria_design_system.md`](auditoria_design_system.md) § 3. Aquí solo se
confirma con el inspector.

| Componente | Ratio calculado | Medido en DevTools | ☐ |
|---|---|---|---|
| `.dia-casilla--cumplido` | 6.00:1 | ______ | ☐ |
| `.dia-casilla` (sin marcar) | 5.82:1 | ______ | ☐ |
| `.badge--marcado` | **4.73:1** ← el más ajustado | ______ | ☐ |
| `.badge--sin-marcar` | 5.82:1 | ______ | ☐ |
| `.racha-cifra` | 6.83:1 | ______ | ☐ |
| `.habito-grupo-titulo` | 9.16:1 | ______ | ☐ |
| Anillo de foco en el sidebar | 7.22:1 | ______ | ☐ |

### Escala de grises

| Qué debe seguir distinguiéndose | ☐ |
|---|---|
| Día cumplido vs. sin marcar en la tira de 7 días (relleno **y** borde) | ☐ |
| Insignia "Marcado hoy" vs. "Sin marcar" (llevan texto, no solo color) | ☐ |
| Prioridad Alta / Media / Baja en el planner | ☐ |
| Barra de progreso de `/metricas` (lleva el número escrito al lado) | ☐ |

Captura en escala de grises: ☐

### Foco con teclado

| Recorrido | ☐ |
|---|---|
| `Tab` por `/habitos` completo: el foco es visible en **todos** los pasos | ☐ |
| El foco se ve también sobre el sidebar navy (`--focus-ring-on-dark`) | ☐ |
| El `<summary>` de "Nuevo hábito" se abre con `Enter` | ☐ |
| Ningún `outline: none` sin sustituto visible | ☐ |

---

## Pendientes conocidos al cerrar el módulo

1. **Fuentes `.woff2` ausentes.** `static/fonts/` no existe; la aplicación cae a
   `system-ui` y `Consolas`. Se ve correcta pero no es la tipografía del design
   system. Ver `auditoria_design_system.md` § 5.
2. **TC-37 no se puede automatizar todavía.** `tasks` no tiene `user_id` (Módulo
   B). `test_module_d.py` lo omite con mensaje explícito y `metrics.py` muestra
   *"El módulo de actividades aún no está conectado"* en vez de un 0 % falso.
   En cuanto Lucero migre la tabla, el caso pasa a verde solo.
