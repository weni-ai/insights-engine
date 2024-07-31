# use stub files to represent it on other parts of the code
# Use django_filters Filter class as a reference
from insights.sources.filtersets import GenericSQLFilter


class TagFilterSet:
    project = GenericSQLFilter(
        source_field="project_id",
        table_alias="s",
        join_clause={
            "s": "INNER JOIN public.sectors_sector AS s ON s.uuid=tg.sector_id",
        },
    )
    sector = GenericSQLFilter(
        source_field="sector_id",
        table_alias="tg",
    )
    sector_id = sector

    def get_field(self, field_name):
        try:
            return getattr(self, field_name)
        except AttributeError:
            return None
