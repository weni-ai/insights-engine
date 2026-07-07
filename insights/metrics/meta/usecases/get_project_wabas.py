from insights.dashboards.models import Dashboard
from insights.projects.models import Project


class GetProjectWabasUseCase:
    def execute(self, project: Project) -> list[str]:
        configs = Dashboard.objects.filter(
            project=project,
            config__is_whatsapp_integration=True,
        ).values_list("config", flat=True)

        seen = set()
        waba_ids = []
        for config in configs:
            waba_id = config.get("waba_id")
            if waba_id and waba_id not in seen:
                seen.add(waba_id)
                waba_ids.append(waba_id)

        return waba_ids
