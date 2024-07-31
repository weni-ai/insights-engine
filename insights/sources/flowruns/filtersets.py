# use stub files to represent it on other parts of the code
# Use django_filters Filter class as a reference
from insights.sources.filtersets import GenericElasticSearchFilter


class FlowRunFilterSet:
    created_on = GenericElasticSearchFilter(
        source_field="created_on",
        field_type="date",
    )
    exited_on = GenericElasticSearchFilter(
        source_field="exited_on",
        field_type="date",
    )
    ended_at = GenericElasticSearchFilter(
        source_field="exited_on",
        field_type="date",
    )
    project = GenericElasticSearchFilter(
        source_field="project_uuid",
        field_type="string",
    )
    flow = GenericElasticSearchFilter(
        source_field="flow_uuid",
        field_type="string",
    )

    def get_field(self, field_name):
        try:
            return getattr(self, field_name)
        except AttributeError:
            return None
