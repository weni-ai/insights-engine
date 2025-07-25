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
