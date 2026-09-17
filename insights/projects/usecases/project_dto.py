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
    inline_agent_switch: bool = False  # Equivalent to is_nexus_multi_agents_active
    is_live_desk_copilot: bool = False
    parent_project_uuid: str | None = None


@dataclass
class ProjectAuthCreationDTO:
    user_email: str
    project_uuid: str
    role: int
