from abc import ABC, abstractmethod
from weni_datalake_sdk.clients.redshift.events import get_events


class BaseDataLakeEventsClient(ABC):
    """
    Base class for the DataLakeEventsClient.
    """

    @abstractmethod
    def get_events(self, query_kwargs: dict) -> dict | list[dict]:
        """
        Get events from the DataLakeEvents source.
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
