import copy

from django.db import transaction

from insights.dashboards.models import Dashboard
from insights.dashboards.usecases.exceptions import (
    InvalidDashboardObject,
    InvalidReportsObject,
    InvalidWidgetsObject,
)
from insights.widgets.models import Report, Widget


class CreateHumanService:
    def create_dashboard(self, project):
        try:
            with transaction.atomic():
                atendimento_humano = Dashboard.objects.create(
                    project=project,
                    name="Atendimento humano",
                    description="Dashboard de atendimento humano",
                    is_default=True,
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
                    source="rooms",
                    config={
                        "limit": 12,
                        "operation": "timeseries_hour_group_count",
                        "filter": {"created_on__gte": "now"},
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [1, 1], "columns": [1, 12]},
                )
                em_andamento = Widget.objects.create(
                    name="Em andamento",
                    type="card",
                    source="rooms",
                    config={
                        "operation": "count",
                        "type_result": "executions",
                        "filter": {"is_active": True, "user_id__isnull": True},
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [2, 2], "columns": [1, 4]},
                )
                Widget.objects.create(
                    name="Tempo de espera",
                    type="card",
                    source="rooms",
                    config={
                        "operation": "avg",
                        "type_result": "executions",
                        "op_field": "waiting_time",
                        "filter": {"created_on__gte": "now"},
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [3, 3], "columns": [5, 8]},
                )
                encerrados = Widget.objects.create(
                    name="Encerrados",
                    type="card",
                    source="rooms",
                    config={
                        "operation": "count",
                        "type_result": "executions",
                        "filter": {"is_active": False, "created_on__gte": "now"},
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [2, 2], "columns": [9, 12]},
                )
                Widget.objects.create(
                    name="Tempo de resposta",
                    type="card",
                    source="rooms",
                    config={
                        "operation": "avg",
                        "type_result": "executions",
                        "op_field": "message_response_time",
                        "filter": {"created_on__gte": "now"},
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [3, 3], "columns": [1, 4]},
                )
                aguardando_atendimento = Widget.objects.create(
                    name="Aguardando atendimento",
                    type="card",
                    source="rooms",
                    config={
                        "operation": "count",
                        "type_result": "executions",
                        "filter": {
                            "is_active": True,
                            "user_id__isnull": False,
                        },
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [2, 2], "columns": [5, 8]},
                )
                Widget.objects.create(
                    name="Tempo de interação",
                    type="card",
                    source="rooms",
                    config={
                        "operation": "avg",
                        "type_result": "executions",
                        "op_field": "interaction_time",
                        "filter": {"created_on__gte": "now"},
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [3, 3], "columns": [9, 12]},
                )
                Widget.objects.create(
                    name="Chats por agente",
                    type="table_dynamic_by_filter",
                    source="agents",
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
                                    "value": "opened",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Encerrados",
                                    "value": "closed",
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
                        },
                        "created_on": {
                            "icon": "forum:weni-600",
                            "fields": [
                                {
                                    "name": "Agente",
                                    "value": "agent",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Chats no período",
                                    "value": "opened",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "Encerrados",
                                    "value": "closed",
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
                            "name_overwrite": "Chats por agente",
                        },
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [1, 3], "columns": [13, 18]},
                )

                self.create_reports(
                    pico_de_atendimento,
                    aguardando_atendimento,
                    em_andamento,
                    encerrados,
                )
        except Exception as exception:
            raise InvalidWidgetsObject(f"Error creating widgets: {exception}")

    def create_reports(
        self,
        pico_de_atendimento,
        aguardando_atendimento,
        em_andamento,
        encerrados,
    ):
        waiting = {
            "name": "Aguardando",
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
                    "name": "Início",
                    "value": "created_on",
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
            "filter": {
                "is_active": True,
                "attending": False,
            },
            "is_default": False,
        }
        in_progress = {
            "name": "Em andamento",
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
                    "name": "Agente",
                    "value": "agent",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "Início",
                    "value": "created_on",
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
            "filter": {"is_active": True, "attending": True},
            "is_default": False,
        }
        closed = {
            "name": "Encerrados",
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
                    "name": "Agente",
                    "value": "agent",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "Início",
                    "value": "created_on",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "Fim",
                    "value": "ended_at",
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
                {
                    "name": "Tags",
                    "value": "tags",
                    "display": True,
                    "hidden_name": False,
                },
            ],
            "filter": {"is_active": False},
            "is_default": False,
        }
        table_group_report = {
            "name": "Em andamento",
            "type": "table_group",
            "source": "rooms",
            "config": {
                "waiting": waiting,
                "in_progress": in_progress,
                "closed": closed,
            },
        }
        try:
            with transaction.atomic():
                Report.objects.create(
                    name="Pico de chats abertos por hora",
                    type="graph_column",
                    source="rooms",
                    config={
                        "operation": "timeseries_hour_group_count",
                    },
                    widget=pico_de_atendimento,
                )
                waiting_report = copy.deepcopy(table_group_report)
                waiting_report["widget"] = aguardando_atendimento
                waiting_report["config"]["waiting"]["is_default"] = True
                Report.objects.create(**waiting_report)

                in_progress_report = copy.deepcopy(table_group_report)
                in_progress_report["widget"] = em_andamento
                in_progress_report["config"]["in_progress"]["is_default"] = True
                Report.objects.create(**in_progress_report)

                closed_report = copy.deepcopy(table_group_report)
                closed_report["widget"] = encerrados
                closed_report["config"]["closed"]["is_default"] = True
                Report.objects.create(**closed_report)

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
