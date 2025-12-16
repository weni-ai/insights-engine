from typing import TypedDict


class EventDataType(TypedDict):
    """
    TypedDict to store events data.
    """

    event_name: str
    key: str
    date: int
    contact_urn: str
    value_type: str
    value: str
    metadata: str  # this is JSON but is returned as a string
