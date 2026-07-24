import uuid
from datetime import timezone as dt_timezone
from typing import TypedDict

from django.db.models import Q
from django.utils import timezone

from insights.dashboards.models import Dashboard
from insights.projects.models import Project


class WhatsappPhoneNumber(TypedDict):
    id: str
    display_phone_number: str


class SaveWhatsappIntegrationUseCase:
    """
    Create the dashboard that represents a WhatsApp integration for a project.

    If a matching dashboard already exists, it is soft-deleted and a new one is
    created (instead of updating in place). Existing config keys are preserved
    and only the integration fields (and optional migration_data) are merged.
    When the project belongs to an organization that has a main project, a copy
    of the dashboard is also created in the main project.
    """

    def execute(
        self,
        project: Project,
        app_uuid: uuid.UUID,
        waba_id: str,
        phone_number: WhatsappPhoneNumber,
        old_waba_id: str | None = None,
    ) -> Dashboard:
        existing = self._find_existing(
            project=project,
            waba_id=waba_id,
            phone_number_id=phone_number["id"],
            old_waba_id=old_waba_id,
        )

        config = dict(existing.config) if existing and existing.config else {}
        config.update(
            {
                "is_whatsapp_integration": True,
                "app_uuid": str(app_uuid),
                "waba_id": waba_id,
                "phone_number": phone_number,
            }
        )

        if old_waba_id:
            config["migration_data"] = {
                "waba_id": old_waba_id,
                "migrated_at": timezone.now()
                .astimezone(dt_timezone.utc)
                .isoformat(),
            }

        self._soft_delete_existing(
            project=project,
            waba_id=waba_id,
            phone_number_id=phone_number["id"],
            old_waba_id=old_waba_id,
        )

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

        if main_project and main_project.pk != project.pk:
            self._soft_delete_existing(
                project=main_project,
                waba_id=waba_id,
                phone_number_id=phone_number["id"],
                old_waba_id=old_waba_id,
            )

            copy_name = f"{project.name} {phone_number['display_phone_number']}"
            Dashboard.objects.create(
                project=main_project,
                config=config,
                name=copy_name,
            )

        return dashboard

    def _matching_filter(
        self,
        waba_id: str,
        phone_number_id: str,
        old_waba_id: str | None = None,
    ) -> Q:
        matching = Q(config__phone_number__id=phone_number_id) | Q(
            config__waba_id=waba_id
        )
        if old_waba_id:
            matching |= Q(config__waba_id=old_waba_id)
        return matching

    def _find_existing(
        self,
        project: Project,
        waba_id: str,
        phone_number_id: str,
        old_waba_id: str | None = None,
    ) -> Dashboard | None:
        return (
            Dashboard.objects.filter(
                project=project,
                config__is_whatsapp_integration=True,
            )
            .filter(
                self._matching_filter(
                    waba_id=waba_id,
                    phone_number_id=phone_number_id,
                    old_waba_id=old_waba_id,
                )
            )
            .first()
        )

    def _soft_delete_existing(
        self,
        project: Project,
        waba_id: str,
        phone_number_id: str,
        old_waba_id: str | None = None,
    ) -> None:
        existing = Dashboard.objects.filter(
            project=project,
            config__is_whatsapp_integration=True,
        ).filter(
            self._matching_filter(
                waba_id=waba_id,
                phone_number_id=phone_number_id,
                old_waba_id=old_waba_id,
            )
        )

        for dashboard in existing:
            dashboard.delete()
