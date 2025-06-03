from django.test import TestCase
from insights.dashboards.models import Dashboard
from insights.dashboards.usecases.dashboard_filters import get_dash_filters


class TestGetDashFilters(TestCase):
    def test_get_dash_filters_atendimento_humano(self):
        dash = Dashboard(name="Atendimento humano")
        expected_filters = {
            "contact": {
                "type": "input_text",
                "label": "filter.contact.label",
                "placeholder": "filter.contact.placeholder",
            },
            "created_on": {
                "type": "date_range",
                "label": "filter.created_on.label",
                "end_sufix": "__lte",
                "placeholder": "filter.created_on.placeholder",
                "start_sufix": "__gte",
            },
            "sector": {
                "type": "select",
                "label": "filter.sector.label",
                "field": "uuid",
                "source": "sectors",
                "placeholder": "filter.sector.placeholder",
            },
            "queue": {
                "type": "select",
                "label": "filter.queue.label",
                "field": "uuid",
                "source": "queues",
                "depends_on": {"filter": "sector", "search_param": "sector_id"},
                "placeholder": "filter.queue.placeholder",
            },
            "agent": {
                "type": "select",
                "label": "filter.agent.label",
                "field": "email",
                "source": "agents",
                "placeholder": "filter.agent.placeholder",
            },
            "tags": {
                "type": "select",
                "label": "filter.tags.label",
                "field": "uuid",
                "source": "tags",
                "depends_on": {"filter": "sector", "search_param": "sector_id"},
                "placeholder": "filter.tags.placeholder",
            },
        }
        result = get_dash_filters(dash)
        self.assertEqual(result, expected_filters)

    def test_get_dash_filters_whatsapp_integration(self):
        dash = Dashboard(
            name="Some other dash", config={"is_whatsapp_integration": True}
        )
        expected_filters = {
            "date": {
                "type": "date_range",
                "label": None,
                "end_sufix": "_end",
                "placeholder": None,
                "start_sufix": "_start",
            },
        }
        result = get_dash_filters(dash)
        self.assertEqual(result, expected_filters)

    def test_get_dash_filters_default(self):
        dash = Dashboard(name="Default dash", config={"is_whatsapp_integration": False})
        expected_filters = {
            "ended_at": {
                "type": "date_range",
                "label": None,
                "end_sufix": "__lte",
                "placeholder": None,
                "start_sufix": "__gte",
            },
        }
        result = get_dash_filters(dash)
        self.assertEqual(result, expected_filters)

    def test_get_dash_filters_default_no_config(self):
        dash = Dashboard(name="Default dash no config", config=None)
        expected_filters = {
            "ended_at": {
                "type": "date_range",
                "label": None,
                "end_sufix": "__lte",
                "placeholder": None,
                "start_sufix": "__gte",
            },
        }
        result = get_dash_filters(dash)
        self.assertEqual(result, expected_filters)
