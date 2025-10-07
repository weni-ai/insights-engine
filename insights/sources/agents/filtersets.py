from insights.sources.filtersets import GenericSQLFilter


class AgentFilterSet:
    project = GenericSQLFilter(
        source_field="project_id",
        table_alias="pp",
    )
    project_id = project
    sector = GenericSQLFilter(
        source_field="sector_id",
        table_alias="q",
        join_clause={
            "r": "INNER JOIN public.rooms_room AS r ON r.user_id=pp.user_id",
            "q": "INNER JOIN public.queues_queue AS q ON q.uuid=r.queue_id",
        },
    )
    queue = GenericSQLFilter(
        source_field="queue_id",
        table_alias="r",
        join_clause={
            "r": "INNER JOIN public.rooms_room AS r ON r.user_id=pp.user_id",
        },
    )

    def get_field(self, field_name):
        try:
            return getattr(self, field_name)
        except AttributeError:
            return None
