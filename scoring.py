"""
VibePlanner - Motor de puntuación transparente (walking skeleton)
-----------------------------------------------------------------
DUEÑA DE ESTE ARCHIVO: Lucero

CONTRATOS CONGELADOS - no cambiar estas firmas sin avisar al grupo:
    calculate_score(task, available_minutes) -> tuple[int, dict]
    rank_tasks(tasks, available_minutes)     -> list[dict]

FORMA EXACTA del breakdown que espera el frontend (Ana maqueta contra esto):
    {
      "prioridad": {"puntos": 50, "razon": "Prioridad Alta"},
      "urgencia":  {"puntos": 40, "razon": "Vence hoy"},
      "tiempo":    {"puntos": 15, "razon": "Entra en tus 120 min disponibles"}
    }

FÓRMULA (especificada en Elaboration, NO improvisar):
    Total = P_Prioridad + P_Urgencia + P_AjusteTiempo
    P_Prioridad : 1 Alta=50 | 2 Media=30 | 3 Baja=10
    P_Urgencia  : vencida u hoy=40 | mañana=20 | en 2-3 días=10 | +3 días=5
    P_Tiempo    : +15 si estimated_minutes <= available_minutes, si no 0
"""

from datetime import datetime
from zoneinfo import ZoneInfo

# 'Hoy' en hora de Lima, NO la del servidor (PythonAnywhere corre en UTC).
TZ = ZoneInfo("America/Lima")

PRIORITY_POINTS = {1: 50, 2: 30, 3: 10}
PRIORITY_LABEL = {1: "Alta", 2: "Media", 3: "Baja"}
TIME_FIT_BONUS = 15


def today_local():
    return datetime.now(TZ).date()


# --------------------------------------------------------------------------
# STUB - Lucero implementa el cuerpo real. Por ahora devuelve un valor fijo
# para que la app arranque y Ana pueda maquetar contra la estructura correcta.
# --------------------------------------------------------------------------
def calculate_score(task, available_minutes):
    """Aplica la fórmula congelada: Total = P_Prioridad + P_Urgencia + P_AjusteTiempo."""
    today = today_local()
    
    # 1. Componente Prioridad
    priority_level = task.get("priority_level", 2)
    p_prio = PRIORITY_POINTS.get(priority_level, 30)
    label_prio = PRIORITY_LABEL.get(priority_level, "Media")
    razon_prio = f"Prioridad {label_prio}"

    # 2. Componente Urgencia
    due_date_str = task.get("due_date", str(today))
    if isinstance(due_date_str, str):
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    else:
        due_date = due_date_str

    delta_days = (due_date - today).days

    if delta_days < 0:
        p_urg = 40
        razon_urg = "Vencida"
    elif delta_days == 0:
        p_urg = 40
        razon_urg = "Vence hoy"
    elif delta_days == 1:
        p_urg = 20
        razon_urg = "Vence mañana"
    elif 2 <= delta_days <= 3:
        p_urg = 10
        razon_urg = "Vence en 2-3 días"
    else:
        p_urg = 5
        razon_urg = "Vence en +3 días"

    # 3. Componente Ajuste de Tiempo
    estimated_minutes = task.get("estimated_minutes", 30)
    if estimated_minutes <= available_minutes:
        p_tiempo = TIME_FIT_BONUS
        razon_tiempo = f"Entra en tus {available_minutes} min disponibles"
    else:
        p_tiempo = 0
        razon_tiempo = f"Supera tus {available_minutes} min disponibles"

    total = p_prio + p_urg + p_tiempo

    breakdown = {
        "prioridad": {"puntos": p_prio, "razon": razon_prio},
        "urgencia": {"puntos": p_urg, "razon": razon_urg},
        "tiempo": {"puntos": p_tiempo, "razon": razon_tiempo},
    }

    return total, breakdown


def rank_tasks(tasks, available_minutes):
    """Ordena tareas por puntaje ↓, luego due_date ↑, luego id ↑ (determinista)."""
    scored = []
    for t in tasks:
        total, breakdown = calculate_score(t, available_minutes)
        item = dict(t)
        item["score"] = total
        item["score_breakdown"] = breakdown
        scored.append(item)
    scored.sort(key=lambda x: (-x["score"], x["due_date"], x.get("id", 0)))
    return scored


# --------------------------------------------------------------------------
# PRUEBAS / ASSERTS DE EVIDENCIA DE TESTING
# --------------------------------------------------------------------------
if __name__ == "__main__":
    from datetime import timedelta

    today = today_local()

    # Tarea 1: Vencida
    task_vencida = {
        "id": 1,
        "title": "Tarea Vencida",
        "priority_level": 1,  # 50 pts
        "due_date": str(today - timedelta(days=2)),  # Vencida (40 pts)
        "estimated_minutes": 30,  # Entra en 120 (15 pts) -> Total: 105
    }
    score_v, breakdown_v = calculate_score(task_vencida, 120)
    # Assert 1: Tarea Vencida
    assert score_v == 105 and breakdown_v["urgencia"]["razon"] == "Vencida", "Assert 1 Falló: Tarea vencida"

    # Tarea 2: Vence Hoy
    task_hoy = {
        "id": 2,
        "title": "Tarea Hoy",
        "priority_level": 2,  # 30 pts
        "due_date": str(today),  # Hoy (40 pts)
        "estimated_minutes": 30,  # Entra en 120 (15 pts) -> Total: 85
    }
    score_h, breakdown_h = calculate_score(task_hoy, 120)
    # Assert 2: Tarea de Hoy
    assert score_h == 85 and breakdown_h["urgencia"]["razon"] == "Vence hoy", "Assert 2 Falló: Tarea de hoy"

    # Tarea 3: Vence a 5 días (+3 días)
    task_futura = {
        "id": 3,
        "title": "Tarea Futura",
        "priority_level": 3,  # 10 pts
        "due_date": str(today + timedelta(days=5)),  # +3 días (5 pts)
        "estimated_minutes": 30,  # Entra en 120 (15 pts) -> Total: 30
    }
    score_f, breakdown_f = calculate_score(task_futura, 120)
    # Assert 3: Tarea Futura
    assert score_f == 30 and breakdown_f["urgencia"]["razon"] == "Vence en +3 días", "Assert 3 Falló: Tarea futura"

    # Tarea 4: Bono de tiempo dentro del disponible
    task_tiempo_ok = {
        "id": 4,
        "title": "Tiempo OK",
        "priority_level": 2,  # 30 pts
        "due_date": str(today),  # 40 pts
        "estimated_minutes": 60,  # <= 120 min (15 pts) -> Total: 85
    }
    score_t_ok, breakdown_t_ok = calculate_score(task_tiempo_ok, 120)
    # Assert 4: Bono de tiempo positivo
    assert breakdown_t_ok["tiempo"]["puntos"] == 15, "Assert 4 Falló: Bono de tiempo OK"

    # Tarea 5: Sin bono de tiempo (supera disponible)
    task_tiempo_excedido = {
        "id": 5,
        "title": "Tiempo Excedido",
        "priority_level": 2,  # 30 pts
        "due_date": str(today),  # 40 pts
        "estimated_minutes": 180,  # > 120 min (0 pts) -> Total: 70
    }
    score_t_exc, breakdown_t_exc = calculate_score(task_tiempo_excedido, 120)
    # Assert 5: Sin bono de tiempo por exceder disponible
    assert score_t_exc == 70 and breakdown_t_exc["tiempo"]["puntos"] == 0, "Assert 5 Falló: Tiempo excedido"

    # Tareas 6 y 7: Empate exacto en puntaje para probar desempate determinista por due_date e id
    task_empate_A = {
        "id": 10,
        "title": "Empate A",
        "priority_level": 2,
        "due_date": str(today + timedelta(days=1)),
        "estimated_minutes": 30,
    }
    task_empate_B = {
        "id": 8,
        "title": "Empate B (Id menor)",
        "priority_level": 2,
        "due_date": str(today + timedelta(days=1)),
        "estimated_minutes": 30,
    }
    ranked = rank_tasks([task_empate_A, task_empate_B], 120)
    # Assert 6: Desempate por id (id 8 debe ir antes que id 10 cuando los puntajes y fechas coinciden)
    assert ranked[0]["id"] == 8 and ranked[1]["id"] == 10, "Assert 6 Falló: Ordenamiento determinista"

    print("SUCCESS: Todas las 6 pruebas de assert pasaron exitosamente!")

