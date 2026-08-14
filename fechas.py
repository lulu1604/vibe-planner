"""
VibePlanner v2 - Fecha y hora locales (fechas.py)
------------------------------------------------------------------------
ARCHIVO COMPARTIDO. Cualquier cambio se avisa al grupo.

Por que existe
--------------
El servidor de PythonAnywhere corre en UTC y Lima es UTC-5. A partir de las
19:00 hora de Lima, para el servidor ya es "manana". Cualquier `datetime.now()`
sin zona horaria produce, a partir de esa hora:

  - la celda equivocada resaltada como "hoy" en el calendario,
  - el mes por defecto saltado al siguiente el 31 a las 19:01,
  - una racha de habitos que se rompe sola cada tarde,
  - una tarea que vence hoy marcada como vencida.

Esta funcion ya existia duplicada en `scoring.today_local()` (Modulo B) y en
`metrics.hoy_iso()` (Modulo D). Tres definiciones de la misma regla es como se
desincronizan: esta es la unica, y las otras dos deberian apuntar aqui en cuanto
sus duenos puedan tocarlas.
"""

from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Lima")
except Exception:
    # Algunos Windows no traen la base de datos de zonas horarias.
    # Lima no aplica horario de verano, asi que el offset fijo es exacto.
    TZ = timezone(timedelta(hours=-5))


def ahora_local():
    """El instante actual en America/Lima."""
    return datetime.now(TZ)


def hoy_local():
    """La fecha de hoy en America/Lima, como `date`."""
    return ahora_local().date()


def hoy_iso():
    """La fecha de hoy en America/Lima, en ISO 'YYYY-MM-DD'."""
    return hoy_local().isoformat()


def anio_mes_local():
    """(anio, mes) actuales en America/Lima."""
    hoy = hoy_local()
    return hoy.year, hoy.month
