import copy

from django.db import transaction

from insights.dashboards.models import HUMAN_SERVICE_DASHBOARD_NAME, Dashboard
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
                    name=HUMAN_SERVICE_DASHBOARD_NAME,
                    description="Dashboard de atendimento humano",
                    is_default=True,
                    grid=[18, 3],
                    is_deletable=False,
                    is_editable=False,
                )
                self.create_widgets(atendimento_humano)

        except Exception as exception:
            raise InvalidDashboardObject(f"Error creating dashboard: {exception}")

    def create_widgets(self, dashboard_atendimento_humano):
        try:
            with transaction.atomic():
                pico_de_atendimento = Widget.objects.create(
                    name="human_service_dashboard.peaks_in_human_service",
                    type="graph_column",
                    source="rooms",
                    config={
                        "limit": 12,
                        "operation": "timeseries_hour_group_count",
                        "live_filter": {
                            "created_on__gte": "today",
                        },
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [1, 1], "columns": [1, 12]},
                )
                em_andamento = Widget.objects.create(
                    name="in_progress",
                    type="card",
                    source="rooms",
                    config={
                        "operation": "count",
                        "type_result": "executions",
                        "filter": {"is_active": True, "user_id__isnull": False},
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [2, 2], "columns": [1, 4]},
                )
                Widget.objects.create(
                    name="human_service_dashboard.waiting_time",
                    type="card",
                    source="rooms",
                    config={
                        "operation": "avg",
                        "type_result": "executions",
                        "op_field": "waiting_time",
                        "filter": {},
                        "live_filter": {
                            "created_on__gte": "today",
                            "user_id__isnull": False,
                            "is_active": False,
                        },
                        "data_type": "sec",
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [3, 3], "columns": [5, 8]},
                )
                encerrados = Widget.objects.create(
                    name="closeds",
                    type="card",
                    source="rooms",
                    config={
                        "operation": "count",
                        "type_result": "executions",
                        "filter": {"is_active": False},
                        "live_filter": {"ended_at__gte": "today"},
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [2, 2], "columns": [9, 12]},
                )
                Widget.objects.create(
                    name="human_service_dashboard.response_time",
                    type="card",
                    source="rooms",
                    config={
                        "operation": "avg",
                        "type_result": "executions",
                        "op_field": "message_response_time",
                        "filter": {},
                        "live_filter": {
                            "created_on__gte": "today",
                            "user_id__isnull": False,
                            "is_active": False,
                        },
                        "data_type": "sec",
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [3, 3], "columns": [1, 4]},
                )
                aguardando_atendimento = Widget.objects.create(
                    name="human_service_dashboard.awaiting_service",
                    type="card",
                    source="rooms",
                    config={
                        "operation": "count",
                        "type_result": "executions",
                        "filter": {
                            "is_active": True,
                            "user_id__isnull": True,
                        },
                    },
                    dashboard=dashboard_atendimento_humano,
                    position={"rows": [2, 2], "columns": [5, 8]},
                )
                Widget.objects.create(
                    name="human_service_dashboard.interaction_time",
                    type="card",
                    source="rooms",
                    config={
                        "operation": "avg",
                        "type_result": "executions",
                        "op_field": "interaction_time",
                        "filter": {},
                        "live_filter": {
                            "created_on__gte": "today",
                            "user_id__isnull": False,
                            "is_active": False,
                        },
                        "data_type": "sec",
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
                                    "name": "agent",
                                    "value": "agent",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "in_progress",
                                    "value": "opened",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "closeds",
                                    "value": "closed",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "table_dynamic_by_filter.status",
                                    "value": "status",
                                    "display": True,
                                    "hidden_name": True,
                                },
                            ],
                            "name_overwrite": "online_agents",
                        },
                        "created_on": {
                            "icon": "forum:weni-600",
                            "fields": [
                                {
                                    "name": "agent",
                                    "value": "agent",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "table_dynamic_by_filter.chats_in_period",
                                    "value": "opened",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "closeds",
                                    "value": "closed",
                                    "display": True,
                                    "hidden_name": False,
                                },
                                {
                                    "name": "table_dynamic_by_filter.status",
                                    "value": "status",
                                    "display": True,
                                    "hidden_name": True,
                                },
                            ],
                            "name_overwrite": "chats_per_agents",
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
            "name": "waiting",
            "fields": [
                {
                    "name": "table_group.contact",
                    "value": "contact",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.urn",
                    "value": "urn",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.created_on",
                    "value": "created_on",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.sector",
                    "value": "sector",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.queue",
                    "value": "queue",
                    "display": True,
                    "hidden_name": False,
                },
            ],
            "filter": {
                "is_active": True,
                "attending": False,
                "user_id__isnull": True,
            },
            "is_default": False,
        }
        in_progress = {
            "name": "in_progress",
            "fields": [
                {
                    "name": "table_group.contact",
                    "value": "contact",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.urn",
                    "value": "urn",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.agent",
                    "value": "agent",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.created_on",
                    "value": "created_on",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.sector",
                    "value": "sector",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.queue",
                    "value": "queue",
                    "display": True,
                    "hidden_name": False,
                },
            ],
            "filter": {"is_active": True, "attending": True, "user_id__isnull": False},
            "is_default": False,
        }
        closed = {
            "name": "closeds",
            "fields": [
                {
                    "name": "table_group.contact",
                    "value": "contact",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.urn",
                    "value": "urn",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.agent",
                    "value": "agent",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.created_on",
                    "value": "created_on",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.ended_at",
                    "value": "ended_at",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.sector",
                    "value": "sector",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.queue",
                    "value": "queue",
                    "display": True,
                    "hidden_name": False,
                },
                {
                    "name": "table_group.tags",
                    "value": "tags",
                    "display": True,
                    "hidden_name": False,
                },
            ],
            "filter": {"is_active": False},
            "live_filter": {"ended_at__gte": "today"},
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
                    name="human_service_dashboard.peaks_in_human_service",
                    type="graph_column",
                    source="rooms",
                    config={
                        "operation": "timeseries_hour_group_count",
                        "live_filter": {
                            "created_on__gte": "today",
                        },
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
