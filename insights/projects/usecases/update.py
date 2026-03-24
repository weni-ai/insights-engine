from insights.projects.models import Project


class UpdateProjectUseCase:
    """Use case for partially updating an existing Project's attributes."""

    def execute(
        self,
        project_uuid: str,
        name: str | None = None,
        timezone: str | None = None,
        date_format: str | None = None,
        config: dict | None = None,
    ) -> None:
        """Update the specified fields of a project.

        Only the fields provided with non-None values will be updated.

        Args:
            project_uuid: UUID of the project to update.
            name: New project name.
            timezone: New timezone identifier (e.g. "America/Sao_Paulo").
            date_format: New date format string (e.g. "DD/MM/YYYY").
            config: New configuration dictionary.

        Raises:
            Exception: If no project with the given UUID exists.
        """
        project: Project | None = Project.objects.filter(uuid=project_uuid).first()

        if project is None:
            raise Exception(
                f"[ UpdateProjectUseCase ] Project with uuid `{project_uuid}` does not exist."
            )

        fields_to_update = []

        for field, value in [
            ("name", name),
            ("timezone", timezone),
            ("date_format", date_format),
        ]:
            if value is not None:
                setattr(project, field, value)
                fields_to_update.append(field)

        if config is not None:
            existing_config = project.config or {}
            setattr(project, "config", {**existing_config, **config})
            fields_to_update.append("config")

        project.save(update_fields=fields_to_update)
