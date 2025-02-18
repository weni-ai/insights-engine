from insights.metrics.skills.services.base import BaseSkillMetricsService


class AbandonedCartSkillService(BaseSkillMetricsService):
    def validate_filters(self, filters: dict):
        # TODO
        return filters

    def get_metrics(self):
        filters = self.validate_filters(self.filters)

        return {}
