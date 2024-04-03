from dataclasses import dataclass


@dataclass
class ProjectCreationDTO:
    uuid: str
    name: str
    is_template: bool
    timezone: str = ""
    date_format: str = ""


@dataclass
class ProjectAuthCreationDTO:
    user_email: str
    project_uuid: str
    role: int
