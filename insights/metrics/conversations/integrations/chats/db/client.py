from typing import TYPE_CHECKING

from insights.db.postgres.django.connection import get_cursor
from insights.metrics.conversations.integrations.chats.db.dataclass import RoomsByQueue


if TYPE_CHECKING:
    from uuid import UUID
    from datetime import datetime


class ChatsClient:
    """
    Client for the chats database.
    """

    def get_rooms_numbers_by_queue(
        self, project_uuid: "UUID", start_date: "datetime", end_date: "datetime"
    ):
        """
        Get the number of rooms by queue.

        Args:
            project_uuid: The UUID of the project.
            start_date: The start date of the period.
            end_date: The end date of the period.
        """
        sql = """
        SELECT
            qq.uuid,
            qq.name,
            COUNT(DISTINCT rr.uuid) AS rooms_number
        FROM
            queues_queue qq
        JOIN
            sectors_sector ss ON qq.sector_id = ss.uuid
        LEFT JOIN
            rooms_room rr ON qq.uuid = rr.queue_id
            AND rr.created_on BETWEEN %s AND %s
        WHERE
            ss.project_id = %s
            AND qq.is_deleted IS FALSE
            AND ss.is_deleted IS FALSE
        GROUP BY
            qq.uuid, qq.name
        ORDER BY
            rooms_number DESC;
        """

        with get_cursor(db_name="chats") as cur:
            cur.execute(sql, (start_date, end_date, project_uuid))
            rows = cur.fetchall()

            for row in rows:
                yield RoomsByQueue(
                    queue_uuid=row[0],
                    queue_name=row[1],
                    rooms_number=row[2],
                )
