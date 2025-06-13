from datetime import datetime, timedelta
from unittest.mock import patch
import uuid
from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta

from insights.metrics.conversations.dataclass import (
    ConversationTotalsMetrics,
    QueueMetric,
    RoomsByQueueMetric,
    SubjectMetricData,
    SubjectsMetrics,
)
from insights.metrics.conversations.integrations.chats.db.dataclass import RoomsByQueue
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_METRICS_TOTALS_MOCK_DATA,
    CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA,
)
from insights.projects.models import Project
from insights.metrics.conversations.enums import (
    ConversationsSubjectsType,
    ConversationsTimeseriesUnit,
)
from insights.metrics.conversations.services import ConversationsMetricsService
from insights.metrics.conversations.tests.mock import (
    CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA,
)


class TestConversationsMetricsService(TestCase):
    service = ConversationsMetricsService()

    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.start_date = datetime.now() - timedelta(days=30)
        self.end_date = datetime.now()

    def test_get_totals(self):
        totals = self.service.get_totals(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertIsInstance(totals, ConversationTotalsMetrics)
        self.assertEqual(
            totals.total,
            CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_ai"]
            + CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_human"],
        )
        self.assertEqual(
            totals.by_ai.value, CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_ai"]
        )
        self.assertEqual(
            totals.by_ai.percentage,
            CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_ai"] / totals.total * 100,
        )
        self.assertEqual(
            totals.by_human.value, CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_human"]
        )
        self.assertEqual(
            totals.by_human.percentage,
            CONVERSATIONS_METRICS_TOTALS_MOCK_DATA["by_human"] / totals.total * 100,
        )

    def test_get_timeseries_for_day_unit(self):
        data = self.service.get_timeseries(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            unit=ConversationsTimeseriesUnit.DAY,
        )

        self.assertEqual(data.unit, ConversationsTimeseriesUnit.DAY)
        self.assertEqual(
            data.total,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[ConversationsTimeseriesUnit.DAY][
                "total"
            ],
        )
        self.assertEqual(
            data.by_human,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[ConversationsTimeseriesUnit.DAY][
                "by_human"
            ],
        )

    def test_get_timeseries_for_hour_unit(self):
        data = self.service.get_timeseries(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            unit=ConversationsTimeseriesUnit.HOUR,
        )

        self.assertEqual(data.unit, ConversationsTimeseriesUnit.HOUR)
        self.assertEqual(
            data.total,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.HOUR
            ]["total"],
        )
        self.assertEqual(
            data.by_human,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.HOUR
            ]["by_human"],
        )

    def test_get_timeseries_for_month_unit(self):
        data = self.service.get_timeseries(
            project=self.project,
            start_date=self.start_date,
            end_date=self.end_date,
            unit=ConversationsTimeseriesUnit.MONTH,
        )

        self.assertEqual(data.unit, ConversationsTimeseriesUnit.MONTH)
        self.assertEqual(
            data.total,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.MONTH
            ]["total"],
        )
        self.assertEqual(
            data.by_human,
            CONVERSATIONS_TIMESERIES_METRICS_MOCK_DATA[
                ConversationsTimeseriesUnit.MONTH
            ]["by_human"],
        )

    def test_get_subjects_metrics(self):
        subjects_metrics = self.service.get_subjects_metrics(
            project_uuid=self.project.uuid,
            start_date=self.start_date,
            end_date=self.end_date,
            conversation_type=ConversationsSubjectsType.GENERAL,
        )

        self.assertIsInstance(subjects_metrics, SubjectsMetrics)
        self.assertEqual(subjects_metrics.has_more, False)

        subjects_data = CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA.get("subjects", [])

        self.assertEqual(len(subjects_metrics.subjects), len(subjects_data))

        for i, subject in enumerate(subjects_metrics.subjects):
            self.assertIsInstance(subject, SubjectMetricData)
            subject_data = subjects_data[i]

            self.assertEqual(
                subject.name,
                subject_data.get("name"),
            )
            self.assertEqual(
                subject.percentage,
                subject_data.get("percentage"),
            )

    def test_get_subjects_metrics_with_limit(self):
        subjects_data = CONVERSATIONS_SUBJECTS_METRICS_MOCK_DATA.get("subjects", [])

        subjects_metrics = self.service.get_subjects_metrics(
            project_uuid=self.project.uuid,
            start_date=self.start_date,
            end_date=self.end_date,
            conversation_type=ConversationsSubjectsType.GENERAL,
            limit=len(subjects_data) - 1,
        )

        self.assertIsInstance(subjects_metrics, SubjectsMetrics)
        self.assertEqual(subjects_metrics.has_more, True)

        self.assertEqual(len(subjects_metrics.subjects), len(subjects_data) - 1)

        for i, subject in enumerate(subjects_metrics.subjects):
            self.assertIsInstance(subject, SubjectMetricData)
            subject_data = subjects_data[i]

            self.assertEqual(
                subject.name,
                subject_data.get("name"),
            )
            self.assertEqual(
                subject.percentage,
                subject_data.get("percentage"),
            )

    @patch(
        "insights.metrics.conversations.services.ChatsClient.get_rooms_numbers_by_queue"
    )
    def test_get_rooms_numbers_by_queue(self, get_rooms_numbers_by_queue):
        rooms_by_queue = [
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue",
                rooms_number=10,
            ),
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue 2",
                rooms_number=20,
            ),
        ]
        get_rooms_numbers_by_queue.return_value = rooms_by_queue

        result = self.service.get_rooms_numbers_by_queue(
            project_uuid=uuid.uuid4(),
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now(),
        )

        self.assertEqual(
            result,
            RoomsByQueueMetric(
                queues=[
                    QueueMetric(name="Test Queue", percentage=33.33),
                    QueueMetric(name="Test Queue 2", percentage=66.67),
                ],
                has_more=False,
            ),
        )

    @patch(
        "insights.metrics.conversations.services.ChatsClient.get_rooms_numbers_by_queue"
    )
    def test_get_rooms_numbers_by_queue_with_limit(self, get_rooms_numbers_by_queue):
        rooms_by_queue = [
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue",
                rooms_number=10,
            ),
            RoomsByQueue(
                queue_uuid=uuid.uuid4(),
                queue_name="Test Queue 2",
                rooms_number=20,
            ),
        ]
        get_rooms_numbers_by_queue.return_value = rooms_by_queue

        result = self.service.get_rooms_numbers_by_queue(
            project_uuid=uuid.uuid4(),
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now(),
            limit=1,
        )

        self.assertEqual(
            result,
            RoomsByQueueMetric(
                queues=[
                    QueueMetric(name="Test Queue", percentage=33.33),
                ],
                has_more=True,
            ),
        )
