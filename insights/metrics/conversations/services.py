from uuid import UUID
from datetime import datetime

from insights.metrics.conversations.exceptions import ConversationsMetricsError
from insights.projects.parsers import parse_dict_to_json
from insights.sources.flowruns.usecases import QueryExecutor as FlowRunsQueryExecutor
from insights.metrics.conversations.enums import CsatMetricsType
from insights.widgets.models import Widget


class ConversationsMetricsService:
    """
    Service to get conversations metrics
    """

    def _get_csat_metrics_from_flowruns(
        self,
        flow_uuid: UUID,
        project_uuid: UUID,
        op_field: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        filters = {
            "ended_at": {
                "gte": start_date,
                "lte": end_date,
            },
            "flow": flow_uuid,
        }

        source_query = FlowRunsQueryExecutor(
            filters,
            operation="recurrence",
            parser=parse_dict_to_json,
            query_kwargs={
                "project": project_uuid,
                "op_field": op_field,
            },
        )

        return source_query.execute()

    def _get_csat_metrics_from_datalake(
        self, agent_uuid: UUID, start_date: datetime, end_date: datetime
    ) -> dict:
        # TODO
        pass

    def get_csat_metrics(
        self,
        project_uuid: UUID,
        widget: Widget,
        start_date: datetime,
        end_date: datetime,
        metric_type: CsatMetricsType,
    ) -> dict:
        """
        Get csat metrics
        """
        # HUMAN
        if metric_type == CsatMetricsType.HUMAN:
            flow_uuid = widget.config.get("filter", {}).get("flow")
            op_field = widget.config.get("op_field")

            if not flow_uuid:
                raise ConversationsMetricsError(
                    "Flow UUID is required in the widget config"
                )

            if not op_field:
                raise ConversationsMetricsError(
                    "Op field is required in the widget config"
                )

            return self._get_csat_metrics_from_flowruns(
                flow_uuid, project_uuid, op_field, start_date, end_date
            )

        # AI
        agent_uuid = (
            widget.config.get("filter", {}).get("datalake_config", {}).get("agent_uuid")
        )

        if not agent_uuid:
            raise ConversationsMetricsError(
                "Agent UUID is required in the widget config"
            )

        return self._get_csat_metrics_from_datalake(agent_uuid, start_date, end_date)
