from __future__ import annotations

from datetime import datetime
from typing import Dict

import pytz
from django.utils import timezone as dj_timezone

from insights.human_support.clients.chats_raw_data import ChatsRawDataClient
from insights.human_support.clients.chats_time_metrics import (
    ChatsTimeMetricsClient,
)
from insights.human_support.filters import HumanSupportFilterSet
from insights.projects.models import Project
from insights.sources.agents.clients import AgentsRESTClient
from insights.sources.custom_status.client import CustomStatusRESTClient
from insights.sources.queues.usecases.query_execute import (
    QueryExecutor as QueuesQueryExecutor,
)
from insights.sources.rooms.usecases.query_execute import (
    QueryExecutor as RoomsQueryExecutor,
)
from insights.sources.sectors.usecases.query_execute import (
    QueryExecutor as SectorsQueryExecutor,
)
from insights.sources.tags.usecases.query_execute import (
    QueryExecutor as TagsQueryExecutor,
)


class HumanSupportDashboardService:
    def __init__(self, project: Project) -> None:
        self.project = project
        self.client = ChatsRawDataClient(project)

    def _expand_all_tokens(self, incoming_filters: dict | None) -> dict:
        """
        Expande '__all__' em sectors/queues/tags para listas de UUIDs do projeto.
        """
        filters = dict(incoming_filters or {})
        project_uuid = str(self.project.uuid)

        def is_all(value):
            return value == "__all__" or (
                isinstance(value, list) and "__all__" in value
            )

        if is_all(filters.get("sectors")):
            data = SectorsQueryExecutor.execute(
                filters={"project": project_uuid}, operation="list", parser=lambda x: x
            )
            filters["sectors"] = [
                row.get("uuid") for row in (data or {}).get("results", [])
            ]

        if is_all(filters.get("queues")):
            data = QueuesQueryExecutor.execute(
                filters={"project": project_uuid}, operation="list", parser=lambda x: x
            )
            filters["queues"] = [
                row.get("uuid") for row in (data or {}).get("results", [])
            ]

        if is_all(filters.get("tags")):
            data = TagsQueryExecutor.execute(
                filters={"project": project_uuid}, operation="list", parser=lambda x: x
            )
            filters["tags"] = [
                row.get("uuid") for row in (data or {}).get("results", [])
            ]
        return filters

    def _normalize_filters(self, incoming_filters: dict | None) -> dict:
        expanded = self._expand_all_tokens(incoming_filters)
        filterset = HumanSupportFilterSet(
            data=expanded, queryset=Project.objects.none()
        )
        filter_form = filterset.form
        filter_form.is_valid()

        cleaned_filters: dict = {}
        for key, value in filter_form.cleaned_data.items():
            if value in (None, [], ""):
                continue
            cleaned_filters[key] = value

        cleaned_filters.pop("project_uuid", None)
        return cleaned_filters

    def get_attendance_status(self, filters: dict | None = None) -> Dict[str, int]:

        normalized = self._normalize_filters(filters)

        # timezone e recorte "hoje" para finished
        tzname = self.project.timezone or "UTC"
        project_tz = pytz.timezone(tzname)
        
        # Use start_date/end_date if provided, otherwise use today
        if normalized.get("start_date") and normalized.get("end_date"):
            start_of_day = normalized["start_date"].isoformat()
            now_iso = normalized["end_date"].isoformat()
        else:
            today = dj_timezone.now().date()
            start_of_day = project_tz.localize(
                datetime.combine(today, datetime.min.time())
            ).isoformat()
            now_iso = dj_timezone.now().astimezone(project_tz).isoformat()

        base: dict = {
            "project": str(self.project.uuid),
        }
        if normalized.get("sectors"):
            base["sector"] = normalized["sectors"]
        if normalized.get("queues"):
            base["queue"] = normalized["queues"]
        if normalized.get("tags"):
            base["tags"] = normalized["tags"]

        is_waiting = (
            RoomsQueryExecutor.execute(
                {**base, "is_active": True, "user_id__isnull": True},
                "count",
                lambda x: x,
                self.project,
            ).get("value")
            or 0
        )
        in_progress = (
            RoomsQueryExecutor.execute(
                {**base, "is_active": True, "user_id__isnull": False},
                "count",
                lambda x: x,
                self.project,
            ).get("value")
            or 0
        )
        finished = (
            RoomsQueryExecutor.execute(
                {
                    **base,
                    "is_active": False,
                    "ended_at__gte": start_of_day,
                    "ended_at__lte": now_iso,
                },
                "count",
                lambda x: x,
                self.project,
            ).get("value")
            or 0
        )

        return {
            "is_waiting": int(is_waiting),
            "in_progress": int(in_progress),
            "finished": int(finished),
        }

    def get_time_metrics(self, filters: dict | None = None) -> Dict[str, float]:
        normalized = self._normalize_filters(filters)

        params: dict = {}
        if normalized.get("sectors"):
            params["sector"] = normalized["sectors"]
        if normalized.get("queues"):
            params["queue"] = normalized["queues"]
        if normalized.get("tags"):
            params["tags"] = normalized["tags"]
        if normalized.get("start_date"):
            params["start_date"] = normalized["start_date"].date().isoformat()
        if normalized.get("end_date"):
            params["end_date"] = normalized["end_date"].date().isoformat()

        client = ChatsTimeMetricsClient(self.project)
        response = client.retrieve(params=params)

        metrics = response or {}

        waiting_avg = float(metrics.get("avg_waiting_time", 0) or 0)
        waiting_max = float(metrics.get("max_waiting_time", 0) or 0)
        first_resp_avg = float(metrics.get("avg_first_response_time", 0) or 0)
        first_resp_max = float(metrics.get("max_first_response_time", 0) or 0)
        chat_avg = float(metrics.get("avg_conversation_duration", 0) or 0)
        chat_max = float(metrics.get("max_conversation_duration", 0) or 0)

        return {
            "average_time_is_waiting": {"average": waiting_avg, "max": waiting_max},
            "average_time_first_response": {
                "average": first_resp_avg,
                "max": first_resp_max,
            },
            "average_time_chat": {"average": chat_avg, "max": chat_max},
        }

    def get_peaks_in_human_service(self, filters: dict | None = None):
        request_params = self._normalize_filters(filters)

        tzname = self.project.timezone or "UTC"
        project_tz = pytz.timezone(tzname)
        
        # Use start_date if provided, otherwise use start of today
        if request_params.get("start_date"):
            start_of_day = request_params["start_date"].isoformat()
        else:
            start_of_day = project_tz.localize(
                datetime.combine(dj_timezone.now().date(), datetime.min.time())
            ).isoformat()

        rooms_filters = {
            "project": str(self.project.uuid),
            "created_on__gte": start_of_day,
        }
        
        # Add end_date filter if provided
        if request_params.get("end_date"):
            rooms_filters["created_on__lte"] = request_params["end_date"].isoformat()
        
        if "sectors" in request_params:
            rooms_filters["sector"] = request_params["sectors"]
        if "queues" in request_params:
            rooms_filters["queue"] = request_params["queues"]
        if "tags" in request_params:
            rooms_filters["tags"] = request_params["tags"]

        result = RoomsQueryExecutor.execute(
            filters=rooms_filters,
            operation="timeseries_hour_group_count",
            parser=lambda x: x,
            project=self.project,
            query_kwargs={
                "time_field": "created_on",
                "start_hour": 0,
                "end_hour": 23,
                "limit": 24,
                "timezone": tzname,
            },
        )
        return result.get("results", [])

    def get_detailed_monitoring_on_going(self, filters: dict | None = None) -> dict:
        normalized = self._normalize_filters(filters)

        params: dict = {
            "is_active": True,
            "user_id__isnull": False,
            "attending": True,
        }
        filter_to_rooms = {"sectors": "sector", "queues": "queue", "tags": "tags"}
        for filter_key, rooms_field in filter_to_rooms.items():
            value = normalized.get(filter_key)
            if value:
                params[rooms_field] = value

        # Add date filters
        if normalized.get("start_date"):
            params["created_on__gte"] = normalized["start_date"].isoformat()
        if normalized.get("end_date"):
            params["created_on__lte"] = normalized["end_date"].isoformat()

        if filters:
            limit = filters.get("limit")
            if limit is not None:
                params["limit"] = limit
            offset = filters.get("offset")
            if offset is not None:
                params["offset"] = offset
            ordering = filters.get("ordering")
            if ordering is not None:
                prefix = "-" if ordering.startswith("-") else ""
                field = ordering.lstrip("-")
                field_mapping = {
                    "Agent": "uuid",
                    "agent": "uuid",
                    "Duration": "duration",
                    "duration": "duration",
                    "Awaiting time": "waiting_time",
                    "awaiting_time": "waiting_time",
                    "First response time": "first_response_time",
                    "first_response_time": "first_response_time",
                    "Sector": "queue__sector__name",
                    "sector": "queue__sector__name",
                    "Queue": "queue__name",
                    "queue": "queue__name",
                    "Contact": "contact__name",
                    "contact": "contact__name",
                }
                mapped_field = field_mapping.get(field, field)
                params["ordering"] = f"{prefix}{mapped_field}"

        response = RoomsQueryExecutor.execute(params, "list", lambda x: x, self.project)

        formatted_results = []
        for room in response.get("results", []):
            formatted_results.append(
                {
                    "agent": room.get("agent"),
                    "duration": room.get("duration"),
                    "awaiting_time": room.get("waiting_time"),
                    "first_response_time": room.get("first_response_time"),
                    "sector": room.get("sector"),
                    "queue": room.get("queue"),
                    "contact": room.get("contact"),
                    "link": room.get("link"),
                }
            )

        return {
            "next": response.get("next"),
            "previous": response.get("previous"),
            "count": response.get("count"),
            "results": formatted_results,
        }

    def get_detailed_monitoring_awaiting(self, filters: dict | None = None) -> dict:
        """
        Lista de salas em espera.
        Retorna { next, previous, count, results: [...] }.
        Critérios: is_active=True, user_id__isnull=True.
        """
        normalized = self._normalize_filters(filters)

        params: dict = {
            "is_active": True,
            "user_id__isnull": True,
            "attending": False,
        }
        filter_to_rooms_field = {"sectors": "sector", "queues": "queue", "tags": "tags"}
        for filter_key, rooms_field in filter_to_rooms_field.items():
            value = normalized.get(filter_key)
            if value:
                params[rooms_field] = value

        # Add date filters
        if normalized.get("start_date"):
            params["created_on__gte"] = normalized["start_date"].isoformat()
        if normalized.get("end_date"):
            params["created_on__lte"] = normalized["end_date"].isoformat()

        if filters:
            if filters.get("limit") is not None:
                params["limit"] = filters.get("limit")
            if filters.get("offset") is not None:
                params["offset"] = filters.get("offset")
            ordering = filters.get("ordering")
            if ordering is not None:
                prefix = "-" if ordering.startswith("-") else ""
                field = ordering.lstrip("-")
                field_mapping = {
                    "Awaiting time": "queue_time",
                    "awaiting_time": "queue_time",
                    "Sector": "queue__sector__name",
                    "sector": "queue__sector__name",
                    "Queue": "queue__name",
                    "queue": "queue__name",
                    "Contact": "contact__name",
                    "contact": "contact__name",
                }
                mapped_field = field_mapping.get(field, field)
                params["ordering"] = f"{prefix}{mapped_field}"

        response = RoomsQueryExecutor.execute(params, "list", lambda x: x, self.project)

        formatted_results = []
        for room in response.get("results", []):
            formatted_results.append(
                {
                    "awaiting_time": room.get("queue_time"),
                    "contact": room.get("contact"),
                    "sector": room.get("sector"),
                    "queue": room.get("queue"),
                    "link": room.get("link"),
                }
            )
        return {
            "next": response.get("next"),
            "previous": response.get("previous"),
            "count": response.get("count"),
            "results": formatted_results,
        }

    def get_detailed_monitoring_agents(self, filters: dict | None = None):
        normalized = self._normalize_filters(filters)

        params: dict = {}
        sectors = normalized.get("sectors")
        if isinstance(sectors, list) and len(sectors) == 1:
            params["sector"] = [str(sectors[0])]
        elif isinstance(sectors, str):
            params["sector"] = [str(sectors)]

        queues = normalized.get("queues")
        if isinstance(queues, list) and len(queues) == 1:
            params["queue"] = queues[0]
        elif isinstance(queues, str):
            params["queue"] = str(queues)

        tags = normalized.get("tags")
        if tags:
            params["tags"] = tags
            
        agents = normalized.get("agents") or filters.get("agent")
        if agents:
            if isinstance(agents, list) and len(agents) == 1:
                params["agent"] = agents[0]
            elif isinstance(agents, str):
                params["agent"] = agents
            else:
                params["agent"] = agents

        # Add date filters
        if normalized.get("start_date"):
            params["start_date"] = normalized["start_date"].date().isoformat()
        if normalized.get("end_date"):
            params["end_date"] = normalized["end_date"].date().isoformat()

        if filters and filters.get("user_request"):
            params["user_request"] = filters.get("user_request")

        if filters:
            if filters.get("limit") is not None:
                params["limit"] = filters.get("limit")
            if filters.get("offset") is not None:
                params["offset"] = filters.get("offset")
            if filters.get("ordering") is not None:
                ordering = filters.get("ordering")
                prefix = "-" if ordering.startswith("-") else ""
                field = ordering.lstrip("-")

                field_mapping = {
                    # Agent/Attendant
                    "Agent": "first_name",
                    "Attendant": "first_name",
                    "attendant": "first_name",
                    "agent": "first_name",
                    "Name": "first_name",
                    "Email": "email",
                    # Status
                    "Status": "status",
                    "status": "status",
                    # Contadores de atendimentos
                    "Finished": "closed",
                    "finished": "closed",
                    "Closed": "closed",
                    "closed": "closed",
                    "Ongoing": "opened",
                    "ongoing": "opened",
                    "Opened": "opened",
                    "opened": "opened",
                    "In Progress": "opened",
                    # Métricas de tempo - com espaços (como vem do front)
                    "Average first response time": "avg_first_response_time",
                    "average first response time": "avg_first_response_time",
                    "average_first_response_time": "avg_first_response_time",
                    "Average response time": "avg_message_response_time",
                    "average response time": "avg_message_response_time",
                    "average_response_time": "avg_message_response_time",
                    "Average duration": "avg_interaction_time",
                    "average duration": "avg_interaction_time",
                    "average_duration": "avg_interaction_time",
                    "Time in service": "time_in_service",
                    "time in service": "time_in_service",
                    "time_in_service": "time_in_service",
                    "Time In Service": "time_in_service",
                    "in_service_time": "time_in_service",
                }

                mapped_field = field_mapping.get(field, field.lower().replace(" ", "_"))
                params["ordering"] = f"{prefix}{mapped_field}"

        response = AgentsRESTClient(self.project).list(params)
        formatted_results = []
        for agent in response.get("results", []):
            status_data = agent.get("status", {})
            if isinstance(status_data, dict):
                status = status_data.get("status", "offline")
            else:
                status = status_data or "offline"

            formatted_results.append(
                {
                    "agent": agent.get("agent"),
                    "agent_email": agent.get("agent_email"),
                    "status": status,
                    "ongoing": agent.get("opened", 0),
                    "finished": agent.get("closed", 0),
                    "average_first_response_time": agent.get("avg_first_response_time"),
                    "average_response_time": agent.get("avg_message_response_time"),
                    "average_duration": agent.get("avg_interaction_time"),
                    "time_in_service": agent.get("time_in_service"),
                    "link": agent.get("link"),
                }
            )

        return {
            "next": response.get("next"),
            "previous": response.get("previous"),
            "count": response.get("count"),
            "results": formatted_results,
        }

    def get_detailed_monitoring_status(self, filters: dict | None = None) -> dict:
        normalized = self._normalize_filters(filters)

        params: dict = {}
        if filters:
            if filters.get("user_request") is not None:
                params["user_request"] = filters.get("user_request")
            if filters.get("created_on__gte") is not None:
                params["created_on__gte"] = filters.get("created_on__gte")
            if filters.get("created_on__lte") is not None:
                params["created_on__lte"] = filters.get("created_on__lte")
        
        # Add date filters from normalized
        if normalized.get("start_date"):
            params["start_date"] = normalized["start_date"].date().isoformat()
        if normalized.get("end_date"):
            params["end_date"] = normalized["end_date"].date().isoformat()
        
        if filters:
            if filters.get("ordering") is not None:
                ordering = filters.get("ordering")
                prefix = "-" if ordering.startswith("-") else ""
                field = ordering.lstrip("-")

                field_mapping = {
                    # Agent
                    "Agent": "email",
                    "agent": "email",
                    # Status
                    "Status": "status",
                    "status": "status",
                    # Contadores de atendimentos
                    "Finished": "closed",
                    "finished": "closed",
                    "Closed": "closed",
                    "closed": "closed",
                    "Ongoing": "opened",
                    "ongoing": "opened",
                    "Opened": "opened",
                    "opened": "opened",
                    "In Progress": "opened",
                    "Created on": "created_on",
                    "created on": "created_on",
                    "Created On": "created_on",
                    "created_on": "created_on",
                }

                mapped_field = field_mapping.get(field, field.lower().replace(" ", "_"))
                params["ordering"] = f"{prefix}{mapped_field}"

        sectors = normalized.get("sectors") or []
        if isinstance(sectors, list) and sectors:
            params["sector"] = sectors[0]
        queues = normalized.get("queues") or []
        if isinstance(queues, list) and queues:
            params["queue"] = queues[0]

        client = CustomStatusRESTClient(self.project)
        return client.list(params)

    def get_finished_rooms(self, filters: dict | None = None) -> dict:
        """
        Lista de salas finalizadas.
        Retorna { next, previous, count, results: [...] }.
        Critérios: is_active=False.
        """
        normalized = self._normalize_filters(filters)

        params: dict = {
            "is_active": False,
        }

        # Apply sector, queue, tags filters
        filter_to_rooms_field = {"sectors": "sector", "queues": "queue", "tags": "tags"}
        for filter_key, rooms_field in filter_to_rooms_field.items():
            value = normalized.get(filter_key)
            if value:
                params[rooms_field] = value

        # Add date filters for ended_at
        if normalized.get("start_date"):
            params["ended_at__gte"] = normalized["start_date"].isoformat()
        if normalized.get("end_date"):
            params["ended_at__lte"] = normalized["end_date"].isoformat()

        # Add agent filter
        if normalized.get("agent"):
            params["user_id"] = str(normalized["agent"])

        # Add contact filter
        if normalized.get("contact"):
            params["contact"] = str(normalized["contact"])

        # Add ticket_id filter (protocol)
        if normalized.get("ticket_id"):
            params["uuid"] = str(normalized["ticket_id"])

        # Pagination and ordering
        if filters:
            if filters.get("limit") is not None:
                params["limit"] = filters.get("limit")
            if filters.get("offset") is not None:
                params["offset"] = filters.get("offset")
            ordering = filters.get("ordering")
            if ordering is not None:
                prefix = "-" if ordering.startswith("-") else ""
                field = ordering.lstrip("-")
                field_mapping = {
                    "Agent": "agent__first_name",
                    "agent": "agent__first_name",
                    "Atendente": "agent__first_name",
                    "atendente": "agent__first_name",
                    "Sector": "queue__sector__name",
                    "sector": "queue__sector__name",
                    "Setor": "queue__sector__name",
                    "setor": "queue__sector__name",
                    "Queue": "queue__name",
                    "queue": "queue__name",
                    "Fila": "queue__name",
                    "fila": "queue__name",
                    "Contact": "contact__name",
                    "contact": "contact__name",
                    "Contato": "contact__name",
                    "contato": "contact__name",
                    "Ticket ID": "uuid",
                    "ticket_id": "uuid",
                    "Ticket id": "uuid",
                    "Protocol": "uuid",
                    "protocol": "uuid",
                    "Protocolo": "uuid",
                    "protocolo": "uuid",
                    "Tempo aguardando": "waiting_time",
                    "tempo aguardando": "waiting_time",
                    "Awaiting time": "waiting_time",
                    "awaiting_time": "waiting_time",
                    "Tempo para 1ª resposta": "first_response_time",
                    "tempo para 1ª resposta": "first_response_time",
                    "First response time": "first_response_time",
                    "first_response_time": "first_response_time",
                    "Tempo de resposta": "first_response_time",
                    "tempo de resposta": "first_response_time",
                    "Duration": "duration",
                    "duration": "duration",
                    "Duração": "duration",
                    "duração": "duration",
                    "Ended at": "ended_at",
                    "ended_at": "ended_at",
                    "Finalizado em": "ended_at",
                    "finalizado em": "ended_at",
                }
                mapped_field = field_mapping.get(field, field)
                params["ordering"] = f"{prefix}{mapped_field}"

        response = RoomsQueryExecutor.execute(params, "list", lambda x: x, self.project)

        formatted_results = []
        for room in response.get("results", []):
            formatted_results.append(
                {
                    "agent": room.get("agent"),
                    "sector": room.get("sector"),
                    "queue": room.get("queue"),
                    "contact": room.get("contact"),
                    "ticket_id": room.get("uuid"),
                    "awaiting_time": room.get("waiting_time"),
                    "first_response_time": room.get("first_response_time"),
                    "duration": room.get("duration"),
                    "ended_at": room.get("ended_at"),
                    "link": room.get("link"),
                }
            )

        return {
            "next": response.get("next"),
            "previous": response.get("previous"),
            "count": response.get("count"),
            "results": formatted_results,
        }

    def get_analysis_status(self, filters: dict | None = None) -> dict:
        """
        Retorna análise completa: contadores + métricas de tempo (incluindo avg_message_response_time).
        Similar ao monitoring/list_status mas com filtros de data e tempo médio de resposta.
        """
        normalized = self._normalize_filters(filters)

        # Timezone e recorte para finished
        tzname = self.project.timezone or "UTC"
        project_tz = pytz.timezone(tzname)
        
        # Use start_date/end_date if provided, otherwise use today
        if normalized.get("start_date") and normalized.get("end_date"):
            start_of_day = normalized["start_date"].isoformat()
            now_iso = normalized["end_date"].isoformat()
        else:
            today = dj_timezone.now().date()
            start_of_day = project_tz.localize(
                datetime.combine(today, datetime.min.time())
            ).isoformat()
            now_iso = dj_timezone.now().astimezone(project_tz).isoformat()

        base: dict = {
            "project": str(self.project.uuid),
        }
        if normalized.get("sectors"):
            base["sector"] = normalized["sectors"]
        if normalized.get("queues"):
            base["queue"] = normalized["queues"]
        if normalized.get("tags"):
            base["tags"] = normalized["tags"]

        # Count rooms
        is_waiting = (
            RoomsQueryExecutor.execute(
                {**base, "is_active": True, "user_id__isnull": True},
                "count",
                lambda x: x,
                self.project,
            ).get("value")
            or 0
        )
        in_progress = (
            RoomsQueryExecutor.execute(
                {**base, "is_active": True, "user_id__isnull": False},
                "count",
                lambda x: x,
                self.project,
            ).get("value")
            or 0
        )
        finished = (
            RoomsQueryExecutor.execute(
                {
                    **base,
                    "is_active": False,
                    "ended_at__gte": start_of_day,
                    "ended_at__lte": now_iso,
                },
                "count",
                lambda x: x,
                self.project,
            ).get("value")
            or 0
        )

        # Get time metrics
        metrics_params: dict = {}
        if normalized.get("sectors"):
            metrics_params["sector"] = normalized["sectors"]
        if normalized.get("queues"):
            metrics_params["queue"] = normalized["queues"]
        if normalized.get("tags"):
            metrics_params["tags"] = normalized["tags"]
        if normalized.get("start_date"):
            metrics_params["start_date"] = normalized["start_date"].date().isoformat()
        if normalized.get("end_date"):
            metrics_params["end_date"] = normalized["end_date"].date().isoformat()

        client = ChatsTimeMetricsClient(self.project)
        response = client.retrieve(params=metrics_params)
        metrics = response or {}

        waiting_avg = float(metrics.get("avg_waiting_time", 0) or 0)
        first_resp_avg = float(metrics.get("avg_first_response_time", 0) or 0)
        message_resp_avg = float(metrics.get("avg_message_response_time", 0) or 0)
        chat_avg = float(metrics.get("avg_conversation_duration", 0) or 0)

        return {
            "finished": int(finished),
            "average_waiting_time": waiting_avg,
            "average_first_response_time": first_resp_avg,
            "average_response_time": message_resp_avg,
            "average_conversation_duration": chat_avg,
        }