# VibePlanner

Planificador diario de actividades con priorizacion transparente y explicable.
Proyecto final - Fundamentals of Vibe Coding, ESAN Global Week 2026.

**Equipo:** Lucero Ayala - Jose Cabrera - Piero Calderon - Ana Cusi

🔗 **App desplegada:** https://ana1604.pythonanywhere.com
📦 **Repositorio:** https://github.com/lulu1604/vibe-planner

---

## Estado del proyecto

| Modulo | Responsable | Estado |
|---|---|---|
| `scoring.py` — motor de puntuacion | Lucero | ✅ 6 asserts |
| `database.py` — persistencia | Jose | ✅ 4 asserts |
| `app.py` — rutas y validacion | Ana | ✅ 11 asserts |
| Despliegue en PythonAnywhere | Ana | ✅ En linea |
| `templates/` + `static/` — frontend | Piero | 🚧 En progreso |

Suites de pruebas (las tres deben pasar antes de desplegar):

```bash
python scoring.py     #  6 asserts
python database.py    #  4 asserts
python app.py test    # 11 asserts
```

---

## Como levantar el proyecto en tu maquina

```bash
git clone <URL-DEL-REPO>
cd vibe-planner

# 1. Crear TU entorno virtual (no se sube al repo)
python -m venv venv

# 2. Activarlo
#    Windows:
venv\Scripts\activate
#    macOS / Linux:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Correr
python app.py
```

Abre http://127.0.0.1:5000 — debes ver la pagina con el formulario vacio.
Si eso funciona, el esqueleto esta bien y ya puedes trabajar en tu modulo.

---

## Reglas que NO se rompen

1. La instancia de Flask se llama **exactamente `app`** a nivel de modulo en
   `app.py`. PythonAnywhere hace `from app import app`. Sin application factory.
2. `vibe_planner.db` **nunca** se sube al repo (ya esta en `.gitignore`).
3. Sin APIs externas, sin CDN, sin gunicorn. Solo Flask y libreria estandar.
4. Toda la logica de puntuacion vive **solo** en `scoring.py`. Ninguna ruta
   recalcula puntajes por su cuenta.
5. La ruta de la base de datos es **absoluta**, calculada desde `__file__`.

---

## Contratos congelados

Estas firmas ya estan definidas. Si necesitas cambiar una, avisa al grupo
**antes** de hacerlo.

```python
# scoring.py
calculate_score(task: dict, available_minutes: int) -> tuple[int, dict]
rank_tasks(tasks: list[dict], available_minutes: int) -> list[dict]

# database.py
get_tasks(filter_status=None) -> list[dict]
get_task_by_id(task_id) -> dict | None
add_task(task_data: dict) -> bool
update_status(task_id, new_status) -> bool
delete_task(task_id) -> bool
get_daily_progress() -> dict  # claves: total, completed, percent
```

Forma exacta del `breakdown` (Ana maqueta contra esto):

```json
{
  "prioridad": {"puntos": 50, "razon": "Prioridad Alta"},
  "urgencia":  {"puntos": 40, "razon": "Vence hoy"},
  "tiempo":    {"puntos": 15, "razon": "Entra en tus 120 min disponibles"}
}
```

---

## Reparto por capa

| Integrante | Modulo | Archivos |
|---|---|---|
| Lucero | Motor de puntuacion | `scoring.py` |
| Jose | Persistencia (dueno unico del esquema SQL) | `database.py` |
| Piero | Rutas Flask + despliegue | `app.py`, `wsgi_pythonanywhere.py` |
| Ana | Vistas, estilos, frontend | `templates/`, `static/` |

## Flujo Git

```bash
git checkout -b feature/tu-modulo
# ... trabajas ...
git add .
git commit -m "descripcion clara"
git push origin feature/tu-modulo
# luego Pull Request en GitHub
```

**Merge a `main` todos los dias**, aunque tu parte este incompleta.
Cuatro ramas que viven una semana = conflictos imposibles el ultimo dia.

## Despliegue

La aplicacion corre en PythonAnywhere: **https://ana1604.pythonanywhere.com**

Guia completa de despliegue y tabla de errores comunes en
[`docs/despliegue.md`](docs/despliegue.md).

Para publicar cambios ya desplegados, en la consola Bash de PythonAnywhere:

```bash
cd ~/vibe-planner && git pull
```

Luego boton **Reload** en la pestana Web. `vibe_planner.db` esta en `.gitignore`,
asi que los datos de produccion sobreviven a cada actualizacion.

---

## Evidencia para Construction

Cada prompt que uses va en `docs/prompts/`. Ver instrucciones ahi.
