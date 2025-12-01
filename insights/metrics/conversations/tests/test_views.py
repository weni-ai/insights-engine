import uuid
from unittest.mock import MagicMock, patch
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APITestCase

from insights.authentication.authentication import User
from insights.authentication.tests.decorators import with_project_auth
from insights.dashboards.models import Dashboard
from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
    CrosstabItemData,
    CrosstabSubItemData,
    SalesFunnelMetrics,
)
from insights.metrics.conversations.enums import (
    ConversationType,
    CsatMetricsType,
    NpsMetricsType,
)
from insights.metrics.conversations.integrations.datalake.services import (
    BaseConversationsMetricsService,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetric,
    ConversationsTotalsMetrics,
)
from insights.metrics.conversations.views import ConversationsMetricsViewSet
from insights.projects.models import Project
from insights.sources.flowruns.tests.mock_query_executor import (
    MockFlowRunsQueryExecutor,
)
from insights.sources.integrations.tests.mock_clients import MockNexusClient
from insights.widgets.models import Widget
from insights.dashboards.models import Dashboard


class BaseTestConversationsMetricsViewSet(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.original_service = ConversationsMetricsViewSet.service
        ConversationsMetricsViewSet.service = ConversationsMetricsService(
            datalake_service=MagicMock(spec=BaseConversationsMetricsService),
            nexus_client=MockNexusClient(),
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
                    CrosstabSubItemData(title="Test Subitem", count=10, percentage=10),
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
            response.data["results"][0]["events"], {"Test Subitem": {"value": 10}}
        )
