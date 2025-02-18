from insights.metrics.skills.exceptions import (
    InvalidDateRangeError,
    MissingFiltersError,
)
from insights.metrics.skills.services.base import BaseSkillMetricsService
from insights.metrics.skills.validators import validate_date_str


class AbandonedCartSkillService(BaseSkillMetricsService):
    def validate_filters(self, filters: dict):
        required_fields = ["start_date", "end_date"]
        missing_fields = []
        valid_fields = {}

        for field in required_fields:
            if field not in filters:
                missing_fields.append(field)
            else:
                valid_fields[field] = validate_date_str(filters[field])

        if valid_fields["start_date"] > valid_fields["end_date"]:
            raise InvalidDateRangeError("End date must be greater than start date")

        if missing_fields:
            raise MissingFiltersError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

        return valid_fields

    def get_metrics(self):
        filters = self.validate_filters(self.filters)

        return {}
