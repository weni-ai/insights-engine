import logging

from insights.projects.models import Project

logger = logging.getLogger(__name__)


class UpdateProjectVTEXAccount:
    """Use case for updating a project's VTEX account."""

    def execute(
        self,
        project: Project,
        vtex_account: str,
        user_email: str | None = None,
    ) -> Project:
        """Update the ``vtex_account`` field of the given project.

        Args:
            project: The project to update.
            vtex_account: The new VTEX account value.
            user_email: Email of the user performing the change. When ``None``
                (e.g. internal JWT requests), the change is attributed to
                ``"INTERNAL"`` in the audit log.

        Returns:
            The updated ``Project`` instance.
        """
        previous_value = project.vtex_account
        project.vtex_account = vtex_account
        project.save(update_fields=["vtex_account"])

        actor = user_email if user_email else "INTERNAL"

        logger.info(
            "[UpdateProjectVTEXAccount] VTEX Account for project %s (%s) "
            "changed from '%s' to '%s' by %s",
            project.name,
            project.uuid,
            previous_value,
            vtex_account,
            actor,
        )

        return project
