from abc import ABC, abstractmethod
from weni_datalake_sdk.clients.redshift.events import get_events, get_events_count


class BaseDataLakeEventsClient(ABC):
    """
    Base class for the DataLakeEventsClient.
    """

    @abstractmethod
    def get_events(self, query_kwargs: dict) -> dict | list[dict]:
        """
        Get events from the DataLakeEvents source.
        """

    @abstractmethod
    def get_events_count(self, **query_kwargs) -> dict:
        """
        Get the count of events from the DataLakeEvents source.
        """


class DataLakeEventsClient(BaseDataLakeEventsClient):
    """
    Client for the DataLakeEvents source.
    """

    def get_events(self, **query_kwargs) -> dict | list[dict]:
        """
        Get events from the DataLakeEvents source.
        """
        try:
            events = get_events(
                **query_kwargs,
            )
        except Exception as e:
            raise e

        return events

    def get_events_count(self, **query_kwargs) -> dict:
        """
        Get the count of events from the DataLakeEvents source.
        """
        try:
            events = get_events_count(
                **query_kwargs,
            )
        except Exception as e:
            raise e

        return events
