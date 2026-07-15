import logging
from uuid import UUID

from rest_framework import status as rest_status
from sentry_sdk import capture_exception

from insights.projects.models import Project
from insights.sources.integrations.clients import BaseNexusClient

logger = logging.getLogger(__name__)


def resolve_project_agent_by_slugs(
    *,
    project_uuid: UUID,
    agent_slugs: list[str],
    agent_role: str,
    nexus_client: BaseNexusClient,
) -> str | None:
    """
    Resolve a project agent UUID by matching configured slugs against the Nexus agents team.

    Returns the first matching agent UUID, or None when no match is found or the lookup fails.
    Logs a warning when more than one agent matches.
    """
    if not agent_slugs:
        return None

    try:
        response = nexus_client.get_project_agents_team(project_uuid)
        if not rest_status.is_success(response.status_code):
            raise ValueError(
                f"Nexus agents team returned {response.status_code}: {response.text}"
            )
        payload = response.json()
        agents = payload.get("agents") if isinstance(payload, dict) else None
        if not isinstance(agents, list):
            raise ValueError("Nexus agents team response missing 'agents' list")
    except Exception as e:
        logger.error(
            "[CONVERSATIONS METRICS] Failed to fetch project agents from Nexus for %s: %s",
            project_uuid,
            e,
        )
        capture_exception(e)
        return None

    configured_slugs = set(agent_slugs)
    matched_agents = [
        agent
        for agent in agents
        if isinstance(agent, dict)
        and agent.get("slug") in configured_slugs
        and agent.get("uuid")
    ]

    if not matched_agents:
        return None

    if len(matched_agents) > 1:
        project_name = (
            Project.objects.filter(uuid=project_uuid)
            .values_list("name", flat=True)
            .first()
        )
        logger.warning(
            "[CONVERSATIONS METRICS] Multiple %s agents found for project %s (%s). "
            "Configured slugs: %s. Matched agents: %s. Using first match.",
            agent_role,
            project_uuid,
            project_name,
            agent_slugs,
            [
                {"slug": agent["slug"], "uuid": agent["uuid"]}
                for agent in matched_agents
            ],
        )

    return matched_agents[0]["uuid"]
