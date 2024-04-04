from dataclasses import dataclass


@dataclass
class DashboardCreationDTO:
    project: str
    name: str
    description: str
    is_default: bool = False
    from_template: bool = False
    template: str = None
