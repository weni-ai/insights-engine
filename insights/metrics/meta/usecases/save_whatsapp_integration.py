import uuid
from typing import TypedDict

from insights.dashboards.models import Dashboard
from insights.projects.models import Project


class WhatsappPhoneNumber(TypedDict):
    id: str
    display_phone_number: str


class SaveWhatsappIntegrationUseCase:
    """
    Create or update the dashboard that represents a WhatsApp integration
    for a project. When the project belongs to an organization that has a
    main project, a copy of the dashboard is also created in the main project.
    """

    def execute(
        self,
        project: Project,
        app_uuid: uuid.UUID,
        waba_id: str,
        phone_number: WhatsappPhoneNumber,
    ) -> Dashboard:
        config = {
            "is_whatsapp_integration": True,
            "app_uuid": str(app_uuid),
            "waba_id": waba_id,
            "phone_number": phone_number,
        }

        dashboard = Dashboard.objects.filter(
            project=project,
            config__phone_number__id=phone_number["id"],
            config__is_whatsapp_integration=True,
        ).first()

        if dashboard:
            dashboard.config = config
            dashboard.save(update_fields=["config"])
        else:
            name = f"Meta {phone_number['display_phone_number']}"
            dashboard = Dashboard.objects.create(
                project=project,
                config=config,
                name=name,
            )

        main_project = Project.objects.filter(
            org_uuid=project.org_uuid,
            config__is_main_project=True,
        ).first()

        if main_project:
            copy_name = f"{project.name} {phone_number['display_phone_number']}"
            Dashboard.objects.create(
                project=main_project,
                config=config,
                name=copy_name,
            )

        return dashboard
