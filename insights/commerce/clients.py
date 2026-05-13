import logging

import requests
from django.conf import settings
from requests.models import Response

from insights.commerce.exceptions import (
    BillingRequestError,
    RetailSetupRequestError,
)
from insights.internals.base import InternalAuthentication

logger = logging.getLogger(__name__)


class RetailSetupClient(InternalAuthentication):
    """
    Client for the internal Retail Setup service.

    Used to find out whether a project has the abandoned cart feature
    active, either through the new "integrated features" model or the
    legacy "gallery agents" model.
    """

    DEFAULT_TIMEOUT = 60

    def __init__(self):
        if not getattr(settings, "RETAIL_URL", ""):
            logger.warning("RETAIL_URL is not set; RetailSetupClient will fail at runtime")

        self.base_url = settings.RETAIL_URL
        self.timeout = self.DEFAULT_TIMEOUT

    def get_project_integrated_features(self, project_uuid: str) -> Response:
        """
        Return the integrated features registered for the project on the
        new model.
        """
        url = f"{self.base_url}/v2/app_integrated_feature/{project_uuid}/"

        try:
            return requests.get(url=url, headers=self.headers, timeout=self.timeout)
        except requests.RequestException as err:
            logger.error(
                "Error fetching integrated features for project %s: %s",
                project_uuid,
                err,
            )
            raise RetailSetupRequestError(str(err)) from err

    def get_project_agents(self, project_uuid: str) -> Response:
        """
        Return the agents available for the project on the legacy model.
        """
        url = f"{self.base_url}/v2/agents/{project_uuid}/"

        try:
            return requests.get(url=url, headers=self.headers, timeout=self.timeout)
        except requests.RequestException as err:
            logger.error(
                "Error fetching agents for project %s: %s",
                project_uuid,
                err,
            )
            raise RetailSetupRequestError(str(err)) from err


class BillingClient(InternalAuthentication):
    """
    Client for the internal Billing service.

    Used to retrieve the meta pricing rates configured for a project.
    """

    DEFAULT_TIMEOUT = 60

    def __init__(self):
        if not getattr(settings, "BILLING_URL", ""):
            logger.warning("BILLING_URL is not set; BillingClient will fail at runtime")

        self.base_url = settings.BILLING_URL
        self.timeout = self.DEFAULT_TIMEOUT

    def get_meta_pricing(self, project_uuid: str) -> Response:
        """
        Return the meta pricing rates configured for the project.
        """
        url = f"{self.base_url}/api/v1/meta-pricing/"

        try:
            return requests.get(
                url=url,
                headers=self.headers,
                params={"project_uuid": project_uuid},
                timeout=self.timeout,
            )
        except requests.RequestException as err:
            logger.error(
                "Error fetching meta pricing for project %s: %s",
                project_uuid,
                err,
            )
            raise BillingRequestError(str(err)) from err
