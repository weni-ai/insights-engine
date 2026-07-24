import uuid
from copy import deepcopy
from datetime import timezone as dt_timezone
from typing import TypedDict

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

    When old_waba_id is provided, every active WhatsApp dashboard in the project
    (and main project copy, if any) with that waba_id is migrated 1:1 — soft-deleted
    and recreated with the new waba_id and migration_data — so multiple phone
    numbers under the same WABA are all preserved. Favorite templates are moved
    asynchronously from each old dashboard to the corresponding new one.

    Without old_waba_id, matching is by phone_number.id only, so other numbers
    on the same WABA are left untouched.

    When the project belongs to an organization that has a main project, a copy
    of each created dashboard is also created in the main project.
    """

    def execute(
        self,
        project: Project,
        app_uuid: uuid.UUID,
        waba_id: str,
        phone_number: WhatsappPhoneNumber,
        old_waba_id: str | None = None,
    ) -> Dashboard:
        if old_waba_id:
            return self._migrate_waba(
                project=project,
                app_uuid=app_uuid,
                waba_id=waba_id,
                phone_number=phone_number,
                old_waba_id=old_waba_id,
            )

        return self._upsert_by_phone(
            project=project,
            app_uuid=app_uuid,
            waba_id=waba_id,
            phone_number=phone_number,
            migration_data=None,
        )

    def _migrate_waba(
        self,
        *,
        project: Project,
        app_uuid: uuid.UUID,
        waba_id: str,
        phone_number: WhatsappPhoneNumber,
        old_waba_id: str,
    ) -> Dashboard:
        migrated_at = timezone.now().astimezone(dt_timezone.utc).isoformat()
        migration_data = {
            "waba_id": old_waba_id,
            "migrated_at": migrated_at,
        }

        old_dashboards = list(
            Dashboard.objects.filter(
                project=project,
                config__is_whatsapp_integration=True,
                config__waba_id=old_waba_id,
            )
        )

        created: list[Dashboard] = []
        for old in old_dashboards:
            created.append(
                self._recreate_dashboard(
                    project=project,
                    source=old,
                    app_uuid=app_uuid,
                    waba_id=waba_id,
                    phone_number=(old.config or {}).get("phone_number")
                    or phone_number,
                    migration_data=migration_data,
                    name_prefix="Meta",
                )
            )

        self._migrate_main_project_copies(
            source_project=project,
            app_uuid=app_uuid,
            waba_id=waba_id,
            old_waba_id=old_waba_id,
            migration_data=migration_data,
            created_dashboards=created,
        )

        if not created:
            return self._upsert_by_phone(
                project=project,
                app_uuid=app_uuid,
                waba_id=waba_id,
                phone_number=phone_number,
                migration_data=migration_data,
            )

        for dashboard in created:
            config_phone = (dashboard.config or {}).get("phone_number") or {}
            if config_phone.get("id") == phone_number["id"]:
                return dashboard

        return created[0]

    def _upsert_by_phone(
        self,
        *,
        project: Project,
        app_uuid: uuid.UUID,
        waba_id: str,
        phone_number: WhatsappPhoneNumber,
        migration_data: dict | None,
    ) -> Dashboard:
        existing = (
            Dashboard.objects.filter(
                project=project,
                config__is_whatsapp_integration=True,
                config__phone_number__id=phone_number["id"],
            ).first()
        )

        dashboard = self._recreate_dashboard(
            project=project,
            source=existing,
            app_uuid=app_uuid,
            waba_id=waba_id,
            phone_number=phone_number,
            migration_data=migration_data,
            name_prefix="Meta",
        )

        main_project = self._get_main_project(project)
        if main_project and main_project.pk != project.pk:
            main_existing = (
                Dashboard.objects.filter(
                    project=main_project,
                    config__is_whatsapp_integration=True,
                    config__phone_number__id=phone_number["id"],
                ).first()
            )
            self._recreate_dashboard(
                project=main_project,
                source=main_existing,
                app_uuid=app_uuid,
                waba_id=waba_id,
                phone_number=phone_number,
                migration_data=migration_data,
                name_prefix=project.name,
                config_override=dict(dashboard.config),
            )

        return dashboard

    def _migrate_main_project_copies(
        self,
        *,
        source_project: Project,
        app_uuid: uuid.UUID,
        waba_id: str,
        old_waba_id: str,
        migration_data: dict,
        created_dashboards: list[Dashboard],
    ) -> None:
        main_project = self._get_main_project(source_project)
        if not main_project or main_project.pk == source_project.pk:
            return

        main_old_dashboards = list(
            Dashboard.objects.filter(
                project=main_project,
                config__is_whatsapp_integration=True,
                config__waba_id=old_waba_id,
            )
        )

        if main_old_dashboards:
            for old in main_old_dashboards:
                self._recreate_dashboard(
                    project=main_project,
                    source=old,
                    app_uuid=app_uuid,
                    waba_id=waba_id,
                    phone_number=(old.config or {}).get("phone_number") or {},
                    migration_data=migration_data,
                    name_prefix=source_project.name,
                )
            return

        for dashboard in created_dashboards:
            phone = (dashboard.config or {}).get("phone_number") or {}
            phone_id = phone.get("id")
            main_existing = None
            if phone_id:
                main_existing = (
                    Dashboard.objects.filter(
                        project=main_project,
                        config__is_whatsapp_integration=True,
                        config__phone_number__id=phone_id,
                    ).first()
                )
            self._recreate_dashboard(
                project=main_project,
                source=main_existing,
                app_uuid=app_uuid,
                waba_id=waba_id,
                phone_number=phone,
                migration_data=migration_data,
                name_prefix=source_project.name,
                config_override=dict(dashboard.config),
            )

    def _recreate_dashboard(
        self,
        *,
        project: Project,
        source: Dashboard | None,
        app_uuid: uuid.UUID,
        waba_id: str,
        phone_number: WhatsappPhoneNumber | dict,
        migration_data: dict | None,
        name_prefix: str,
        config_override: dict | None = None,
    ) -> Dashboard:
        if config_override is not None:
            config = deepcopy(config_override)
        else:
            config = deepcopy(source.config) if source and source.config else {}

        config.update(
            {
                "is_whatsapp_integration": True,
                "app_uuid": str(app_uuid),
                "waba_id": waba_id,
                "phone_number": phone_number,
            }
        )
        if migration_data is not None:
            config["migration_data"] = migration_data

        old_dashboard_uuid = source.uuid if source is not None else None
        if source is not None:
            source.delete()

        display = (
            phone_number.get("display_phone_number")
            if isinstance(phone_number, dict)
            else None
        ) or "unknown"

        dashboard = Dashboard.objects.create(
            project=project,
            config=config,
            name=f"{name_prefix} {display}",
        )

        if old_dashboard_uuid is not None and migration_data is not None:
            self._enqueue_move_favorite_templates(
                old_dashboard_uuid=old_dashboard_uuid,
                new_dashboard_uuid=dashboard.uuid,
            )

        return dashboard

    def _enqueue_move_favorite_templates(
        self,
        *,
        old_dashboard_uuid: uuid.UUID,
        new_dashboard_uuid: uuid.UUID,
    ) -> None:
        from insights.metrics.meta.tasks import move_favorite_templates

        move_favorite_templates.delay(
            str(old_dashboard_uuid),
            str(new_dashboard_uuid),
        )

    def _get_main_project(self, project: Project) -> Project | None:
        if not project.org_uuid:
            return None
        return Project.objects.filter(
            org_uuid=project.org_uuid,
            config__is_main_project=True,
        ).first()
