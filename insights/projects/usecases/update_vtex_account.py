import logging

from django.db import transaction

from insights.projects.dataclass import UnlinkedProject
from insights.projects.models import Project

logger = logging.getLogger(__name__)


class UpdateProjectVTEXAccount:
    """Use case for updating a project's VTEX account."""

    def execute(
        self,
        project: Project,
        vtex_account: str,
        user_email: str | None = None,
    ) -> tuple[Project, list[UnlinkedProject]]:
        """Update the ``vtex_account`` field of the given project.

        If other projects already hold the same ``vtex_account``, their
        value is set to ``None`` within the same database transaction so
        that only one project owns a given VTEX account at a time.

        Args:
            project: The project to update.
            vtex_account: The new VTEX account value.
            user_email: Email of the user performing the change. When ``None``
                (e.g. internal JWT requests), the change is attributed to
                ``"INTERNAL"`` in the audit log.

        Returns:
            A tuple of the updated ``Project`` instance and a list of
            ``UnlinkedProject`` dataclass instances representing the
            projects that were unlinked.
        """
        actor = user_email if user_email else "INTERNAL"

        removed_projects = []

        with transaction.atomic():
            if vtex_account:
                conflicting = Project.objects.filter(
                    vtex_account=vtex_account,
                ).exclude(pk=project.pk)

                removed_projects = list(conflicting.values_list("name", "uuid"))

                if removed_projects:
                    conflicting.update(vtex_account=None)

            previous_value = project.vtex_account
            project.vtex_account = vtex_account
            project.save(update_fields=["vtex_account"])

        for name, uuid in removed_projects:
            logger.info(
                "[UpdateProjectVTEXAccount] Removed VTEX Account '%s' "
                "from project %s (%s) by %s",
                vtex_account,
                name,
                uuid,
                actor,
            )

        logger.info(
            "[UpdateProjectVTEXAccount] VTEX Account for project %s (%s) "
            "changed from '%s' to '%s' by %s",
            project.name,
            project.uuid,
            previous_value,
            vtex_account,
            actor,
        )

        projects_unlinked = [
            UnlinkedProject(uuid=str(uuid), name=name)
            for name, uuid in removed_projects
        ]

        return project, projects_unlinked
