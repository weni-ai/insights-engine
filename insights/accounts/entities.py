from dataclasses import dataclass


@dataclass
class User:
    uuid: str = None
    email: str = None
    first_name: str = None
    last_name: str = None
