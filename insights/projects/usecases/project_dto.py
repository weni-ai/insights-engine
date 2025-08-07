from dataclasses import dataclass


@dataclass
class ProjectCreationDTO:
    uuid: str
    name: str
    is_template: bool
    timezone: str = ""
    date_format: str = ""
    vtex_account: str | None = None
    org_uuid: str | None = None


@dataclass
class ProjectAuthCreationDTO:
    user_email: str
    project_uuid: str
    role: int
