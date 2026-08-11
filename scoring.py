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
    """TODO: aplicar la fórmula. Devolver (total:int, breakdown:dict)."""
    breakdown = {
        "prioridad": {"puntos": 0, "razon": "TODO: puntos por prioridad"},
        "urgencia": {"puntos": 0, "razon": "TODO: puntos por urgencia"},
        "tiempo": {"puntos": 0, "razon": "TODO: bono de ajuste de tiempo"},
    }
    return 0, breakdown


def rank_tasks(tasks, available_minutes):
    """TODO: ordenar por puntaje ↓, luego due_date ↑, luego id ↑ (determinista)."""
    scored = []
    for t in tasks:
        total, breakdown = calculate_score(t, available_minutes)
        item = dict(t)
        item["score"] = total
        item["score_breakdown"] = breakdown
        scored.append(item)
    scored.sort(key=lambda x: (-x["score"], x["due_date"], x["id"]))
    return scored
