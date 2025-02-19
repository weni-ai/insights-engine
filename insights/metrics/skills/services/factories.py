from typing import TYPE_CHECKING
from insights.metrics.skills.services.abandoned_cart import AbandonedCartSkillService

if TYPE_CHECKING:
    from insights.metrics.skills.services.base import BaseSkillMetricsService
    from insights.projects.models import Project


SERVICE_FACTORY_MAP = {
    "abandoned_cart": AbandonedCartSkillService,
}


class SkillMetricsServiceFactory:
    @staticmethod
    def get_service(
        skill_name: str, project: "Project", filters: dict
    ) -> "BaseSkillMetricsService":
        service = SERVICE_FACTORY_MAP.get(skill_name)

        if service is None:
            raise ValueError(f"Invalid skill name: {skill_name}")

        return service(project, filters)
