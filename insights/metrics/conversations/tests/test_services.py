from datetime import datetime, timedelta
from django.test import TestCase

from insights.dashboards.models import Dashboard
from insights.metrics.conversations.enums import CsatMetricsType
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.projects.models import Project
from insights.sources.flowruns.tests.mock_query_executor import (
    MockFlowRunsQueryExecutor,
)
from insights.widgets.models import Widget


class TestConversationsMetricsService(TestCase):

    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
        )
        self.dashboard = Dashboard.objects.create(
            name="Test Dashboard",
            project=self.project,
        )
        self.service = ConversationsMetricsService(
            flowruns_query_executor=MockFlowRunsQueryExecutor
        )

    def test_get_csat_metrics_from_flowruns(self):
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

        self.service.get_csat_metrics(
            project_uuid=self.project.uuid,
            widget=widget,
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            metric_type=CsatMetricsType.HUMAN,
        )
