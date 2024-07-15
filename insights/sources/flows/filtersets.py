# use stub files to represent it on other parts of the code
# Use django_filters Filter class as a reference
from insights.sources.filtersets import GenericSQLFilter


class FlowsFilterSet:
    project = GenericSQLFilter(
        source_field="proj_uuid",
        table_alias="o",
        join_clause={"o": "INNER JOIN public.orgs_org AS o ON o.id=f.org_id"},
    )
    project_id = project

    def get_field(self, field_name):
        try:
            return getattr(self, field_name)
        except AttributeError:
            return None
