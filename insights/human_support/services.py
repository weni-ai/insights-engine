from __future__ import annotations

from datetime import datetime
from typing import Dict

import pytz
from django.utils import timezone as dj_timezone

from insights.human_support.clients.chats import ChatsClient
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
    def __init__(
        self, project: Project, chats_client: ChatsClient = ChatsClient()
    ) -> None:
        self.project = project
        self.client = ChatsRawDataClient(project)
        self.chats_client = chats_client

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

        filterset.apply_project_timezone(self.project)

        cleaned_filters: dict = {}
        for key, value in filter_form.cleaned_data.items():
            if value in (None, [], ""):
                continue
            cleaned_filters[key] = value

        cleaned_filters.pop("project_uuid", None)
        return cleaned_filters

    def get_attendance_status(self, filters: dict | None = None) -> Dict[str, int]:

        normalized = self._normalize_filters(filters)

        tzname = self.project.timezone or "UTC"
        project_tz = pytz.timezone(tzname)
        today = dj_timezone.now().date()
        start_of_day = project_tz.localize(
            datetime.combine(today, datetime.min.time())
        ).isoformat()
        now_iso = dj_timezone.now().astimezone(project_tz).isoformat()

        base: dict = {
            "project": str(self.project.uuid),
        }
        if normalized.get("sectors"):
            if not isinstance(normalized["sectors"], list):
                normalized["sectors"] = [normalized["sectors"]]
            base["sector__in"] = normalized["sectors"]
        if normalized.get("queues"):
            if not isinstance(normalized["queues"], list):
                normalized["queues"] = [normalized["queues"]]
            base["queue__in"] = normalized["queues"]
        if normalized.get("tags"):
            if not isinstance(normalized["tags"], list):
                normalized["tags"] = [normalized["tags"]]
            base["tags__in"] = normalized["tags"]

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

        time_metrics_filters_mapping = {
            "sectors": ("sector", list),
            "queues": ("queue", list),
            "tags": ("tag", list),
        }

        for filter_key, filter_value in time_metrics_filters_mapping.items():
            if not (value := normalized.get(filter_key)):
                continue

            param, param_type = filter_value

            if param_type == list and not isinstance(value, list):
                value = [value]

            params[param] = value

        if normalized.get("start_date"):
            params["start_date"] = normalized["start_date"].date().isoformat()
        if normalized.get("end_date"):
            params["end_date"] = normalized["end_date"].date().isoformat()

        client = ChatsTimeMetricsClient(self.project)
        response = client.retrieve_time_metrics(params=params)

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
        start_of_day = project_tz.localize(
            datetime.combine(dj_timezone.now().date(), datetime.min.time())
        ).isoformat()

        rooms_filters = {
            "project": str(self.project.uuid),
            "created_on__gte": start_of_day,
        }
        if "sectors" in request_params:
            if not isinstance(request_params["sectors"], list):
                request_params["sectors"] = [request_params["sectors"]]
            rooms_filters["sector__in"] = request_params["sectors"]
        if "queues" in request_params:
            if not isinstance(request_params["queues"], list):
                request_params["queues"] = [request_params["queues"]]
            rooms_filters["queue__in"] = request_params["queues"]
        if "tags" in request_params:
            if not isinstance(request_params["tags"], list):
                request_params["tags"] = [request_params["tags"]]
            rooms_filters["tags__in"] = request_params["tags"]

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

    def get_analysis_peaks_in_human_service(self, filters: dict | None = None):
        request_params = self._normalize_filters(filters)

        tzname = self.project.timezone or "UTC"
        project_tz = pytz.timezone(tzname)

        if request_params.get("start_date") and request_params.get("end_date"):
            start_datetime = request_params["start_date"].isoformat()
            end_datetime = request_params["end_date"].isoformat()
        else:
            today = dj_timezone.now().date()
            start_datetime = project_tz.localize(
                datetime.combine(today, datetime.min.time())
            ).isoformat()
            end_datetime = dj_timezone.now().astimezone(project_tz).isoformat()

        rooms_filters = {
            "project": str(self.project.uuid),
            "created_on__gte": start_datetime,
            "created_on__lte": end_datetime,
        }
        if "sectors" in request_params:
            if not isinstance(request_params["sectors"], list):
                request_params["sectors"] = [request_params["sectors"]]
            rooms_filters["sector__in"] = request_params["sectors"]
        if "queues" in request_params:
            if not isinstance(request_params["queues"], list):
                request_params["queues"] = [request_params["queues"]]
            rooms_filters["queue__in"] = request_params["queues"]
        if "tags" in request_params:
            if not isinstance(request_params["tags"], list):
                request_params["tags"] = [request_params["tags"]]
            rooms_filters["tags__in"] = request_params["tags"]

        result = RoomsQueryExecutor.execute(
            filters=rooms_filters,
            operation="timeseries_hour_group_count",
            parser=lambda x: x,
            project=self.project,
            query_kwargs={
                "time_field": "created_on",
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

        filter_to_rooms = {
            "sectors": "sector",
            "queues": "queue",
            "tags": "tags",
        }

        for filter_name in ("sectors", "queues", "tags"):
            if filters.get(filter_name) and not isinstance(
                filters.get(filter_name), list
            ):
                filters[filter_name] = [filters[filter_name]]

        for filter_key, rooms_field in filter_to_rooms.items():
            value = normalized.get(filter_key)
            if value:
                params[rooms_field] = value

        if normalized.get("agent"):
            params["agent"] = str(normalized["agent"])

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

    def _get_detailed_monitoring_agents_filters(self, filters: dict) -> dict:
        normalized = self._normalize_filters(filters)

        filter_mapping = {
            "sectors": ("sector", normalized),
            "queues": ("queue", normalized),
            "tags": ("tag", normalized),
            "agent": ("agent", normalized),
            "start_date": ("start_date", normalized),
            "end_date": ("end_date", normalized),
            "user_request": ("user_request", filters),
            "limit": ("limit", filters),
            "offset": ("offset", filters),
        }

        list_filters = {"sectors", "queues", "tags"}
        date_filters = {"start_date", "end_date"}

        params: dict = {}

        for filter_key, filter_value in filter_mapping.items():
            param, source = filter_value
            value = source.get(filter_key)

            if not value:
                continue

            if filter_key in date_filters:
                params[param] = value.date().isoformat()
                continue

            if filter_key not in list_filters:
                params[param] = value
                continue

            if isinstance(value, list) and len(value) == 1:
                params[param] = [str(value[0])]
            elif isinstance(filter_value, str):
                params[param] = [str(value)]

        if filters.get("ordering") is not None:
            ordering = filters.get("ordering")
            prefix = "-" if ordering.startswith("-") else ""
            field = ordering.lstrip("-")

            field_mapping = {
                "Agent": "first_name",
                "Attendant": "first_name",
                "attendant": "first_name",
                "agent": "first_name",
                "Name": "first_name",
                "Email": "email",
                "Status": "status",
                "status": "status",
                "Finished": "closed",
                "finished": "closed",
                "Closed": "closed",
                "closed": "closed",
                "Ongoing": "opened",
                "ongoing": "opened",
                "Opened": "opened",
                "opened": "opened",
                "In Progress": "opened",
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

        return params

    def get_detailed_monitoring_agents(self, filters: dict = {}):
        params = self._get_detailed_monitoring_agents_filters(filters)

        response = AgentsRESTClient(self.project).list(params)

        formatted_results = []
        for agent in response.get("results", []):
            status_data = agent.get("status", {})
            status = "offline"
            status_label = None

            if isinstance(status_data, dict):
                status = status_data.get("status", "offline")
                if "label" in status_data:
                    status_label = status_data.get("label")
            else:
                status = status_data or "offline"

            result_data = {
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

            if status_label is not None:
                result_data["status_label"] = status_label

            formatted_results.append(result_data)

        return {
            "next": response.get("next"),
            "previous": response.get("previous"),
            "count": response.get("count"),
            "results": formatted_results,
        }

    def get_detailed_monitoring_status(self, filters: dict = {}) -> dict:
        ordering_fields = {"agent", "-agent"}
        normalized = self._normalize_filters(filters)

        params: dict = {}

        if filters.get("user_request") is not None:
            params["user_request"] = filters.get("user_request")
        if (ordering := filters.get("ordering")) and ordering in ordering_fields:
            params["ordering"] = ordering

        for pagination_filter in ("limit", "offset"):
            if filters.get(pagination_filter):
                params[pagination_filter] = filters.get(pagination_filter)

        mapping = {
            "sectors": ("sector", list),
            "queues": ("queue", list),
            "agent": ("agent", str),
            "start_date": ("start_date", str),
            "end_date": ("end_date", str),
        }

        for filter_key, filter_value in mapping.items():
            param, param_type = filter_value
            if value := normalized.get(filter_key):
                if param_type == list and len(value) > 0:
                    value = value[0]
                elif param in ("start_date", "end_date"):
                    value = value.isoformat()
                params[param] = str(value) if param_type == str else value

        client = CustomStatusRESTClient(self.project)
        return client.list_custom_status_by_agent(params)

    def csat_score_by_agents(
        self, user_request: str | None = None, filters: dict | None = None
    ) -> dict:
        """
        Return the csat score by agents.
        """
        normalized_filters = self._normalize_filters(filters) or {}
        normalized_filters["user_request"] = user_request

        if not normalized_filters.get("start_date") and not normalized_filters.get(
            "end_date"
        ):
            project_timezone = (
                pytz.timezone(self.project.timezone)
                if self.project.timezone
                else pytz.UTC
            )
            today = dj_timezone.now().astimezone(project_timezone).date()
            normalized_filters["start_date"] = project_timezone.localize(
                datetime.combine(today, datetime.min.time())
            )
            normalized_filters["end_date"] = project_timezone.localize(
                datetime.combine(today, datetime.max.time())
            )

        return self.chats_client.csat_score_by_agents(
            project_uuid=str(self.project.uuid), params=normalized_filters
        )

    def _get_analysis_detailed_monitoring_status_filters(
        self, filters: dict, ordering_fields: set
    ) -> dict:
        normalized = self._normalize_filters(filters)

        params: dict = {}

        mapping = {
            "user_request": ("user_request", str),
            "start_date": ("start_date", str),
            "end_date": ("end_date", str),
            "sectors": ("sector", list),
            "queues": ("queue", list),
            "agent": ("agent", str),
        }

        for filter_key, filter_value in mapping.items():
            param, param_type = filter_value
            if value := normalized.get(filter_key):
                if param_type == list and len(value) > 0:
                    value = value[0]

                elif param in ("start_date", "end_date"):
                    value = value.isoformat()

                params[param] = str(value) if param_type == str else value

        if filters.get("limit"):
            params["limit"] = filters.get("limit")
        if filters.get("offset"):
            params["offset"] = filters.get("offset")

    def get_analysis_detailed_monitoring_status(
        self, filters: dict | None = None
    ) -> dict:
        ordering_fields = {"agent", "-agent"}
        params = self._get_analysis_detailed_monitoring_status_filters(
            filters, ordering_fields
        )

        client = CustomStatusRESTClient(self.project)
        response = client.list_custom_status_by_agent(params)

        formatted_results = []
        for agent_data in response.get("results", []):
            formatted_results.append(
                {
                    "agent": agent_data.get("agent"),
                    "agent_email": agent_data.get("agent_email"),
                    "custom_status": agent_data.get("custom_status", []),
                    "link": agent_data.get("link"),
                }
            )

        return {
            "next": response.get("next"),
            "previous": response.get("previous"),
            "count": response.get("count"),
            "results": formatted_results,
        }

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

        filter_to_rooms_field = {"sectors": "sector", "queues": "queue", "tags": "tags"}
        for filter_key, rooms_field in filter_to_rooms_field.items():
            value = normalized.get(filter_key)
            if value:
                params[rooms_field] = value

        if normalized.get("start_date"):
            params["ended_at__gte"] = normalized["start_date"].isoformat()
        if normalized.get("end_date"):
            params["ended_at__lte"] = normalized["end_date"].isoformat()

        if normalized.get("agent"):
            params["agent"] = str(normalized["agent"])

        if normalized.get("contact"):
            params["contact_external_id"] = str(normalized["contact"])

        if normalized.get("ticket_id"):
            params["protocol"] = str(normalized["ticket_id"])

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
                    "agent": "user_full_name",
                    "sector": "queue__sector__name",
                    "queue": "queue__name",
                    "contact": "contact__name",
                    "ticket_id": "protocol",
                    "protocol": "protocol",
                    "awaiting_time": "waiting_time",
                    "first_response_time": "first_response_time",
                    "duration": "duration",
                    "ended_at": "ended_at",
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
                    "ticket_id": room.get("protocol"),
                    "awaiting_time": room.get("waiting_time"),
                    "first_response_time": room.get("first_response_time"),
                    "duration": room.get("duration"),
                    "ended_at": room.get("ended_at"),
                    "csat_rating": room.get("csat_rating"),
                    "link": room.get("link"),
                }
            )

        return {
            "next": response.get("next"),
            "previous": response.get("previous"),
            "count": response.get("count"),
            "results": formatted_results,
        }

    def _get_analysis_status_finished_filters(self, normalized: dict) -> dict:
        base: dict = {
            "project": str(self.project.uuid),
        }

        finished_filters_mapping = {
            "sectors": ("sector__in", list),
            "queues": ("queue__in", list),
            "tags": ("tags__in", list),
            "agent": ("agent", str),
        }

        for filter_key, filter_value in finished_filters_mapping.items():
            if not (value := normalized.get(filter_key)):
                continue

            param, param_type = filter_value

            if param_type == list and not isinstance(value, list):
                value = [value]

            base[param] = value

        return base

    def _get_analysis_status_metrics_filters(self, normalized: dict) -> dict:
        metrics_params: dict = {}

        metrics_filters_mapping = {
            "sectors": ("sector", list),
            "queues": ("queue", list),
            "tags": ("tag", list),
        }

        for filter_key, filter_value in metrics_filters_mapping.items():
            if not (value := normalized.get(filter_key)):
                continue

            param, param_type = filter_value

            if param_type == list and not isinstance(value, list):
                value = [value]

            metrics_params[param] = value

        if normalized.get("start_date"):
            metrics_params["start_date"] = normalized["start_date"].isoformat()
        if normalized.get("end_date"):
            metrics_params["end_date"] = normalized["end_date"].isoformat()

        return metrics_params

    def get_analysis_status(self, filters: dict | None = None) -> dict:
        """
        Returns a complete analysis: counters + time metrics (including avg_message_response_time).
        Similar to monitoring/list_status but with date filters and average response time.
        """
        normalized = self._normalize_filters(filters)

        tzname = self.project.timezone or "UTC"
        project_tz = pytz.timezone(tzname)

        if normalized.get("start_date") and normalized.get("end_date"):
            start_date = normalized["start_date"].isoformat()
            end_date = normalized["end_date"].isoformat()
        else:
            today = dj_timezone.now().date()
            start_date = project_tz.localize(
                datetime.combine(today, datetime.min.time())
            ).isoformat()
            end_date = dj_timezone.now().astimezone(project_tz).isoformat()

        finished_filters = self._get_analysis_status_finished_filters(normalized)

        finished = (
            RoomsQueryExecutor.execute(
                {
                    **finished_filters,
                    "is_active": False,
                    "ended_at__gte": start_date,
                    "ended_at__lte": end_date,
                },
                "count",
                lambda x: x,
                self.project,
            ).get("value")
            or 0
        )

        metrics_params = self._get_analysis_status_metrics_filters(normalized)

        client = ChatsTimeMetricsClient(self.project)
        response = client.retrieve_time_metrics_for_analysis(params=metrics_params)
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

    def get_csat_ratings(self, filters: dict | None = None) -> dict:
        filters_mapping = {
            "sectors": "sectors",
            "queues": "queues",
            "tags": "tags",
            "start_date": "start_date",
            "end_date": "end_date",
            "agent_email": "agent",
        }

        normalized_filters = self._normalize_filters(filters)

        if (
            "start_date" not in normalized_filters
            and "end_date" not in normalized_filters
        ):
            project_timezone = (
                pytz.timezone(self.project.timezone)
                if self.project.timezone
                else pytz.UTC
            )

            today = dj_timezone.now().astimezone(project_timezone).date()
            normalized_filters["start_date"] = project_timezone.localize(
                datetime.combine(today, datetime.min.time())
            )
            normalized_filters["end_date"] = project_timezone.localize(
                datetime.combine(today, datetime.max.time())
            )

        params = {}

        for filter_key, filter_value in filters_mapping.items():
            value = normalized_filters.get(filter_key)
            if value:
                params[filter_value] = value

        ratings_from_chats = self.chats_client.csat_ratings(
            project_uuid=str(self.project.uuid), params=params
        )
        ratings_data = {
            str(rating): {"value": 0, "full_value": 0} for rating in range(1, 6)
        }

        for data in ratings_from_chats.get("csat_ratings", []):
            rating = str(data.get("rating"))

            if rating not in ratings_data:
                continue

            ratings_data[rating]["value"] = data.get("value")
            ratings_data[rating]["full_value"] = data.get("full_value")

        return ratings_data
