from insights.dashboards.tasks import create_conversation_dashboard
from insights.projects.models import Project
from insights.projects.tasks import handle_project_created_with_inline_agent_switch

from .project_dto import ProjectCreationDTO

from insights.dashboards.usecases.human_service_dashboard_creation import (
    CreateHumanService,
)


class ProjectsUseCase:

    def get_by_uuid(self, project_uuid: str) -> Project:
        try:
            return Project.objects.get(uuid=project_uuid)
        except Project.DoesNotExist:
            raise Exception(
                f"[ ProjectsUseCase ] Project with uuid `{project_uuid}` does not exists!"
            )
        except Exception as exception:
            raise Exception(f"[ ProjectsUseCase ] error: {str(exception)}")

    def get_main_project(self, org_uuid: str) -> Project:
        return Project.objects.filter(
            org_uuid=org_uuid, config__is_main_project=True
        ).first()

    def create_project(self, project_dto: ProjectCreationDTO) -> Project:

        main_project = self.get_main_project(project_dto.org_uuid)

        if main_project:
            config = {
                "is_secondary_project": True,
            }
        else:
            config = None

        is_live_desk_copilot = bool(project_dto.is_live_desk_copilot)
        parent_project_uuid = (
            project_dto.parent_project_uuid if is_live_desk_copilot else None
        )
        if is_live_desk_copilot and not parent_project_uuid:
            raise Exception(
                "'parent_project_uuid' cannot be empty when "
                "'is_live_desk_copilot' is True!"
            )

        project = Project.objects.create(
            uuid=project_dto.uuid,
            name=project_dto.name,
            is_template=project_dto.is_template,
            timezone=project_dto.timezone,
            date_format=project_dto.date_format,
            vtex_account=project_dto.vtex_account,
            org_uuid=project_dto.org_uuid,
            is_nexus_multi_agents_active=project_dto.inline_agent_switch or False,
            config=config,
            is_live_desk_copilot=is_live_desk_copilot,
            parent_project_uuid=parent_project_uuid,
        )
        CreateHumanService().create_dashboard(project)
        create_conversation_dashboard.delay(project.uuid)

        if project.is_nexus_multi_agents_active:
            handle_project_created_with_inline_agent_switch.delay(project.uuid)

        return project
