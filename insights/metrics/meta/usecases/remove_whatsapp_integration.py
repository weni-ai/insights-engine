from uuid import UUID

from insights.dashboards.models import Dashboard
from insights.projects.models import Project


class RemoveWhatsappIntegrationUseCase:
    """
    Use case to remove WhatsApp integration dashboards for a project.

    When the project belongs to an organization that has a main project,
    matching dashboards are also removed from the main project.
    """

    def execute(self, project_uuid: UUID, waba_id: str) -> int:
        current_project = Project.objects.filter(uuid=project_uuid).first()

        projects = [current_project]

        main_project = Project.objects.filter(
            org_uuid=current_project.org_uuid,
            config__is_main_project=True,
        ).first()

        if main_project:
            projects.append(main_project)

        deleted_count, _ = Dashboard.objects.filter(
            project__in=projects,
            config__waba_id=waba_id,
        ).delete()

        return deleted_count
