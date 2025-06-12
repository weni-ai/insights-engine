from datetime import datetime
from uuid import UUID

from insights.db.postgres.django.connection import get_cursor


class ChatsClient:
    """
    Client for the chats database.
    """

    def get_rooms_numbers_by_queue(
        self, project_uuid: UUID, start_date: datetime, end_date: datetime
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
        JOIN
            rooms_room rr ON qq.uuid = rr.queue_id
        WHERE
            ss.project_id = %s
            AND rr.created_on BETWEEN %s AND %s
        GROUP BY
            qq.uuid, qq.name;
        """

        with get_cursor(db_name="chats") as cur:
            cur.execute(sql, (project_uuid, start_date, end_date))
            return cur.fetchall()
