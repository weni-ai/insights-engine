from insights.sources.dl_events.clients import BaseDataLakeEventsClient
from insights.sources.dl_events.tests.factories import ClassificationEventFactory


class ClassificationMockDataLakeEventsClient(BaseDataLakeEventsClient):
    """
    Mock client for the DataLakeEvents source.
    """

    def get_events(self, **query_kwargs) -> dict | list[dict]:
        """
        Get events from the DataLakeEvents source.
        """

        return [ClassificationEventFactory() for _ in range(10)]

    def get_events_count(self, **query_kwargs) -> dict:
        """
        Get events count from the DataLakeEvents source.
        """

        return [{"count": 10}]

    def get_events_count_by_group(self, **query_kwargs) -> dict:
        """
        Get events count by group from the DataLakeEvents source.
        """

        return [{"payload_value": "1", "count": 10}]
