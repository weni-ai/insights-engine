from django.db.models import Q

from insights.dashboards.models import CONVERSATION_DASHBOARD_NAME, Dashboard
from insights.projects.models import Project


class ConversationsDashboardCreation:
    """
    This class is used to create a conversations dashboard for a project.
    """

    @classmethod
    def get_for_project(cls, project: Project) -> Dashboard | None:
        """
        Get the conversations dashboard for a project.
        """
        return Dashboard.objects.filter(
            project=project,
            name=CONVERSATION_DASHBOARD_NAME,
        ).first()

    @classmethod
    def get_params(cls, project: Project) -> dict:
        return {
            "name": CONVERSATION_DASHBOARD_NAME,
            "description": "Conversations dashboard",
            "grid": [],
            "is_deletable": False,
            "is_editable": False,
            "project": project,
        }

    @classmethod
    def create_for_project(cls, project: Project) -> Dashboard:
        """
        Create a conversations dashboard for a project.
        """
        if existing_dashboard := cls.get_for_project(project):
            return existing_dashboard

        dashboard = Dashboard.objects.create(**cls.get_params(project))

        return dashboard

    @classmethod
    def create_for_all_projects(cls, bulk_size=1000) -> int:
        """
        Create a conversations dashboard for all projects.
        """
        dashboards_to_create = []
        current_index = 0

        created = 0

        for project in Project.objects.filter(
            ~Q(dashboards__name=CONVERSATION_DASHBOARD_NAME)
        ):
            dashboards_to_create.append(Dashboard(**cls.get_params(project)))

            if len(dashboards_to_create) >= bulk_size:
                Dashboard.objects.bulk_create(dashboards_to_create)
                dashboards_to_create = []
                created += bulk_size

            current_index += 1

        if dashboards_to_create:
            Dashboard.objects.bulk_create(dashboards_to_create)
            created += len(dashboards_to_create)

        return created
