import pytz
from datetime import date, datetime
from logging import getLogger

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied

from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.projects.models import Project
from insights.sources.integrations.clients import WeniIntegrationsClient
from insights.sources.orders.clients import VtexOrdersRestClient
from insights.sources.vtex_conversions.dataclass import (
    OrdersConversions,
    OrdersConversionsGraphData,
    OrdersConversionsGraphDataField,
    OrdersConversionsUTMData,
)
from insights.sources.vtex_conversions.serializers import (
    OrdersConversionsFiltersSerializer,
    OrdersConversionsMetricsSerializer,
)

logger = getLogger(__name__)


class VTEXOrdersConversionsService:
    """
    Service to get orders conversions from Meta Graph API and VTEX API.
    """

    def __init__(
        self,
        project: Project,
        meta_api_client: MetaGraphAPIClient,
        integrations_client: WeniIntegrationsClient,
        orders_client: VtexOrdersRestClient,
    ):
        self.project = project
        self.meta_api_client = meta_api_client
        self.integrations_client = integrations_client
        self.orders_client = orders_client

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

        wabas = [waba.get("waba_id") for waba in project_wabas if waba.get("waba_id")]

        return waba_id in wabas

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

        if not self.project_has_permission_to_access_waba(waba_id):
            logger.error(
                "Verified that project %s does not have permission to access WABA %s while checking permissions in the VTEX orders conversions service",
                self.project.uuid,
                waba_id,
            )
            raise PermissionDenied(
                detail=_("Project does not have permission to access WABA"),
                code="project_without_waba_permission",
            )

        metrics_data = (
            self.meta_api_client.get_messages_analytics(
                waba_id, template_id, start_date, end_date
            )
            .get("data", {})
            .get("status_count")
        )

        return metrics_data

    def get_orders_metrics(self, start_date: date, end_date: date, utm_source: str):
        """
        Get orders metrics from VTEX API.
        """

        orders_data = self.orders_client.list(
            query_filters={
                "utm_source": (utm_source,),
                "ended_at__gte": str(start_date),
                "ended_at__lte": str(end_date),
            }
        )

        return orders_data

    def get_metrics(self, filters: dict):
        """
        Get metrics from Meta Graph API and VTEX API.
        """
        tz_name = "UTC"
        tz = pytz.timezone(tz_name)

        if "ended_at__gte" in filters:
            start_date = datetime.fromisoformat(filters["ended_at__gte"])

            if start_date and start_date.tzinfo is None:
                start_date = tz.localize(start_date)
            elif start_date and start_date.tzinfo:
                start_date = start_date.replace(tzinfo=tz)

            filters["ended_at__gte"] = start_date

        if "ended_at__lte" in filters:
            end_date = datetime.fromisoformat(filters["ended_at__lte"])

            if end_date and end_date.tzinfo is None:
                end_date = tz.localize(end_date)
            elif end_date and end_date.tzinfo:
                end_date = end_date.replace(tzinfo=tz)

            filters["ended_at__lte"] = end_date

        serializer = OrdersConversionsFiltersSerializer(data=filters)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]

        metrics_data = self.get_message_metrics(
            serializer.validated_data["waba_id"],
            serializer.validated_data["template_id"],
            start_date.date(),
            end_date.date(),
        )

        graph_data_fields = {}
        for status in ("sent", "delivered", "read", "clicked"):
            status_data = metrics_data.get(status, {})
            graph_data_fields[status] = OrdersConversionsGraphDataField(
                value=status_data.get("value", 0),
                percentage=status_data.get("percentage", 0),
            )

        orders_data = self.get_orders_metrics(
            start_date,
            end_date,
            serializer.validated_data["utm_source"],
        )

        utm_data = OrdersConversionsUTMData(
            count_sell=orders_data.get("countSell", 0),
            accumulated_total=orders_data.get("accumulatedTotal", 0),
            medium_ticket=orders_data.get("medium_ticket", 0),
            currency_code=orders_data.get("currencyCode", ""),
        )

        graph_data_fields["orders"] = {
            "value": utm_data.count_sell,
            "percentage": (
                round((utm_data.count_sell / graph_data_fields["sent"].value) * 100, 2)
                if graph_data_fields["sent"].value
                else 0
            ),
        }

        graph_data = OrdersConversionsGraphData(**graph_data_fields)
        orders_conversions = OrdersConversions(graph_data=graph_data, utm_data=utm_data)

        orders_conversions_serializer = OrdersConversionsMetricsSerializer(
            instance=orders_conversions
        )

        return orders_conversions_serializer.data
