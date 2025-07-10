from weni_datalake_sdk.clients.redshift.events import get_events


class DataLakeEventsClient:
    """
    Client for the DataLakeEvents source.
    """

    def get_events(self, query_kwargs: dict) -> dict | list[dict]:
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
