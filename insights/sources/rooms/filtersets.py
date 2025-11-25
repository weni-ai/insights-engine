from insights.sources.filtersets import GenericSQLFilter

# use stub files to represent it on other parts of the code
# Use django_filters Filter class as a reference


class RoomFilterSet:
    agent = GenericSQLFilter(
        source_field="user_id",
        table_alias="r",
    )
    project = GenericSQLFilter(
        source_field="uuid",
        table_alias="p",
        join_clause={
            "q": "INNER JOIN public.queues_queue AS q ON q.uuid=r.queue_id AND q.is_deleted=false",
            "s": "INNER JOIN public.sectors_sector AS s ON s.uuid=q.sector_id AND s.is_deleted=false",
            "p": "INNER JOIN public.projects_project AS p ON p.uuid=s.project_id",
        },
    )
    tag = GenericSQLFilter(
        source_field="sectortag_id",
        table_alias="tg",
        join_clause={
            "tg": "INNER JOIN public.rooms_room_tags AS tg ON tg.room_id=r.uuid"
        },
    )
    tags = tag
    sector = GenericSQLFilter(
        source_field="sector_id",
        table_alias="q",
        join_clause={
            "q": "INNER JOIN public.queues_queue AS q ON q.uuid=r.queue_id AND q.is_deleted=false",
        },
    )
    sector_id = sector
    queue = GenericSQLFilter(
        source_field="queue_id",
        table_alias="r",
        join_clause={
            "q": "INNER JOIN public.queues_queue AS q ON q.uuid=r.queue_id AND q.is_deleted=false",
        },
    )
    contact = GenericSQLFilter(
        source_field="uuid",
        table_alias="ctt",
        join_clause={
            "ctt": "INNER JOIN public.contacts_contact AS ctt on ctt.uuid=r.contact_id",
        },
    )
    created_on = GenericSQLFilter(
        source_field="created_on",
        table_alias="r",
    )
    ended_at = GenericSQLFilter(
        source_field="ended_at",
        table_alias="r",
    )
    user = GenericSQLFilter(
        source_field="user_id",
        table_alias="r",
    )
    user_id = user
    is_active = GenericSQLFilter(
        source_field="is_active",
        table_alias="r",
    )
    protocol = GenericSQLFilter(
        source_field="protocol",
        table_alias="r",
    )

    def get_field(self, field_name):
        try:
            return getattr(self, field_name)
        except AttributeError:
            return None
