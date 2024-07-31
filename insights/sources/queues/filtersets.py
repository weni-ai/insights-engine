# use stub files to represent it on other parts of the code
# Use django_filters Filter class as a reference
from insights.sources.filtersets import GenericSQLFilter


class QueueFilterSet:
    project = GenericSQLFilter(
        source_field="project_id",
        table_alias="s",
        join_clause={
            "s": "INNER JOIN public.sectors_sector AS s ON s.uuid=q.sector_id",
        },
    )
    project_id = project
    sector = GenericSQLFilter(
        source_field="sector_id",
        table_alias="q",
    )
    sector_id = sector
    uuid = GenericSQLFilter(
        source_field="uuid",
        table_alias="q",
    )

    def get_field(self, field_name):
        try:
            return getattr(self, field_name)
        except AttributeError:
            return None
