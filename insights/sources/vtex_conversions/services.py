from datetime import date

from django.conf import settings

from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.projects.models import Project
from insights.sources.integrations.clients import WeniIntegrationsClient
from rest_framework.exceptions import PermissionDenied
from insights.sources.vtex_conversions.dataclass import (
    OrdersConversions,
    OrdersConversionsGraphData,
    OrdersConversionsGraphDataField,
)
from insights.sources.vtex_conversions.serializers import (
    OrdersConversionsFiltersSerializer,
    OrdersConversionsMetricsSerializer,
)


class VTEXOrdersConversionsService:
    """
    Service to get orders conversions from Meta Graph API and VTEX API.
    """

    def __init__(self, project: Project):
        self.project = project
        self.meta_api_client = MetaGraphAPIClient()
        self.integrations_client = WeniIntegrationsClient()

    def project_has_permission_to_access_waba(self, waba_id: str) -> bool:
        """
        Check if the project has permission to access the WABA.
        """

        if test_waba_id := getattr(settings, "WHATSAPP_ABANDONED_CART_WABA_ID", None):
            # TEMPORARY, this should be used only in the development and staging environments
            return waba_id == test_waba_id

        try:
            project_wabas = self.integrations_client.get_wabas_for_project(
                self.project.uuid
            )
        except Exception as e:
            raise e

        return waba_id in project_wabas

    def get_message_metrics(
        self,
        waba_id: str,
        template_id: str,
        start_date: date,
        end_date: date,
    ) -> OrdersConversionsGraphData:
        """
        Get message metrics from Meta Graph API.
        """

        metrics_data = (
            self.meta_api_client.get_messages_analytics(
                waba_id, template_id, start_date, end_date
            )
            .get("data", {})
            .get("status_count")
        )

        return metrics_data

    def get_metrics(self, filters: dict):
        """
        Get metrics from Meta Graph API and VTEX API.
        """

        serializer = OrdersConversionsFiltersSerializer(data=filters)
        serializer.is_valid(raise_exception=True)

        if not self.project_has_permission_to_access_waba(
            serializer.validated_data["waba_id"]
        ):
            raise PermissionDenied

        metrics_data = self.get_message_metrics(
            serializer.validated_data["waba_id"],
            serializer.validated_data["template_id"],
            serializer.validated_data["start_date"],
            serializer.validated_data["end_date"],
        )

        graph_data = OrdersConversionsGraphData()

        for status in ("sent", "delivered", "read", "clicked"):
            status_data = metrics_data.get(status, {})

            field = OrdersConversionsGraphDataField(
                value=status_data.get("value", 0),
                percentage=status_data.get("percentage", 0),
            )

            setattr(graph_data, status, field)

        orders_conversions = OrdersConversions(graph_data=graph_data)
        orders_conversions_serializer = OrdersConversionsMetricsSerializer(
            instance=orders_conversions
        )

        return orders_conversions_serializer.data
