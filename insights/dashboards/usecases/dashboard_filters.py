from insights.dashboards.models import Dashboard


def get_dash_filters(dash: Dashboard):
    if dash.name == "Atendimento humano":
        data = {
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
        return data
    else:
        data = {
            "ended_at": {
                "type": "date_range",
                "label": None,
                "end_sufix": "__lte",
                "placeholder": None,
                "start_sufix": "__gte",
            },
        }
        return data
