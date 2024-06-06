from insights.dashboards.models import Dashboard


def get_dash_filters(dash: Dashboard):
    if dash.name == "Atendimento humano":
        data = {
            "tags": {
                "type": "select",
                "label": "Tags",
                "source": "chats_tags",
                "depends_on": {"filter": "sectors", "search_param": "sector"},
                "placeholder": "Selecione tags",
            },
            "agents": {
                "type": "select",
                "label": "Agente",
                "source": "chats_agents",
                "depends_on": {"filter": "sectors", "search_param": None},
                "placeholder": "Selecione agente",
            },
            "queues": {
                "type": "select",
                "label": "Fila",
                "source": "chats_queues",
                "depends_on": {"filter": "sectors", "search_param": "sector"},
                "placeholder": "Selecione fila",
            },
            "contact": {
                "type": "input_text",
                "label": "Pesquisa por contato",
                "placeholder": "Nome ou URN do contato",
            },
            "sectors": {
                "type": "select",
                "label": "Setor",
                "source": "chats_sectors",
                "placeholder": "Selecione setor",
            },
            "ended_at": {
                "type": "date_range",
                "label": "Data",
                "end_sufix": "_before",
                "placeholder": None,
                "start_sufix": "_after",
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
