from insights.dashboards.models import Dashboard
from insights.projects.models import Project


class RemoveWhatsappIntegrationUseCase:
    """
    Remove the dashboards that represent a WhatsApp integration for the
    given project and waba_id. When the project belongs to an organization
    that has a main project, the dashboard copy in the main project is also
    removed.
    """

    def execute(self, project: Project, waba_id: str) -> int:
        projects = [project]

        main_project = Project.objects.filter(
            org_uuid=project.org_uuid,
            config__is_main_project=True,
        ).first()

        if main_project and main_project.pk != project.pk:
            projects.append(main_project)

        deleted_count, _ = Dashboard.objects.filter(
            project__in=projects,
            config__waba_id=waba_id,
            config__is_whatsapp_integration=True,
        ).delete()

        return deleted_count
