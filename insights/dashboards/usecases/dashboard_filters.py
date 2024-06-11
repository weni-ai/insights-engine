from insights.dashboards.models import Dashboard


def get_dash_filters(dash: Dashboard):
    if dash.name == "Atendimento humano":
        data = {
            "contact": {
                "type": "input_text",
                "label": "Pesquisa por contato",
                "placeholder": "Nome ou URN do contato",
            },
            "ended_at": {
                "type": "date_range",
                "label": "Data",
                "end_sufix": "_before",
                "placeholder": None,
                "start_sufix": "_after",
            },
            "sectors": {
                "type": "select",
                "label": "Setor",
                "source": "chats_sectors",
                "placeholder": "Selecione setor",
            },
            "queues": {
                "type": "select",
                "label": "Fila",
                "source": "chats_queues",
                "depends_on": {"filter": "sectors", "search_param": "sector"},
                "placeholder": "Selecione fila",
            },
            "agents": {
                "type": "select",
                "label": "Agente",
                "source": "chats_agents",
                "depends_on": {"filter": "sectors", "search_param": None},
                "placeholder": "Selecione agente",
            },
            "tags": {
                "type": "select",
                "label": "Tags",
                "source": "chats_tags",
                "depends_on": {"filter": "sectors", "search_param": "sector"},
                "placeholder": "Selecione tags",
            },
        }
        return data
    else:
        data = {
            "ended_at": {
                "type": "date_range",
                "end_sufix": "_before",
                "placeholder": None,
                "start_sufix": "_after",
            }
        }
        return data
