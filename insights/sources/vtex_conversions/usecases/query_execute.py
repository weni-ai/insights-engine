import json
import logging

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied


from insights.metrics.meta.clients import MetaGraphAPIClient
from insights.projects.models import Project
from insights.sources.cache import CacheClient
from insights.sources.integrations.clients import WeniIntegrationsClient
from insights.sources.orders.clients import VtexOrdersRestClient
from insights.sources.vtex_conversions.services import VTEXOrdersConversionsService
from insights.sources.vtexcredentials.clients import AuthRestClient
from insights.sources.vtexcredentials.exceptions import VtexCredentialsNotFound

logger = logging.getLogger(__name__)


class QueryExecutor:
    @classmethod
    def get_vtex_credentials(cls, project: Project):

        if getattr(settings, "VTEX_ORDERS_CREDENTIALS", None):
            # TEMPORARY, this should be used only in the development and staging environments
            return {"vtex_credentials": json.loads(settings.VTEX_ORDERS_CREDENTIALS)}

        vtex_credentials_client = AuthRestClient(project=project.uuid)

        try:
            credentials = vtex_credentials_client.get_vtex_auth()
        except VtexCredentialsNotFound as e:
            logger.error(
                "VTEX credentials not found for project %s while checking permissions in the VTEX orders conversions service",
                project.uuid,
            )
            raise PermissionDenied(
                detail=_("Project does not have the credentials to access VTEX's API"),
                code="project_without_vtex_credentials",
            ) from e
        except Exception as e:
            logger.error(
                "Error while getting VTEX credentials for project %s while checking permissions in the VTEX orders conversions service",
                project.uuid,
            )
            raise e

        return credentials

    @classmethod
    def execute(cls, filters: dict, *args, project: Project, **kwargs):
        meta_api_client = MetaGraphAPIClient()
        integrations_client = WeniIntegrationsClient()
        vtex_credentials = cls.get_vtex_credentials(project)
        orders_client = VtexOrdersRestClient(vtex_credentials, CacheClient())

        service = VTEXOrdersConversionsService(
            project, meta_api_client, integrations_client, orders_client
        )

        return service.get_metrics(filters)
