from insights.dashboards.models import Dashboard


class DashboardRetrieveUseCase:

    def get(self, pk=None):
        if pk:
            return Dashboard.objects.get(pk=pk)

        return Dashboard.objects.get(is_default=True)
