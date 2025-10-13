from abc import ABC, abstractmethod
from weni_datalake_sdk.clients.redshift.events import (
    get_events,
    get_events_count,
    get_events_count_by_group,
)


class BaseDataLakeEventsClient(ABC):
    """
    Base class for the DataLakeEventsClient.
    """

    @abstractmethod
    def get_events(
        self, use_silver_tables: bool = False, **query_kwargs
    ) -> dict | list[dict]:
        """
        Get events from the DataLakeEvents source.
        """

    @abstractmethod
    def get_events_count(self, use_silver_tables: bool = False, **query_kwargs) -> dict:
        """
        Get the count of events from the DataLakeEvents source.
        """

    @abstractmethod
    def get_events_count_by_group(
        self, use_silver_tables: bool = False, **query_kwargs
    ) -> dict:
        """
        Get the count of events by group from the DataLakeEvents source.
        """


class DataLakeEventsClient(BaseDataLakeEventsClient):
    """
    Client for the DataLakeEvents source.
    """

    def get_events(
        self, use_silver_tables: bool = False, **query_kwargs
    ) -> dict | list[dict]:
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

    def get_events_count(self, use_silver_tables: bool = False, **query_kwargs) -> dict:
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

    def get_events_count_by_group(
        self, use_silver_tables: bool = False, **query_kwargs
    ) -> dict:
        """
        Get the count of events by group from the DataLakeEvents source.
        """
        try:
            events = get_events_count_by_group(
                **query_kwargs,
            )
        except Exception as e:
            raise e

        return events
