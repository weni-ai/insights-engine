# use stub files to represent it on other parts of the code
# Use django_filters Filter class as a reference
from insights.sources.filtersets import GenericSQLFilter


class SectorFilterSet:
    project = GenericSQLFilter(
        source_field="project_id",
        table_alias="s",
    )
    project_id = project
    uuid = GenericSQLFilter(
        source_field="uuid",
        table_alias="s",
    )

    def get_field(self, field_name):
        try:
            return getattr(self, field_name)
        except AttributeError:
            return None
