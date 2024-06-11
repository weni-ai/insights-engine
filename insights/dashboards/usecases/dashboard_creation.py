from insights.dashboards.models import Dashboard
from insights.widgets.models import Widget, Report
from django.db import transaction
from insights.dashboards.usecases.exceptions import (
    InvalidDashboardObject,
    InvalidWidgetsObject,
    InvalidReportsObject,
)


class CreateHumanService:
    def create_dashboard(self, project):
        try:
            with transaction.atomic():
                atendimento_humano = Dashboard.objects.create(
                    project=project,
                    name="Atendimento humano",
                    description="Dashboard de atendimento humano",
                    is_default=False,
                    grid=[18, 3],
                )
                self.create_widgets(atendimento_humano)

        except Exception as exception:
            raise InvalidDashboardObject(f"Error creating dashboard: {exception}")

    def create_widgets(self, dashboard_atendimento_humano):
        try:
            with transaction.atomic():
                pico_de_atendimento = Widget.objects.create(
                    name="Picos de atendimentos abertos",
                    type="graph_column",
                    source="chats",
                    config={
                        "end_time": "18:00",
                        "interval": "60",
                        "start_time": "07:00",
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [1, 1], "columns": [1, 12]},
                )
                em_andamento = Widget.objects.create(
                    name="Em andamento",
                    type="card",
                    source="chats",
                    config={"operation": "count", "type_result": "executions"},
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [2, 2], "columns": [1, 4]},
                )
                Widget.objects.create(
                    name="Tempo de espera",
                    type="card",
                    source="chats",
                    config={"operation": "AVG", "type_result": "executions"},
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [2, 2], "columns": [5, 8]},
                )
                encerrados = Widget.objects.create(
                    name="Encerrados",
                    type="card",
                    source="chats",
                    config={"operation": "AVG", "type_result": "executions"},
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [2, 2], "columns": [9, 12]},
                )
                Widget.objects.create(
                    name="Tempo de resposta",
                    type="card",
                    source="chats",
                    config={"operation": "count", "type_result": "executions"},
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [3, 3], "columns": [1, 4]},
                )
                aguardando_atendimento = Widget.objects.create(
                    name="Aguardando atendimento",
                    type="card",
                    source="chats",
                    config={"operation": "count", "type_result": "executions"},
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [3, 3], "columns": [5, 8]},
                )
                Widget.objects.create(
                    name="Tempo de interação",
                    type="card",
                    source="chats",
                    config={"operation": "count", "type_result": "executions"},
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [3, 3], "columns": [9, 12]},
                )
                Widget.objects.create(
                    name="Chats por agente",
                    type="table_dynamic_by_filter",
                    source="chats",
                    config={
                        "default": {
                            "icon": "forum:weni-600",
                            "fields": [
                                {
                                    "name": "Agente",
                                    "value": "agent",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Em andamento",
                                    "value": "open",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Encerrados",
                                    "value": "close",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Status",
                                    "value": "status",
                                    "display": True,
                                    "hidden_name": True,
                                },
                            ],
                            "name_overwrite": "Agentes online",
                        }
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [1, 3], "columns": [13, 18]},
                )

                self.create_reports(
                    pico_de_atendimento,
                    em_andamento,
                    encerrados,
                    aguardando_atendimento,
                )
        except Exception as exception:
            raise InvalidWidgetsObject(f"Error creating widgets: {exception}")

    def create_reports(
        self, pico_de_atendimento, em_andamento, encerrados, aguardando_atendimento
    ):
        try:
            with transaction.atomic():
                Report.objects.create(
                    name="Pico de chats abertos por hora",
                    type="graph_column",
                    source="chats",
                    config={},
                    widget=pico_de_atendimento,
                )
                Report.objects.create(
                    name="Em andamento",
                    type="table_group",
                    source="chats",
                    config=[
                        {
                            "name": "Aguardando",
                            "slug": "waiting",
                            "fields": [
                                {
                                    "name": "Contato",
                                    "value": "contact",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "URN",
                                    "value": "urn",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Horário do início",
                                    "value": "start_time",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Setor",
                                    "value": "sector",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Fila",
                                    "value": "queue",
                                    "display": True,
                                    "hidden_name": False,
                                },
                            ],
                            "filter": None,
                            "is_default": False,
                        },
                        {
                            "name": "Em andamento",
                            "slug": "in_progress",
                            "fields": [
                                {
                                    "name": "Contato",
                                    "value": "contact",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "URN",
                                    "value": "urn",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Horário do início",
                                    "value": "start_time",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Setor",
                                    "value": "sector",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Fila",
                                    "value": "queue",
                                    "display": True,
                                    "hidden_name": False,
                                },
                            ],
                            "filter": None,
                            "is_default": True,
                        },
                        {
                            "name": "Encerrados",
                            "slug": "closed",
                            "fields": [
                                {
                                    "name": "Contato",
                                    "value": "contact",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "URN",
                                    "value": "urn",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Horário do início",
                                    "value": "start_time",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Setor",
                                    "value": "sector",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Fila",
                                    "value": "queue",
                                    "display": True,
                                    "hidden_name": False,
                                },
                            ],
                            "filter": None,
                            "is_default": False,
                        },
                    ],
                    widget=em_andamento,
                )
                Report.objects.create(
                    name="Encerrados",
                    type="table_group",
                    source="chats",
                    config=[
                        {
                            "name": "Aguardando",
                            "slug": "waiting",
                            "fields": [
                                {
                                    "name": "Contato",
                                    "value": "contact",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "URN",
                                    "value": "urn",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Horário do início",
                                    "value": "start_time",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Setor",
                                    "value": "sector",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Fila",
                                    "value": "queue",
                                    "display": True,
                                    "hidden_name": False,
                                },
                            ],
                            "filter": None,
                            "is_default": False,
                        },
                        {
                            "name": "Em andamento",
                            "slug": "in_progress",
                            "fields": [
                                {
                                    "name": "Contato",
                                    "value": "contact",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "URN",
                                    "value": "urn",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Horário do início",
                                    "value": "start_time",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Setor",
                                    "value": "sector",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Fila",
                                    "value": "queue",
                                    "display": True,
                                    "hidden_name": False,
                                },
                            ],
                            "filter": None,
                            "is_default": False,
                        },
                        {
                            "name": "Encerrados",
                            "slug": "closed",
                            "fields": [
                                {
                                    "name": "Contato",
                                    "value": "contact",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "URN",
                                    "value": "urn",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Horário do início",
                                    "value": "start_time",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Setor",
                                    "value": "sector",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Fila",
                                    "value": "queue",
                                    "display": True,
                                    "hidden_name": False,
                                },
                            ],
                            "filter": None,
                            "is_default": True,
                        },
                    ],
                    widget=encerrados,
                )
                Report.objects.create(
                    name="Aguardando atendimento",
                    type="table_group",
                    source="chats",
                    config=[
                        {
                            "name": "Aguardando",
                            "slug": "waiting",
                            "fields": [
                                {
                                    "name": "Contato",
                                    "value": "contact",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "URN",
                                    "value": "urn",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Horário do início",
                                    "value": "start_time",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Setor",
                                    "value": "sector",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Fila",
                                    "value": "queue",
                                    "display": True,
                                    "hidden_name": False,
                                },
                            ],
                            "filter": None,
                            "is_default": True,
                        },
                        {
                            "name": "Em andamento",
                            "slug": "in_progress",
                            "fields": [
                                {
                                    "name": "Contato",
                                    "value": "contact",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "URN",
                                    "value": "urn",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Horário do início",
                                    "value": "start_time",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Setor",
                                    "value": "sector",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Fila",
                                    "value": "queue",
                                    "display": True,
                                    "hidden_name": False,
                                },
                            ],
                            "filter": None,
                            "is_default": False,
                        },
                        {
                            "name": "Encerrados",
                            "slug": "closed",
                            "fields": [
                                {
                                    "name": "Contato",
                                    "value": "contact",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "URN",
                                    "value": "urn",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Horário do início",
                                    "value": "start_time",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Setor",
                                    "value": "sector",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Fila",
                                    "value": "queue",
                                    "display": True,
                                    "hidden_name": False,
                                },
                            ],
                            "filter": None,
                            "is_default": False,
                        },
                    ],
                    widget=aguardando_atendimento,
                )
        except Exception as exception:
            raise InvalidReportsObject(f"Error creating dashboard: {exception}")


class CreateFlowResults:
    def create_dashboard(self, project):
        try:
            with transaction.atomic():
                dashboard_resultado_de_fluxo = Dashboard.objects.create(
                    project=project,
                    name="Resultados de fluxos",
                    description="Dashboard de resultado de fluxo",
                    is_default=False,
                    grid=[12, 3],
                )
                self.create_widgets(dashboard_resultado_de_fluxo)

        except Exception as exception:
            raise InvalidDashboardObject(f"Error creating dashboard: {exception}")

    def create_widgets(self, dashboard_resultado_de_fluxo):
        try:
            with transaction.atomic():
                Widget.objects.create(
                    name="Métrica vazia",
                    type="card",
                    source="",
                    config={},
                    dashboard=dashboard_resultado_de_fluxo,
                    position={"rows": [1, 1], "columns": [1, 4]},
                )
                Widget.objects.create(
                    name="Métrica vazia",
                    type="card",
                    source="",
                    config={},
                    dashboard=dashboard_resultado_de_fluxo,
                    position={"rows": [2, 2], "columns": [1, 4]},
                )
                Widget.objects.create(
                    name="Métrica vazia",
                    type="card",
                    source="",
                    config={},
                    dashboard=dashboard_resultado_de_fluxo,
                    position={"rows": [3, 3], "columns": [1, 4]},
                )
                Widget.objects.create(
                    name="Métrica vazia",
                    type="card",
                    source="",
                    config={},
                    dashboard=dashboard_resultado_de_fluxo,
                    position={"rows": [1, 1], "columns": [5, 8]},
                )
                Widget.objects.create(
                    name="Métrica vazia",
                    type="card",
                    source="",
                    config={},
                    dashboard=dashboard_resultado_de_fluxo,
                    position={"rows": [2, 2], "columns": [5, 8]},
                )
                Widget.objects.create(
                    name="Métrica vazia",
                    type="card",
                    source="",
                    config={},
                    dashboard=dashboard_resultado_de_fluxo,
                    position={"rows": [3, 3], "columns": [5, 8]},
                )
                Widget.objects.create(
                    name="Métrica vazia",
                    type="graph_funnel",
                    source="",
                    config={},
                    dashboard=dashboard_resultado_de_fluxo,
                    position={"rows": [1, 3], "columns": [9, 12]},
                )
        except Exception as exception:
            raise InvalidWidgetsObject(f"Error creating widgets: {exception}")

    def create_reports():
        pass
