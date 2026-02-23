import pytz
from datetime import date, datetime
from logging import getLogger

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied
from sentry_sdk import capture_message

from insights.dashboards.models import Dashboard
from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.metrics.meta.enums import ProductType
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
        return Dashboard.objects.filter(
            project=self.project,
            config__is_whatsapp_integration=True,
            config__waba_id=waba_id,
        ).exists()

    def get_message_metrics(
        self,
        waba_id: str,
        template_id: str,
        start_date: date,
        end_date: date,
        product_type: str = ProductType.CLOUD_API.value,
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
                waba_id, template_id, start_date, end_date, product_type=product_type
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

        waba_id = serializer.validated_data["waba_id"]

        use_mm_lite = Dashboard.objects.filter(
            project=self.project,
            config__is_whatsapp_integration=True,
            config__waba_id=waba_id,
            config__is_mm_lite_active=True,
        ).exists()

        cloud_api_metrics_data = self.get_message_metrics(
            waba_id,
            serializer.validated_data["template_id"],
            start_date.date(),
            end_date.date(),
        )

        raw_graph_data_fields = {}
        sent_total = 0

        for status in ("sent", "delivered", "read", "clicked"):
            status_data = cloud_api_metrics_data.get(status, {})

            raw_graph_data_fields[status] = {
                "value": status_data.get("value", 0),
            }

            if status == "sent":
                sent_total += status_data.get("value", 0)

        if use_mm_lite:
            mm_lite_metrics_data = self.get_message_metrics(
                waba_id,
                serializer.validated_data["template_id"],
                start_date.date(),
                end_date.date(),
                product_type=ProductType.MM_LITE.value,
            )

            for status in ("sent", "delivered", "read", "clicked"):
                status_data = mm_lite_metrics_data.get(status, {})
                raw_graph_data_fields[status]["value"] += status_data.get("value", 0)

                if status == "sent":
                    sent_total += status_data.get("value", 0)

        graph_data_fields = {}

        for status, data in raw_graph_data_fields.items():
            graph_data_fields[status] = OrdersConversionsGraphDataField(
                value=data["value"],
                percentage=(
                    round((data["value"] / sent_total) * 100, 2)
                    if sent_total > 0
                    else 0
                ),
            )

        orders_data = self.get_orders_metrics(
            start_date,
            end_date,
            serializer.validated_data["utm_source"],
        )

        if not isinstance(orders_data, dict):
            error_msg = "Error fetching orders. Orders data is not a dictionary. Orders data: %s"
            logger.error(
                error_msg,
                orders_data,
            )
            capture_message(
                error_msg,
                orders_data,
            )
            raise Exception("Error fetching orders.")

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
