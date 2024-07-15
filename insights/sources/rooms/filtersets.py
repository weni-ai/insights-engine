# use stub files to represent it on other parts of the code
# Use django_filters Filter class as a reference
class RoomSQLFilter:
    """Responsible for cleaning and validating Filter data"""

    def __init__(
        self,
        source_field: str,
        table_alias: str,
        join_clause: dict = {},
        value: any = None,
    ) -> None:
        self.source_field = source_field
        self.table_alias = table_alias
        self.join_clause = join_clause
        self.value = value


class RoomFilterSet:
    agent = RoomSQLFilter(
        source_field="user_id",
        table_alias="r",
    )
    project = RoomSQLFilter(
        source_field="uuid",
        table_alias="p",
        join_clause={
            "q": "INNER JOIN public.queues_queue AS q ON q.uuid=r.queue_id",
            "s": "INNER JOIN public.sectors_sector AS s ON s.uuid=q.sector_id",
            "p": "INNER JOIN public.projects_project AS p ON p.uuid=s.project_id",
        },
    )
    tag = RoomSQLFilter(
        source_field="sectortag_id",
        table_alias="tg",
        join_clause={
            "tg": "INNER JOIN public.rooms_room_tags AS tg ON tg.room_id=r.uuid"
        },
    )
    tags = tag
    sector = RoomSQLFilter(
        source_field="sector_id",
        table_alias="q",
        join_clause={
            "q": "INNER JOIN public.queues_queue AS q ON q.uuid=r.queue_id",
        },
    )
    sector_id = sector
    queue = RoomSQLFilter(
        source_field="queue_id",
        table_alias="r",
    )
    contact = RoomSQLFilter(
        source_field="uuid",
        table_alias="ctt",
        join_clause={
            "q": "INNER JOIN public.contacts_contact AS ctt on ctt.uuid=r.contact_id",
        },
    )
    created_on = RoomSQLFilter(
        source_field="created_on",
        table_alias="r",
    )
    ended_at = RoomSQLFilter(
        source_field="ended_at",
        table_alias="r",
    )

    def get_field(self, field_name):
        try:
            return getattr(self, field_name)
        except AttributeError:
            return None
