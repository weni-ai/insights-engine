from dataclasses import dataclass


@dataclass
class TicketID:
    ticket_id: str

    def __init__(self, ticket_id: str):
        self.ticket_id = ticket_id
