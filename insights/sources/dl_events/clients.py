from abc import ABC, abstractmethod
from typing import Optional

from django.conf import settings

from weni_datalake_sdk.clients.redshift.events import (
    get_events,
    get_events_count,
    get_events_count_by_group,
    get_events_silver,
    get_events_silver_count,
    get_events_silver_count_by_group,
    get_events_sum,
    get_events_avg,
    get_events_max,
    get_events_min,
    get_events_unique_contact_urns,
    get_events_recurring_contact_urns,
    get_events_silver_unique_contact_urns,
    get_events_silver_recurring_contact_urns,
)


USE_SILVER_TABLES = settings.CONVERSATIONS_DASHBOARD_USE_SILVER_TABLES


class BaseDataLakeEventsClient(ABC):
    """
    Base class for the DataLakeEventsClient.
    """

    @abstractmethod
    def get_events(
        self, table: Optional[str] = None, **query_kwargs
    ) -> dict | list[dict]:
        """
        Get events from the DataLakeEvents source.
        """

    @abstractmethod
    def get_events_count(self, table: Optional[str] = None, **query_kwargs) -> dict:
        """
        Get the count of events from the DataLakeEvents source.
        """

    @abstractmethod
    def get_events_count_by_group(
        self, table: Optional[str] = None, **query_kwargs
    ) -> dict:
        """
        Get the count of events by group from the DataLakeEvents source.
        """

    @abstractmethod
    def get_events_sum(self, **query_kwargs) -> dict:
        """
        Get the sum of events from the DataLakeEvents source.
        """

    @abstractmethod
    def get_events_avg(self, **query_kwargs) -> dict:
        """
        Get the average of events from the DataLakeEvents source.
        """

    @abstractmethod
    def get_events_max(self, **query_kwargs) -> dict:
        """
        Get the maximum of events from the DataLakeEvents source.
        """

    @abstractmethod
    def get_events_min(self, **query_kwargs) -> dict:
        """
        Get the minimum of events from the DataLakeEvents source.
        """

    @abstractmethod
    def get_unique_contacts_count(self, **query_kwargs) -> int:
        """
        Get the count of unique contacts from the DataLakeEvents source.
        """

    @abstractmethod
    def get_returning_contacts_count(self, **query_kwargs) -> int:
        """
        Get the count of returning contacts from the DataLakeEvents source.
        """


class DataLakeEventsClient(BaseDataLakeEventsClient):
    """
    Client for the DataLakeEvents source.
    """

    def get_events(
        self, table: Optional[str] = None, **query_kwargs
    ) -> dict | list[dict]:
        """
        Get events from the DataLakeEvents source.
        """
        if table is not None and USE_SILVER_TABLES:
            query_kwargs["table"] = table
            method = get_events_silver
        else:
            method = get_events

        try:
            events = method(
                **query_kwargs,
            )
        except Exception as e:
            raise e

        return events

    def get_events_count(self, table: Optional[str] = None, **query_kwargs) -> dict:
        """
        Get the count of events from the DataLakeEvents source.
        """
        if table is not None and USE_SILVER_TABLES:
            query_kwargs["table"] = table
            method = get_events_silver_count
        else:
            method = get_events_count

        try:
            events = method(
                **query_kwargs,
            )
        except Exception as e:
            raise e

        return events

    def get_events_count_by_group(
        self, table: Optional[str] = None, **query_kwargs
    ) -> dict:
        """
        Get the count of events by group from the DataLakeEvents source.
        """
        if table is not None and USE_SILVER_TABLES:
            query_kwargs["table"] = table
            method = get_events_silver_count_by_group
        else:
            method = get_events_count_by_group

        try:
            events = method(
                **query_kwargs,
            )
        except Exception as e:
            raise e

        return events

    def get_events_sum(self, **query_kwargs) -> dict:
        """
        Get the sum of events from the DataLakeEvents source.
        """
        return get_events_sum(**query_kwargs)

    def get_events_avg(self, **query_kwargs) -> dict:
        """
        Get the average of events from the DataLakeEvents source.
        """
        return get_events_avg(**query_kwargs)

    def get_events_max(self, **query_kwargs) -> dict:
        """
        Get the maximum of events from the DataLakeEvents source.
        """
        return get_events_max(**query_kwargs)

    def get_events_min(self, **query_kwargs) -> dict:
        """
        Get the minimum of events from the DataLakeEvents source.
        """
        return get_events_min(**query_kwargs)

    def get_unique_contacts_count(
        self, table: Optional[str] = None, **query_kwargs
    ) -> int:
        if table is not None and USE_SILVER_TABLES:
            query_kwargs["table"] = table
            method = get_events_silver_unique_contact_urns
        else:
            method = get_events_unique_contact_urns

        try:
            return method(**query_kwargs)
        except Exception as e:
            raise e

    def get_returning_contacts_count(
        self, table: Optional[str] = None, **query_kwargs
    ) -> int:
        if table is not None and USE_SILVER_TABLES:
            query_kwargs["table"] = table
            method = get_events_silver_recurring_contact_urns
        else:
            method = get_events_recurring_contact_urns

        try:
            return method(**query_kwargs)
        except Exception as e:
            raise e
