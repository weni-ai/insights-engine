from insights.projects.models import Project
from insights.sources.vtex_conversions.services import VTEXOrdersConversionsService


class QueryExecutor:
    @staticmethod
    def execute(filters: dict, *args, project: Project, **kwargs):
        print("VTEX CONVERSIONS QUERY EXECUTOR - filters")
        print(filters)
        service = VTEXOrdersConversionsService(project)

        return service.get_metrics(filters)
