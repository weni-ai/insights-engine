import uuid
from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase
import json

from insights.authentication.authentication import User
from insights.authentication.services.tests.test_jwt_service import (
    generate_private_key,
    generate_private_key_pem,
    generate_public_key_pem,
)
from insights.authentication.tests.decorators import (
    with_internal_auth,
    with_project_auth,
)
from insights.dashboards.models import Dashboard
from insights.metrics.conversations.dataclass import (
    AgentInvocationAgent,
    AgentInvocationItem,
    AgentInvocationMetrics,
    AvailableWidgetsList,
    AvgConversationsPerContactMetricsData,
    ContactMetricsData,
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
    CrosstabItemData,
    CrosstabSubItemData,
    ReturningContactsMetricsData,
    SalesFunnelMetrics,
    ToolResultAgent,
    ToolResultItem,
    ToolResultMetrics,
    UniqueContactsMetricsData,
)
from insights.metrics.conversations.enums import (
    AvailableWidgets,
    AvailableWidgetsListType,
    ConversationType,
    CsatMetricsType,
    NpsMetricsType,
)
from insights.metrics.conversations.integrations.datalake.services import (
    BaseDatalakeConversationsMetricsService,
)
from insights.metrics.conversations.services import (
    ConversationsMetricsService,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
)
from insights.metrics.conversations.api.v1.views import ConversationsMetricsViewSet
from insights.projects.models import Project
from insights.sources.flowruns.tests.mock_query_executor import (
    MockFlowRunsQueryExecutor,
)
from insights.sources.integrations.tests.mock_clients import MockResponse
from insights.widgets.models import Widget
from insights.dashboards.models import Dashboard
from insights.sources.integrations.clients import NexusConversationsAPIClient


JWT_PRIVATE_KEY = generate_private_key()
JWT_PRIVATE_KEY_PEM = generate_private_key_pem(JWT_PRIVATE_KEY)
JWT_PUBLIC_KEY_PEM = generate_public_key_pem(JWT_PRIVATE_KEY.public_key())


class BaseTestConversationsMetricsViewSet(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.original_service = ConversationsMetricsViewSet.service

        nexus_conversations_client = MagicMock(spec=NexusConversationsAPIClient)
        nexus_conversations_client.get_topics.return_value = MockResponse(
            status_code=200, content=json.dumps([])
        )
        nexus_conversations_client.get_subtopics.return_value = MockResponse(
            status_code=200, content=json.dumps([])
        )
        nexus_conversations_client.create_topic.return_value = MockResponse(
            status_code=201, content=json.dumps({})
        )
        nexus_conversations_client.create_subtopic.return_value = MockResponse(
            status_code=201, content=json.dumps({})
        )
        nexus_conversations_client.delete_topic.return_value = MockResponse(
            status_code=204, content=json.dumps({})
        )
        nexus_conversations_client.delete_subtopic.return_value = MockResponse(
            status_code=204, content=json.dumps({})
        )

        ConversationsMetricsViewSet.service = ConversationsMetricsService(
            datalake_service=MagicMock(spec=BaseDatalakeConversationsMetricsService),
            nexus_conversations_client=nexus_conversations_client,
            flowruns_query_executor=MockFlowRunsQueryExecutor,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        ConversationsMetricsViewSet.service = cls.original_service

    def get_totals(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/totals/"

        return self.client.get(url, query_params)

    def get_nps(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/nps/"

        return self.client.get(url, query_params)

    def get_topics(self, query_params: dict) -> Response:
        url = reverse("conversations-topics")

        return self.client.get(url, query_params, format="json")

    def get_subtopics(self, topic_uuid: uuid.UUID, query_params: dict) -> Response:
        url = reverse("conversations-subtopics", kwargs={"topic_uuid": topic_uuid})

        return self.client.get(url, query_params, format="json")

    def create_topic(self, data: dict) -> Response:
        url = reverse("conversations-topics")

        return self.client.post(url, data, format="json")

    def create_subtopic(self, topic_uuid: uuid.UUID, data: dict) -> Response:
        url = reverse("conversations-subtopics", kwargs={"topic_uuid": topic_uuid})

        return self.client.post(url, data, format="json")

    def delete_topic(self, topic_uuid: uuid.UUID, data: dict) -> Response:
        url = reverse("conversations-topic", kwargs={"topic_uuid": topic_uuid})

        return self.client.delete(url, data, format="json")

    def delete_subtopic(
        self, topic_uuid: uuid.UUID, subtopic_uuid: uuid.UUID, data: dict
    ) -> Response:
        url = reverse(
            "conversations-subtopic",
            kwargs={"topic_uuid": topic_uuid, "subtopic_uuid": subtopic_uuid},
        )

        return self.client.delete(url, data, format="json")

    def get_topics_distribution(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/topics-distribution/"

        return self.client.get(url, query_params)

    def get_totals(self, query_params: dict) -> Response:
        url = "/v1/metrics/conversations/totals/"

        return self.client.get(url, query_params)

    def get_csat_metrics(self, query_params: dict) -> Response:
        url = reverse("conversations-csat")

        return self.client.get(url, query_params, format="json")

    def get_nps_metrics(self, query_params: dict) -> Response:
        url = reverse("conversations-nps")

        return self.client.get(url, query_params, format="json")

    def get_custom_metrics(self, query_params: dict) -> Response:
        url = reverse("conversations-custom")

        return self.client.get(url, query_params, format="json")

    def get_sales_funnel_metrics(self, query_params: dict) -> Response:
        url = reverse("conversations-sales-funnel")

        return self.client.get(url, query_params, format="json")

    def get_crosstab_metrics(self, query_params: dict) -> Response:
        url = reverse("conversations-crosstab")

        return self.client.get(url, query_params, format="json")

    def get_available_widgets(self, query_params: dict) -> Response:
        url = reverse("conversations-available-widgets")

        return self.client.get(url, query_params, format="json")

    def get_absolute_numbers(self, query_params: dict) -> Response:
        url = reverse("conversations-absolute-numbers")

        return self.client.get(url, query_params, format="json")

    def get_tool_result(self, query_params: dict) -> Response:
        url = reverse("conversations-tool-result")

        return self.client.get(url, query_params, format="json")

    def get_agent_invocation(self, query_params: dict) -> Response:
        url = reverse("conversations-agent-invocation")

        return self.client.get(url, query_params, format="json")

    def get_contacts_metrics(self, query_params: dict) -> Response:
        url = reverse("conversations-contacts")

        return self.client.get(url, query_params, format="json")


class TestConversationsMetricsViewSetAsAnonymousUser(
    BaseTestConversationsMetricsViewSet
):
    def test_cannot_get_totals_when_not_authenticated(self):
        response = self.get_totals({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_nps_when_unauthenticated(self):
        response = self.get_nps({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_topics_distribution_when_unauthenticated(self):
        response = self.get_topics_distribution({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_topics_when_unauthenticated(self):
        response = self.get_topics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_subtopics_when_unauthenticated(self):
        response = self.get_subtopics(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_topic_when_unauthenticated(self):
        response = self.create_topic({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_create_subtopic_when_unauthenticated(self):
        response = self.create_subtopic(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_delete_topic_when_unauthenticated(self):
        response = self.delete_topic(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_delete_subtopic_when_unauthenticated(self):
        response = self.delete_subtopic(uuid.uuid4(), uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_topics_distribution_when_unauthenticated(self):
        response = self.get_topics_distribution({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_totals_when_not_authenticated(self):
        response = self.get_totals({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_csat_metrics_when_unauthenticated(self):
        response = self.get_csat_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_nps_metrics_when_unauthenticated(self):
        response = self.get_nps_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_custom_metrics_when_unauthenticated(self):
        response = self.get_custom_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_sales_funnel_metrics_when_unauthenticated(self):
        response = self.get_sales_funnel_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_crosstab_metrics_when_unauthenticated(self):
        response = self.get_crosstab_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_available_widgets_when_unauthenticated(self):
        response = self.get_available_widgets({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_available_widgets_when_unauthenticated(self):
        response = self.get_available_widgets({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_crosstab_metrics_when_unauthenticated(self):
        response = self.get_crosstab_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_absolute_numbers_when_unauthenticated(self):
        response = self.get_absolute_numbers({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_tool_result_when_unauthenticated(self):
        response = self.get_tool_result({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_agent_invocation_when_unauthenticated(self):
        response = self.get_agent_invocation({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_get_contacts_metrics_when_unauthenticated(self):
        response = self.get_contacts_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConversationsMetricsViewSetAsAuthenticatedUser(
    BaseTestConversationsMetricsViewSet
):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@test.com")
        self.project = Project.objects.create(name="Test Project")  # type: ignore
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )

        self.client.force_authenticate(self.user)

    def test_cannot_get_totals_without_permission(self):
        response = self.get_totals(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-01",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_get_totals_without_project_uuid(self):
        response = self.get_totals({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    @with_project_auth
    def test_cannot_get_totals_without_required_query_params(self):
        response = self.get_totals({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_totals"
    )
    def test_get_totals(self, mock_get_totals):
        mock_get_totals.return_value = ConversationsTotalsMetrics(
            total_conversations=ConversationsTotalsMetric(value=100, percentage=100),
            resolved=ConversationsTotalsMetric(value=60, percentage=60),
            unresolved=ConversationsTotalsMetric(value=40, percentage=40),
            transferred_to_human=ConversationsTotalsMetric(value=0, percentage=0),
        )

        response = self.get_totals(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-01",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_conversations"]["value"], 100)
        self.assertEqual(response.data["total_conversations"]["percentage"], 100)
        self.assertEqual(response.data["resolved"]["value"], 60)
        self.assertEqual(response.data["resolved"]["percentage"], 60)
        self.assertEqual(response.data["unresolved"]["value"], 40)
        self.assertEqual(response.data["unresolved"]["percentage"], 40)

    def test_cannot_get_topics_distribution_without_permission(self):
        response = self.get_topics_distribution({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_topics_distribution_without_required_fields(self):
        response = self.get_topics_distribution({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["start_date"][0].code,
            "required",
        )
        self.assertEqual(
            response.data["end_date"][0].code,
            "required",
        )

    def test_cannot_get_nps_without_project_uuid(self):
        response = self.get_nps({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_nps_without_permission(self):
        response = self.get_nps({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_nps_without_required_query_params(self):
        response = self.get_nps({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")
        self.assertEqual(response.data["type"][0].code, "required")

    def test_cannot_get_topics_without_project_uuid(self):
        response = self.get_topics({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_topics_without_project_permission(self):
        response = self.get_topics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_get_topics(self):
        response = self.get_topics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_get_subtopics_without_project_uuid(self):
        response = self.get_subtopics(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_subtopics_without_project_permission(self):
        response = self.get_subtopics(uuid.uuid4(), {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_get_subtopics(self):
        topic_uuid = uuid.uuid4()

        response = self.get_subtopics(
            topic_uuid,
            {"project_uuid": self.project.uuid},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @with_project_auth
    def test_cannot_create_topic_without_required_fields(self):
        response = self.create_topic({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")
        self.assertEqual(response.data["name"][0].code, "required")
        self.assertEqual(response.data["description"][0].code, "required")

    @with_project_auth
    def test_create_topic(self):
        response = self.create_topic(
            {
                "project_uuid": self.project.uuid,
                "name": "Test Topic",
                "description": "Test Description",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_create_subtopic_without_project_permission(self):
        response = self.create_subtopic(
            uuid.uuid4(),
            {
                "project_uuid": self.project.uuid,
                "name": "Test Subtopic",
                "description": "Test Subtopic Description",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_create_subtopic_without_required_fields(self):
        response = self.create_topic({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")
        self.assertEqual(response.data["name"][0].code, "required")
        self.assertEqual(response.data["description"][0].code, "required")

    @with_project_auth
    def test_create_subtopic(self):
        topic_uuid = uuid.uuid4()
        response = self.create_subtopic(
            topic_uuid,
            {
                "project_uuid": self.project.uuid,
                "name": "Test Subtopic",
                "description": "Test Subtopic Description",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_delete_topic_without_project_uuid(self):
        response = self.delete_topic(uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_delete_topic_without_project_permission(self):
        response = self.delete_topic(uuid.uuid4(), {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_delete_topic(self):
        response = self.delete_topic(uuid.uuid4(), {"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_subtopic_without_project_uuid(self):
        response = self.delete_subtopic(uuid.uuid4(), uuid.uuid4(), {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_delete_subtopic_without_project_permission(self):
        response = self.delete_subtopic(
            uuid.uuid4(), uuid.uuid4(), {"project_uuid": self.project.uuid}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_delete_subtopic(self):
        response = self.delete_subtopic(
            uuid.uuid4(), uuid.uuid4(), {"project_uuid": self.project.uuid}
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_get_topics_distribution_without_project_uuid(self):
        response = self.get_topics_distribution({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["project_uuid"][0].code,
            "required",
        )

    @with_project_auth
    def test_get_topics_distribution(self):
        response = self.get_topics_distribution(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2021-01-01",
                "end_date": "2021-01-02",
                "type": ConversationType.AI,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("topics", response.data)
        self.assertIn("uuid", response.data["topics"][0])
        self.assertIn("name", response.data["topics"][0])
        self.assertIn("quantity", response.data["topics"][0])
        self.assertIn("subtopics", response.data["topics"][0])
        self.assertIn("percentage", response.data["topics"][0])

    def test_cannot_get_csat_metrics_without_project_uuid(self):
        response = self.get_csat_metrics({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_csat_metrics_without_permission(self):
        response = self.get_csat_metrics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_csat_metrics_without_required_params(self):
        response = self.get_csat_metrics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["widget_uuid"][0].code, "required")
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")
        self.assertEqual(response.data["type"][0].code, "required")

    @with_project_auth
    def test_get_csat_metrics_human(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                    "op_field": "csat",
                },
                "operation": "recurrence",
                "op_field": "result",
            },
        )

        response = self.get_csat_metrics(
            {
                "project_uuid": self.project.uuid,
                "widget_uuid": widget.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "type": CsatMetricsType.HUMAN,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_get_nps_metrics_without_project_uuid(self):
        response = self.get_nps_metrics({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_nps_metrics_without_permission(self):
        response = self.get_nps_metrics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_nps_metrics_without_required_params(self):
        response = self.get_nps_metrics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["widget_uuid"][0].code, "required")
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")
        self.assertEqual(response.data["type"][0].code, "required")

    @with_project_auth
    def test_get_nps_metrics_human(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                    "op_field": "nps",
                },
                "operation": "recurrence",
                "op_field": "result",
            },
        )

        response = self.get_nps_metrics(
            {
                "project_uuid": self.project.uuid,
                "widget_uuid": widget.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "type": NpsMetricsType.HUMAN,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @with_project_auth
    def test_get_nps_metrics_ai(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="flowruns",
            type="flow_result",
            position=[1, 2],
            config={
                "filter": {
                    "flow": "123",
                    "op_field": "nps",
                },
                "operation": "recurrence",
                "op_field": "result",
                "datalake_config": {
                    "agent_uuid": str(uuid.uuid4()),
                },
            },
        )

        response = self.get_nps_metrics(
            {
                "project_uuid": self.project.uuid,
                "widget_uuid": widget.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "type": NpsMetricsType.AI,
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_get_custom_metrics_without_permission(self):
        response = self.get_custom_metrics(
            {
                "project_uuid": self.project.uuid,
                "widget_uuid": uuid.uuid4(),
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_get_custom_metrics_without_project_uuid(self):
        response = self.get_custom_metrics({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    @with_project_auth
    def test_cannot_get_custom_metrics_without_required_params(self):
        response = self.get_custom_metrics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["widget_uuid"][0].code, "required")
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")

    @with_project_auth
    def test_get_custom_metrics(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.custom",
            type="custom",
            position=[1, 2],
            config={
                "datalake_config": {
                    "agent_uuid": str(uuid.uuid4()),
                    "key": "test_key",
                },
            },
        )

        response = self.get_custom_metrics(
            {
                "project_uuid": self.project.uuid,
                "widget_uuid": widget.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_get_sales_funnel_metrics_without_project_uuid(self):
        response = self.get_sales_funnel_metrics({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_sales_funnel_metrics_without_permission(self):
        response = self.get_sales_funnel_metrics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_sales_funnel_metrics_without_required_params(self):
        response = self.get_sales_funnel_metrics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["widget_uuid"][0].code, "required")
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_sales_funnel_data"
    )
    def test_get_sales_funnel_metrics(self, mock_get_sales_funnel_data):
        mock_get_sales_funnel_data.return_value = SalesFunnelMetrics(
            leads_count=100,
            total_orders_count=100,
            total_orders_value=100,
            currency_code="BRL",
        )

        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.sales_funnel",
            type="sales_funnel",
            position=[1, 2],
            config={},
        )

        response = self.get_sales_funnel_metrics(
            {
                "project_uuid": self.project.uuid,
                "widget_uuid": widget.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_available_widgets_without_project_uuid(self):
        response = self.get_available_widgets({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_get_available_widgets_without_permission(self):
        response = self.get_available_widgets({"project_uuid": self.project.uuid})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_available_widgets"
    )
    @with_project_auth
    def test_get_available_widgets(self, mock_get_available_widgets):
        mock_get_available_widgets.return_value = AvailableWidgetsList(
            available_widgets=[AvailableWidgets.SALES_FUNNEL]
        )
        response = self.get_available_widgets({"project_uuid": self.project.uuid})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["available_widgets"], [AvailableWidgets.SALES_FUNNEL]
        )

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_available_widgets"
    )
    @with_project_auth
    def test_get_available_widgets_with_native_type(self, mock_get_available_widgets):
        mock_get_available_widgets.return_value = AvailableWidgetsList(
            available_widgets=[AvailableWidgets.SALES_FUNNEL]
        )
        response = self.get_available_widgets(
            {"project_uuid": self.project.uuid, "type": AvailableWidgetsListType.NATIVE}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["available_widgets"], [AvailableWidgets.SALES_FUNNEL]
        )

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_available_widgets"
    )
    @with_project_auth
    def test_get_available_widgets_with_custom_type(self, mock_get_available_widgets):
        mock_get_available_widgets.return_value = AvailableWidgetsList(
            available_widgets=[]
        )
        response = self.get_available_widgets(
            {"project_uuid": self.project.uuid, "type": AvailableWidgetsListType.CUSTOM}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["available_widgets"], [])

    def test_cannot_get_crosstab_metrics_without_widget_uuid(self):
        response = self.get_crosstab_metrics({})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_get_crosstab_metrics_without_valid_widget_uuid(self):
        response = self.get_crosstab_metrics({"widget_uuid": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_get_crosstab_metrics_without_widget_permission(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.crosstab",
            type="conversations.crosstab",
            position=[1, 2],
            config={
                "source_a": {
                    "key": "test_key",
                },
                "source_b": {
                    "key": "test_key",
                },
            },
        )

        response = self.get_crosstab_metrics({"widget_uuid": widget.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_crosstab_data"
    )
    @with_project_auth
    def test_get_crosstab_metrics(self, mock_get_crosstab_data):
        mock_get_crosstab_data.return_value = [
            CrosstabItemData(
                title="Test Item",
                total=100,
                subitems=[
                    CrosstabSubItemData(title="Test Subitem", count=15, percentage=30),
                ],
            ),
        ]
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.crosstab",
            type="conversations.crosstab",
            position=[1, 2],
            config={
                "source_a": {
                    "key": "test_key",
                },
                "source_b": {
                    "key": "test_key",
                },
            },
        )

        response = self.get_crosstab_metrics(
            {
                "widget_uuid": widget.uuid,
                "start_date": "2025-01-24",
                "end_date": "2025-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_rows"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Test Item")
        self.assertEqual(response.data["results"][0]["total"], 100)
        self.assertEqual(
            response.data["results"][0]["events"],
            {"Test Subitem": {"value": 30, "full_value": 15}},
        )

    def test_get_available_widgets_without_project_uuid(self):
        response = self.get_available_widgets({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_get_available_widgets_without_permission(self):
        response = self.get_available_widgets({"project_uuid": self.project.uuid})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_available_widgets"
    )
    @with_project_auth
    def test_get_available_widgets(self, mock_get_available_widgets):
        mock_get_available_widgets.return_value = AvailableWidgetsList(
            available_widgets=[AvailableWidgets.SALES_FUNNEL]
        )
        response = self.get_available_widgets({"project_uuid": self.project.uuid})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["available_widgets"], [AvailableWidgets.SALES_FUNNEL]
        )

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_available_widgets"
    )
    @with_project_auth
    def test_get_available_widgets_with_native_type(self, mock_get_available_widgets):
        mock_get_available_widgets.return_value = AvailableWidgetsList(
            available_widgets=[AvailableWidgets.SALES_FUNNEL]
        )
        response = self.get_available_widgets(
            {"project_uuid": self.project.uuid, "type": AvailableWidgetsListType.NATIVE}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["available_widgets"], [AvailableWidgets.SALES_FUNNEL]
        )

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_available_widgets"
    )
    @with_project_auth
    def test_get_available_widgets_with_custom_type(self, mock_get_available_widgets):
        mock_get_available_widgets.return_value = AvailableWidgetsList(
            available_widgets=[]
        )
        response = self.get_available_widgets(
            {"project_uuid": self.project.uuid, "type": AvailableWidgetsListType.CUSTOM}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["available_widgets"], [])

    @with_project_auth
    def test_cannot_get_absolute_numbers_without_widget_uuid(self):
        response = self.get_absolute_numbers({})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_absolute_numbers_without_valid_widget_uuid(self):
        response = self.get_absolute_numbers({"widget_uuid": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_get_absolute_numbers_without_widget_permission(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers.child",
            type="conversations.absolute_numbers.child",
            position=[1, 2],
            config={
                "operation": "TOTAL",
                "key": "test_key",
                "datalake_config": {
                    "agent_uuid": str(uuid.uuid4()),
                },
            },
        )

        response = self.get_absolute_numbers({"widget_uuid": widget.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_absolute_numbers_without_required_params(self):
        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers.child",
            type="conversations.absolute_numbers.child",
            position=[1, 2],
            config={
                "operation": "TOTAL",
                "key": "test_key",
                "agent_uuid": str(uuid.uuid4()),
            },
        )

        response = self.get_absolute_numbers({"widget_uuid": widget.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_absolute_numbers"
    )
    @with_project_auth
    def test_get_absolute_numbers(self, mock_get_absolute_numbers):
        mock_get_absolute_numbers.return_value = {
            "value": 150,
        }

        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers.child",
            type="conversations.absolute_numbers.child",
            position=[1, 2],
            config={
                "operation": "TOTAL",
                "key": "test_key",
                "agent_uuid": str(uuid.uuid4()),
            },
        )

        response = self.get_absolute_numbers(
            {
                "widget_uuid": widget.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["value"], 150)

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_absolute_numbers"
    )
    @with_project_auth
    def test_get_absolute_numbers_with_child_widget(self, mock_get_absolute_numbers):
        mock_get_absolute_numbers.return_value = {
            "value": 150,
        }

        parent_widget = Widget.objects.create(
            name="Test Parent Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers.parent",
            type="conversations.absolute_numbers.parent",
            position=[1, 2],
            config={},
        )

        widget = Widget.objects.create(
            name="Test Widget",
            parent=parent_widget,
            source="conversations.absolute_numbers.child",
            type="conversations.absolute_numbers.child",
            position=[1, 2],
            config={
                "operation": "TOTAL",
                "key": "test_key",
                "agent_uuid": str(uuid.uuid4()),
            },
        )

        response = self.get_absolute_numbers(
            {
                "widget_uuid": widget.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["value"], 150)

    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_absolute_numbers"
    )
    @with_project_auth
    def test_get_absolute_numbers_returns_500_on_service_error(
        self, mock_get_absolute_numbers
    ):
        mock_get_absolute_numbers.side_effect = RuntimeError("Service error")

        widget = Widget.objects.create(
            name="Test Widget",
            dashboard=self.dashboard,
            source="conversations.absolute_numbers.child",
            type="conversations.absolute_numbers.child",
            position=[1, 2],
            config={
                "operation": "TOTAL",
                "key": "test_key",
                "agent_uuid": str(uuid.uuid4()),
            },
        )

        response = self.get_absolute_numbers(
            {
                "widget_uuid": widget.uuid,
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = json.loads(response.content)
        self.assertIn("code", data)
        self.assertEqual(data["code"], "INTERNAL_ERROR")

    def test_cannot_get_agent_invocation_without_project_uuid(self):
        response = self.get_agent_invocation({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_agent_invocation_without_permission(self):
        response = self.get_agent_invocation({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_agent_invocation_without_required_params(self):
        response = self.get_agent_invocation({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_agent_invocations"
    )
    def test_get_agent_invocation(self, mock_get_agent_invocations):
        agent_uuid = str(uuid.uuid4())
        mock_get_agent_invocations.return_value = AgentInvocationMetrics(
            invocations=[
                AgentInvocationItem(
                    label="invocation_1",
                    agent=AgentInvocationAgent(uuid=agent_uuid),
                    value=100.0,
                    full_value=10,
                ),
            ],
            total=1,
        )

        response = self.get_agent_invocation(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["label"], "invocation_1")
        self.assertEqual(response.data["results"][0]["agent"]["uuid"], agent_uuid)
        self.assertEqual(response.data["results"][0]["value"], 100.0)
        self.assertEqual(response.data["results"][0]["full_value"], 10)

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_agent_invocations"
    )
    def test_get_agent_invocation_with_null_agent(self, mock_get_agent_invocations):
        mock_get_agent_invocations.return_value = AgentInvocationMetrics(
            invocations=[
                AgentInvocationItem(
                    label="invocation_1",
                    agent=None,
                    value=100.0,
                    full_value=10,
                ),
            ],
            total=1,
        )

        response = self.get_agent_invocation(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["label"], "invocation_1")
        self.assertIsNone(response.data["results"][0]["agent"])
        self.assertEqual(response.data["results"][0]["value"], 100.0)
        self.assertEqual(response.data["results"][0]["full_value"], 10)

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_agent_invocations"
    )
    def test_get_agent_invocation_empty(self, mock_get_agent_invocations):
        mock_get_agent_invocations.return_value = AgentInvocationMetrics(
            invocations=[],
            total=0,
        )

        response = self.get_agent_invocation(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 0)
        self.assertEqual(len(response.data["results"]), 0)

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_agent_invocations"
    )
    def test_get_agent_invocation_returns_500_on_service_error(
        self, mock_get_agent_invocations
    ):
        mock_get_agent_invocations.side_effect = RuntimeError("Service error")

        response = self.get_agent_invocation(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = json.loads(response.content)
        self.assertIn("code", data)
        self.assertEqual(data["code"], "INTERNAL_ERROR")
        self.assertIn("event_id", data)

    def test_cannot_get_tool_result_without_project_uuid(self):
        response = self.get_tool_result({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_tool_result_without_permission(self):
        response = self.get_tool_result({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_tool_result_without_required_params(self):
        response = self.get_tool_result({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_tool_results"
    )
    def test_get_tool_result(self, mock_get_tool_results):
        agent_uuid = str(uuid.uuid4())
        mock_get_tool_results.return_value = ToolResultMetrics(
            tool_results=[
                ToolResultItem(
                    label="tool_result_1",
                    agent=ToolResultAgent(uuid=agent_uuid),
                    value=100.0,
                    full_value=10,
                ),
            ],
            total=1,
        )
        response = self.get_tool_result(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(len(response.data["results"]), 1)

        self.assertEqual(response.data["results"][0]["label"], "tool_result_1")

        self.assertEqual(response.data["results"][0]["agent"]["uuid"], agent_uuid)
        self.assertEqual(response.data["results"][0]["value"], 100.0)
        self.assertEqual(response.data["results"][0]["full_value"], 10)

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_tool_results"
    )
    def test_get_tool_result_with_null_agent(self, mock_get_tool_results):
        mock_get_tool_results.return_value = ToolResultMetrics(
            tool_results=[
                ToolResultItem(
                    label="tool_result_1",
                    agent=None,
                    value=100.0,
                    full_value=10,
                ),
            ],
            total=1,
            {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["label"], "tool_result_1")

        self.assertIsNone(response.data["results"][0]["agent"])
        self.assertEqual(response.data["results"][0]["value"], 100.0)
        self.assertEqual(response.data["results"][0]["full_value"], 10)

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_tool_results"
    )
    def test_get_tool_result_empty(self, mock_get_tool_results):
        mock_get_tool_results.return_value = ToolResultMetrics(
            tool_results=[],
            total=0,
        )

        response = self.get_tool_result(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 0)
        self.assertEqual(len(response.data["results"]), 0)

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_tool_results"
    )
    def test_get_tool_result_returns_500_on_service_error(self, mock_get_tool_results):
        mock_get_tool_results.side_effect = RuntimeError("Service error")

        response = self.get_tool_result(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = json.loads(response.content)
        self.assertIn("code", data)
        self.assertEqual(data["code"], "INTERNAL_ERROR")
        self.assertIn("event_id", data)

    def test_cannot_get_contacts_metrics_without_project_uuid(self):
        response = self.get_contacts_metrics({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    def test_cannot_get_contacts_metrics_without_permission(self):
        response = self.get_contacts_metrics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_project_auth
    def test_cannot_get_contacts_metrics_without_required_params(self):
        response = self.get_contacts_metrics({"project_uuid": self.project.uuid})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_contacts_metrics"
    )
    def test_get_contacts_metrics(self, mock_get_contacts_metrics):
        mock_get_contacts_metrics.return_value = ContactMetricsData(
            unique=UniqueContactsMetricsData(value=80),
            returning=ReturningContactsMetricsData(value=28, percentage=35.0),
            avg_conversations_per_contact=AvgConversationsPerContactMetricsData(
                value=1.25
            ),
        )

        response = self.get_contacts_metrics(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unique"]["value"], 80)
        self.assertEqual(response.data["returning"]["value"], 28)
        self.assertEqual(response.data["returning"]["percentage"], 35.0)
        self.assertEqual(response.data["avg_conversations_per_contact"]["value"], 1.25)

    @with_project_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_contacts_metrics"
    )
    def test_get_contacts_metrics_returns_500_on_service_error(
        self, mock_get_contacts_metrics
    ):
        mock_get_contacts_metrics.side_effect = RuntimeError("Service error")

        response = self.get_contacts_metrics(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = json.loads(response.content)
        self.assertIn("code", data)
        self.assertEqual(data["code"], "INTERNAL_ERROR")
        self.assertIn("event_id", data)


class BaseTestInternalConversationsMetricsViewSet(APITestCase):
    def get_project_ai_csat_metrics(self, query_params: dict) -> Response:
        url = reverse("internal_api:internal-ai-csat-metrics-project-ai-csat-metrics")
        self.assertEqual(
            url, "/v1/internal/metrics/conversations/project-ai-csat-metrics/"
        )

        return self.client.get(url, query_params, format="json")


class TestInternalConversationsMetricsViewSetAsAnonymousUser(
    BaseTestInternalConversationsMetricsViewSet
):
    def test_cannot_get_project_ai_csat_metrics_when_unauthenticated(self):
        response = self.get_project_ai_csat_metrics({})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestInternalConversationsMetricsViewSetWithInternalAuthentication(
    BaseTestInternalConversationsMetricsViewSet
):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.user = User.objects.create(email="internal@vtex.com")
        self.client.force_authenticate(self.user)

    def test_cannot_get_project_ai_csat_metrics_without_permission(self):
        response = self.get_project_ai_csat_metrics({})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_internal_auth
    def test_cannot_get_project_ai_csat_metrics_without_required_fields(self):
        response = self.get_project_ai_csat_metrics({})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["start_date"][0].code, "required")
        self.assertEqual(response.data["end_date"][0].code, "required")
        self.assertEqual(response.data["project_uuid"][0].code, "required")

    @with_internal_auth
    @patch(
        "insights.metrics.conversations.services.ConversationsMetricsService.get_csat_metrics"
    )
    def test_get_project_ai_csat_metrics(self, mock_get_csat_metrics):
        mock_get_csat_metrics.return_value = {
            "results": [
                {
                    "label": "1",
                    "value": 100,
                    "full_value": 100,
                }
            ],
        }

        Widget.objects.create(
            name="Test Widget",
            dashboard=Dashboard.objects.create(
                project=self.project, name="Test Dashboard"
            ),
            source="conversations.csat",
            type="conversations.csat",
            position=[1, 2],
            config={"datalake_config": {"agent_uuid": str(uuid.uuid4())}},
        )

        response = self.get_project_ai_csat_metrics(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["label"], "1")
        self.assertEqual(response.data["results"][0]["value"], 100)
        self.assertEqual(response.data["results"][0]["full_value"], 100)


class TestConversationsMetricsViewSetAsInternalUser(
    BaseTestConversationsMetricsViewSet
):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.user = User.objects.create(email="internal@vtex.com")

        self.client.force_authenticate(self.user)

    def test_cannot_get_totals_without_internal_auth(self):
        response = self.get_totals(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @with_internal_auth
    def test_can_get_totals_with_internal_auth(self):
        response = self.get_totals(
            {
                "project_uuid": self.project.uuid,
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
