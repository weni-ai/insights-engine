import json
from unittest.mock import patch
from uuid import UUID

from django.test import TestCase, override_settings

from insights.metrics.conversations.usecases._resolve_project_agent_by_slugs import (
    resolve_project_agent_by_slugs,
)
from insights.metrics.conversations.usecases.get_project_concierge_agent import (
    GetProjectConciergeAgentUseCase,
)
from insights.metrics.conversations.usecases.get_project_payment_agent import (
    GetProjectPaymentAgentUseCase,
)
from insights.projects.models import Project
from insights.sources.integrations.tests.mock_clients import MockNexusClient, MockResponse

CONCIERGE_UUID = UUID("11111111-1111-1111-1111-111111111111")
PAYMENT_UUID = UUID("22222222-2222-2222-2222-222222222222")
OTHER_UUID = UUID("33333333-3333-3333-3333-333333333333")


def _agents_team_response(agents: list[dict]) -> MockResponse:
    return MockResponse(
        status_code=200,
        content=json.dumps({"manager": {"external_id": ""}, "agents": agents}),
    )


def _agent(uuid: str, slug: str, name: str = "Agent") -> dict:
    return {
        "uuid": uuid,
        "slug": slug,
        "name": name,
        "about": {"en": "", "pt": None, "es": None},
        "group": None,
        "is_official": True,
        "mcps": None,
        "active": True,
    }


class TestResolveProjectAgentBySlugs(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.nexus_client = MockNexusClient()

    def test_returns_none_when_agent_slugs_is_empty(self):
        with patch.object(
            self.nexus_client, "get_project_agents_team"
        ) as mock_get_agents_team:
            result = resolve_project_agent_by_slugs(
                project_uuid=self.project.uuid,
                agent_slugs=[],
                agent_role="concierge",
                nexus_client=self.nexus_client,
            )

        self.assertIsNone(result)
        mock_get_agents_team.assert_not_called()

    def test_returns_uuid_when_single_agent_matches(self):
        with patch.object(
            self.nexus_client,
            "get_project_agents_team",
            return_value=_agents_team_response(
                [_agent(str(CONCIERGE_UUID), "concierge")]
            ),
        ):
            result = resolve_project_agent_by_slugs(
                project_uuid=self.project.uuid,
                agent_slugs=["concierge", "alternative_concierge"],
                agent_role="concierge",
                nexus_client=self.nexus_client,
            )

        self.assertEqual(result, CONCIERGE_UUID)

    def test_returns_first_matching_agent_in_nexus_order(self):
        with patch.object(
            self.nexus_client,
            "get_project_agents_team",
            return_value=_agents_team_response(
                [
                    _agent(str(OTHER_UUID), "other"),
                    _agent(str(CONCIERGE_UUID), "concierge"),
                    _agent(str(PAYMENT_UUID), "alternative_concierge"),
                ]
            ),
        ):
            result = resolve_project_agent_by_slugs(
                project_uuid=self.project.uuid,
                agent_slugs=["concierge", "alternative_concierge"],
                agent_role="concierge",
                nexus_client=self.nexus_client,
            )

        self.assertEqual(result, CONCIERGE_UUID)

    @patch(
        "insights.metrics.conversations.usecases._resolve_project_agent_by_slugs.logger"
    )
    def test_logs_warning_and_returns_first_when_multiple_agents_match(
        self, mock_logger
    ):
        with patch.object(
            self.nexus_client,
            "get_project_agents_team",
            return_value=_agents_team_response(
                [
                    _agent(str(CONCIERGE_UUID), "concierge"),
                    _agent(str(PAYMENT_UUID), "alternative_concierge"),
                ]
            ),
        ):
            result = resolve_project_agent_by_slugs(
                project_uuid=self.project.uuid,
                agent_slugs=["concierge", "alternative_concierge"],
                agent_role="concierge",
                nexus_client=self.nexus_client,
            )

        self.assertEqual(result, CONCIERGE_UUID)
        mock_logger.warning.assert_called_once()
        warning_args = mock_logger.warning.call_args[0]
        self.assertIn("concierge", warning_args[1])
        self.assertEqual(warning_args[2], self.project.uuid)
        self.assertEqual(warning_args[3], "Test Project")
        self.assertEqual(
            warning_args[5],
            [
                {"slug": "concierge", "uuid": str(CONCIERGE_UUID)},
                {"slug": "alternative_concierge", "uuid": str(PAYMENT_UUID)},
            ],
        )

    def test_returns_none_when_no_agent_matches(self):
        with patch.object(
            self.nexus_client,
            "get_project_agents_team",
            return_value=_agents_team_response(
                [_agent(str(OTHER_UUID), "other")]
            ),
        ):
            result = resolve_project_agent_by_slugs(
                project_uuid=self.project.uuid,
                agent_slugs=["concierge"],
                agent_role="concierge",
                nexus_client=self.nexus_client,
            )

        self.assertIsNone(result)

    def test_skips_agents_without_uuid(self):
        with patch.object(
            self.nexus_client,
            "get_project_agents_team",
            return_value=_agents_team_response(
                [{"slug": "concierge", "name": "Concierge"}]
            ),
        ):
            result = resolve_project_agent_by_slugs(
                project_uuid=self.project.uuid,
                agent_slugs=["concierge"],
                agent_role="concierge",
                nexus_client=self.nexus_client,
            )

        self.assertIsNone(result)

    @patch(
        "insights.metrics.conversations.usecases._resolve_project_agent_by_slugs.capture_exception"
    )
    @patch(
        "insights.metrics.conversations.usecases._resolve_project_agent_by_slugs.logger"
    )
    def test_returns_none_when_nexus_returns_non_success(
        self, mock_logger, mock_capture_exception
    ):
        with patch.object(
            self.nexus_client,
            "get_project_agents_team",
            return_value=MockResponse(status_code=500, content="error"),
        ):
            result = resolve_project_agent_by_slugs(
                project_uuid=self.project.uuid,
                agent_slugs=["concierge"],
                agent_role="concierge",
                nexus_client=self.nexus_client,
            )

        self.assertIsNone(result)
        mock_logger.error.assert_called_once()
        mock_capture_exception.assert_called_once()

    @patch(
        "insights.metrics.conversations.usecases._resolve_project_agent_by_slugs.capture_exception"
    )
    @patch(
        "insights.metrics.conversations.usecases._resolve_project_agent_by_slugs.logger"
    )
    def test_returns_none_when_agents_list_is_missing(
        self, mock_logger, mock_capture_exception
    ):
        with patch.object(
            self.nexus_client,
            "get_project_agents_team",
            return_value=MockResponse(status_code=200, content=json.dumps({})),
        ):
            result = resolve_project_agent_by_slugs(
                project_uuid=self.project.uuid,
                agent_slugs=["concierge"],
                agent_role="concierge",
                nexus_client=self.nexus_client,
            )

        self.assertIsNone(result)
        mock_logger.error.assert_called_once()
        mock_capture_exception.assert_called_once()


class TestGetProjectConciergeAgentUseCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Concierge Project")
        self.nexus_client = MockNexusClient()
        self.use_case = GetProjectConciergeAgentUseCase(
            nexus_client=self.nexus_client
        )

    @override_settings(
        CONVERSATIONS_METRICS_CONCIERGE_AGENT_SLUGS=["concierge", "alternative_concierge"]
    )
    def test_execute_returns_matching_concierge_agent_uuid(self):
        with patch.object(
            self.nexus_client,
            "get_project_agents_team",
            return_value=_agents_team_response(
                [_agent(str(CONCIERGE_UUID), "alternative_concierge")]
            ),
        ) as mock_get_agents_team:
            result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertEqual(result, CONCIERGE_UUID)
        mock_get_agents_team.assert_called_once_with(self.project.uuid)

    @override_settings(CONVERSATIONS_METRICS_CONCIERGE_AGENT_SLUGS=[])
    def test_execute_returns_none_when_slugs_not_configured(self):
        with patch.object(
            self.nexus_client, "get_project_agents_team"
        ) as mock_get_agents_team:
            result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertIsNone(result)
        mock_get_agents_team.assert_not_called()


class TestGetProjectPaymentAgentUseCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Payment Project")
        self.nexus_client = MockNexusClient()
        self.use_case = GetProjectPaymentAgentUseCase(nexus_client=self.nexus_client)

    @override_settings(
        CONVERSATIONS_METRICS_PAYMENT_AGENT_SLUGS=["payment", "alternative_payment"]
    )
    def test_execute_returns_matching_payment_agent_uuid(self):
        with patch.object(
            self.nexus_client,
            "get_project_agents_team",
            return_value=_agents_team_response(
                [_agent(str(PAYMENT_UUID), "payment")]
            ),
        ) as mock_get_agents_team:
            result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertEqual(result, PAYMENT_UUID)
        mock_get_agents_team.assert_called_once_with(self.project.uuid)

    @override_settings(CONVERSATIONS_METRICS_PAYMENT_AGENT_SLUGS=[])
    def test_execute_returns_none_when_slugs_not_configured(self):
        with patch.object(
            self.nexus_client, "get_project_agents_team"
        ) as mock_get_agents_team:
            result = self.use_case.execute(project_uuid=self.project.uuid)

        self.assertIsNone(result)
        mock_get_agents_team.assert_not_called()
