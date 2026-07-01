import logging
from dataclasses import dataclass
from datetime import date

from sentry_sdk import capture_exception

from insights.metrics.meta.usecases.get_project_wabas import GetProjectWabasUseCase
from insights.metrics.meta.usecases.get_templates_from_prefix import (
    GetTemplatesFromPrefixUseCase,
)
from insights.metrics.meta.usecases.get_templates_metrics_from_multiple_wabas import (
    GetTemplatesMetricsFromMultipleWabasUseCase,
    WabaTemplateIDs,
)
from insights.metrics.templates_and_orders.exceptions import (
    ErrorGettingOrdersMetrics,
    TemplatesNotFoundError,
)
from insights.metrics.vtex.services.orders_service import OrdersService
from insights.projects.models import Project

logger = logging.getLogger(__name__)


@dataclass
class MetricsLimits:
    max_wabas: int | None = None
    max_template_ids: int | None = None


class GetTemplatesAndOrdersMetrics:
    def __init__(
        self,
        get_project_wabas: GetProjectWabasUseCase | None = None,
        get_templates_from_prefix: GetTemplatesFromPrefixUseCase | None = None,
        get_templates_metrics: GetTemplatesMetricsFromMultipleWabasUseCase | None = None,
    ):
        self.get_project_wabas = get_project_wabas or GetProjectWabasUseCase()
        self.get_templates_from_prefix = (
            get_templates_from_prefix or GetTemplatesFromPrefixUseCase()
        )
        self.get_templates_metrics = (
            get_templates_metrics or GetTemplatesMetricsFromMultipleWabasUseCase()
        )

    def _get_template_metrics(
        self,
        project: Project,
        template_name_prefix: str,
        start_date: date,
        end_date: date,
        limits: MetricsLimits | None = None,
        require_templates: bool = False,
    ) -> dict:
        waba_ids = self.get_project_wabas.execute(project)

        if limits and limits.max_wabas is not None:
            waba_ids = waba_ids[: limits.max_wabas]

        waba_templates: list[WabaTemplateIDs] = []
        any_templates = False
        for waba_id in waba_ids:
            template_ids = self.get_templates_from_prefix.execute(
                waba_id=waba_id,
                prefix=template_name_prefix,
                max_template_ids=(
                    limits.max_template_ids if limits else None
                ),
            )
            if template_ids:
                any_templates = True
                waba_templates.append(
                    WabaTemplateIDs(waba_id=waba_id, template_ids=template_ids)
                )

        if require_templates and not any_templates:
            raise TemplatesNotFoundError(
                "No templates found for the project"
            )

        return self.get_templates_metrics.execute(
            waba_templates=waba_templates,
            start_date=start_date,
            end_date=end_date,
        )

    def _get_orders_metrics(
        self,
        project: Project,
        utm_source: str,
        start_date: date,
        end_date: date,
    ) -> dict:
        service = OrdersService(project)

        filters = {
            "start_date": start_date,
            "end_date": end_date,
        }

        try:
            return service.get_metrics_from_utm_source(
                utm_source=utm_source, filters=filters
            )
        except Exception as e:
            capture_exception(e)
            logger.error("Error getting orders from VTEX: %s", e, exc_info=True)
            raise ErrorGettingOrdersMetrics("Error getting orders from VTEX") from e

    def execute(
        self,
        project: Project,
        start_date: date,
        end_date: date,
        utm_source: str,
        template_name_prefix: str,
        limits: MetricsLimits | None = None,
        require_templates: bool = False,
    ) -> dict:
        template_metrics = self._get_template_metrics(
            project=project,
            template_name_prefix=template_name_prefix,
            start_date=start_date,
            end_date=end_date,
            limits=limits,
            require_templates=require_templates,
        )

        orders_metrics = self._get_orders_metrics(
            project=project,
            utm_source=utm_source,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "template_metrics": template_metrics,
            "orders_metrics": orders_metrics,
        }
