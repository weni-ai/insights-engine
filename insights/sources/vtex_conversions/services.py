from datetime import date
from logging import getLogger

from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied

from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.projects.models import Project
from insights.sources.cache import CacheClient
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
from insights.sources.vtexcredentials.clients import AuthRestClient
from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound


logger = getLogger(__name__)


class VTEXOrdersConversionsService:
    """
    Service to get orders conversions from Meta Graph API and VTEX API.
    """

    def __init__(self, project: Project):
        self.project = project

        self.meta_api_client = MetaGraphAPIClient()
        self.integrations_client = WeniIntegrationsClient()

        self.vtex_credentials_client = AuthRestClient(project=self.project.uuid)
        self.orders_client_class = VtexOrdersRestClient

    def project_has_permission_to_access_waba(self, waba_id: str) -> bool:
        """
        Check if the project has permission to access the WABA.
        """

        try:
            project_wabas = self.integrations_client.get_wabas_for_project(
                self.project.uuid
            )
        except Exception as e:
            raise e

        return waba_id in project_wabas

    def get_credentials(self, waba_id: str) -> dict:
        """
        Get VTEX credentials for project and check if the project has permission
        to access Meta's Graph API for the selected WABA.
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

        try:
            credentials = self.vtex_credentials_client.get_vtex_auth()
        except VtexCredentialsNotFound as e:
            logger.error(
                "VTEX credentials not found for project %s while checking permissions in the VTEX orders conversions service",
                self.project.uuid,
            )
            raise PermissionDenied(
                detail=_("Project does not have the credentials to access VTEX's API"),
                code="project_without_vtex_credentials",
            ) from e
        except Exception as e:
            logger.error(
                "Error while getting VTEX credentials for project %s while checking permissions in the VTEX orders conversions service",
                self.project.uuid,
            )
            raise e

        return {"vtex_credentials": credentials}

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

    def get_orders_metrics(
        self, credentials, start_date: date, end_date: date, utm_source: str
    ):
        """
        Get orders metrics from VTEX API.
        """

        orders_client = self.orders_client_class(
            auth_params=credentials,
            cache_client=CacheClient(),
        )

        orders_data = orders_client.list(
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

        serializer = OrdersConversionsFiltersSerializer(data=filters)
        serializer.is_valid(raise_exception=True)

        vtex_credentials = self.get_credentials(
            serializer.validated_data["waba_id"]
        ).get("vtex_credentials")

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

        orders_data = self.get_orders_metrics(
            vtex_credentials,
            serializer.validated_data["start_date"],
            serializer.validated_data["end_date"],
            serializer.validated_data["utm_source"],
        )

        utm_data = OrdersConversionsUTMData(
            count_sell=orders_data.get("countSell", 0),
            accumulated_total=orders_data.get("accumulatedTotal", 0),
            medium_ticket=orders_data.get("medium_ticket", 0),
            currency_code=orders_data.get("currencyCode", ""),
        )

        # The percentage is calculated based on the number of orders
        # that were made based on the message with the UTM source
        graph_data.orders.value = utm_data.count_sell
        graph_data.orders.percentage = (
            round((utm_data.count_sell / graph_data.sent.value) * 100, 2)
            if graph_data.sent.value
            else 0
        )

        orders_conversions = OrdersConversions(graph_data=graph_data, utm_data=utm_data)
        orders_conversions_serializer = OrdersConversionsMetricsSerializer(
            instance=orders_conversions
        )

        return orders_conversions_serializer.data
