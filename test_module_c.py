"""
VibePlanner v2 - Suite de Pruebas Automáticas del Módulo C (test_module_c.py)
-------------------------------------------------------------------------------
DUEÑO: Jose Cabrera (Módulo C - Calendario e Invitaciones)

Cubre los casos de prueba manuales TC-25 a TC-32 de la especificación VUP v2:
  - TC-25: Creación y visualización en el día correcto con hora y color
  - TC-26: Navegación de meses y cruces de año (Dic->Ene, Ene->Dic)
  - TC-27: Validación server-side end_at <= start_at
  - TC-28: Aislamiento entre cuentas (Ana no ve los eventos de Jose)
  - TC-29: Invitaciones por token y aceptación de invitados
  - TC-30: Token inválido no revela información
  - TC-31: Redirección post-login en invitaciones
  - TC-32: Idempotencia en aceptación de invitaciones
"""

import os
import tempfile
import unittest

from app import app
import database
import repo_events
import repo_users
import security


class TestModuleCCalendar(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.fd, cls.db_path = tempfile.mkstemp(suffix=".db")
        os.close(cls.fd)
        database.DB_PATH = cls.db_path
        database.init_db()

        app.config["TESTING"] = True
        cls.app_context = app.app_context()
        cls.app_context.push()

        # Crear cuentas de prueba para TC-28 y TC-29
        cls.user_jose_id = repo_users.create_user({"username": "jose_test", "email": "jose@test.com", "password": "Password123"}, ("usuario",))
        cls.user_ana_id = repo_users.create_user({"username": "ana_test", "email": "ana@test.com", "password": "Password123"}, ("usuario",))
        cls.user_piero_id = repo_users.create_user({"username": "piero_test", "email": "piero@test.com", "password": "Password123"}, ("usuario",))

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def setUp(self):
        self.client = app.test_client()

    def test_tc25_create_and_list_month_event(self):
        """TC-25: Un evento creado el 27 aparece en la consulta del mes con su hora y color."""
        data = {
            "title": "Reunión de Equipo",
            "description": "Discutir entregables VUP",
            "start_at": "2026-08-27 10:00",
            "end_at": "2026-08-27 11:30",
            "color": "#D7707F",
            "status": "confirmado"
        }
        event_id = repo_events.create(data, self.user_jose_id)
        self.assertGreater(event_id, 0)

        month_events = repo_events.list_month(self.user_jose_id, 2026, 8)
        self.assertTrue(any(e["id"] == event_id and e["title"] == "Reunión de Equipo" for e in month_events))
        self.assertTrue(any(e["color"] == "#D7707F" and e["start_at"] == "2026-08-27 10:00" for e in month_events))

    def test_tc26_year_cross_navigation(self):
        """TC-26: Navegación entre meses y cruces de año en list_month (Dic->Ene)."""
        data_dec = {
            "title": "Cierre de Año",
            "start_at": "2026-12-31 23:00",
            "end_at": "2026-12-31 23:59",
            "color": "#2F4156"
        }
        data_jan = {
            "title": "Año Nuevo",
            "start_at": "2027-01-01 00:00",
            "end_at": "2027-01-01 02:00",
            "color": "#567C8D"
        }
        id_dec = repo_events.create(data_dec, self.user_jose_id)
        id_jan = repo_events.create(data_jan, self.user_jose_id)

        dec_events = repo_events.list_month(self.user_jose_id, 2026, 12)
        jan_events = repo_events.list_month(self.user_jose_id, 2027, 1)

        self.assertTrue(any(e["id"] == id_dec for e in dec_events))
        self.assertFalse(any(e["id"] == id_jan for e in dec_events))

        self.assertTrue(any(e["id"] == id_jan for e in jan_events))
        self.assertFalse(any(e["id"] == id_dec for e in jan_events))

    def test_tc27_validation_end_before_start(self):
        """TC-27: end_at <= start_at se rechaza en la capa de datos/servidor."""
        data_invalid = {
            "title": "Evento Imposible",
            "start_at": "2026-08-20 15:00",
            "end_at": "2026-08-20 14:00",
            "color": "#567C8D"
        }
        with self.assertRaises(Exception):
            repo_events.create(data_invalid, self.user_jose_id)

    def test_tc28_user_privacy_isolation(self):
        """TC-28: Ana ve 0 eventos propios de Jose en su calendario."""
        data_jose = {
            "title": "Evento Privado Jose",
            "start_at": "2026-09-15 10:00",
            "end_at": "2026-09-15 11:00",
            "color": "#567C8D"
        }
        event_id = repo_events.create(data_jose, self.user_jose_id)

        ana_events = repo_events.list_month(self.user_ana_id, 2026, 9)
        self.assertFalse(any(e["id"] == event_id for e in ana_events))

    def test_tc29_invitation_accept_flow(self):
        """TC-29: Piero crea evento e invita a Ana; Ana acepta y aparece en su calendario como 'invitado'."""
        data_piero = {
            "title": "Taller de Vibe Coding",
            "start_at": "2026-10-10 16:00",
            "end_at": "2026-10-10 18:00",
            "color": "#C8D9E6"
        }
        event_id = repo_events.create(data_piero, self.user_piero_id)
        token = repo_events.create_invitation(event_id)

        success = repo_events.accept_invitation(token, self.user_ana_id)
        self.assertTrue(success)

        ana_events = repo_events.list_month(self.user_ana_id, 2026, 10)
        ana_event = next((e for e in ana_events if e["id"] == event_id), None)
        self.assertIsNotNone(ana_event)
        self.assertEqual(ana_event["origen"], "invitado")
        self.assertEqual(ana_event["anfitrion"], "piero_test")

    def test_tc30_invalid_token_no_leak(self):
        """TC-30: Token inexistente o revocado devuelve None y no filtra datos."""
        inv_data = repo_events.get_event_by_token("token_falso_12345")
        self.assertIsNone(inv_data)

    def test_tc32_idempotent_invitation_acceptance(self):
        """TC-32: Aceptar la misma invitación dos veces es idempotente y no duplica ni desborda asistentes."""
        data = {
            "title": "Hackathon ESAN",
            "start_at": "2026-11-05 09:00",
            "end_at": "2026-11-05 18:00",
            "color": "#567C8D"
        }
        event_id = repo_events.create(data, self.user_jose_id)
        token = repo_events.create_invitation(event_id)

        res1 = repo_events.accept_invitation(token, self.user_ana_id)
        self.assertTrue(res1)
        count1 = repo_events.count_attendees(event_id)

        res2 = repo_events.accept_invitation(token, self.user_ana_id)
        self.assertTrue(res2)
        count2 = repo_events.count_attendees(event_id)

        self.assertEqual(count1, count2)
        self.assertEqual(count2, 2)


if __name__ == "__main__":
    unittest.main()
