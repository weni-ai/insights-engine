from insights.dashboards.models import Dashboard


def get_dash_filters(dash: Dashboard):
    if dash.name == "Atendimento humano":
        data = {
            "contact": {
                "type": "input_text",
                "label": "Pesquisa por contato",
                "placeholder": "Nome ou URN do contato",
            },
            "created_on": {
                "type": "date_range",
                "label": "Data",
                "end_sufix": "__lte",
                "placeholder": None,
                "start_sufix": "__gte",
            },
            "sector": {
                "type": "select",
                "label": "Setor",
                "field": "uuid",
                "source": "sectors",
                "placeholder": "Selecione setor",
            },
            "queue": {
                "type": "select",
                "label": "Fila",
                "field": "uuid",
                "source": "queues",
                "depends_on": {"filter": "sector", "search_param": "sector_id"},
                "placeholder": "Selecione fila",
            },
            "agent": {
                "type": "select",
                "label": "Agente",
                "field": "email",
                "source": "agents",
                "depends_on": {"filter": "sector", "search_param": None},
                "placeholder": "Selecione agente",
            },
            "tags": {
                "type": "select",
                "label": "Tags",
                "field": "uuid",
                "source": "tags",
                "depends_on": {"filter": "sector", "search_param": "sector_id"},
                "placeholder": "Selecione tags",
            },
        }
        return data
    else:
        data = {
            "ended_at": {
                "type": "date_range",
                "label": "Data",
                "end_sufix": "__lte",
                "placeholder": None,
                "start_sufix": "__gte",
            },
        }
        return data
