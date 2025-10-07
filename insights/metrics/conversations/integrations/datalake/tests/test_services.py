from datetime import datetime, timedelta
import json
import uuid

from django.conf import settings
from unittest.mock import call, patch
from django.test import TestCase

from insights.metrics.conversations.dataclass import (
    ConversationsTotalsMetrics,
    SubtopicTopicRelation,
)
from insights.metrics.conversations.enums import ConversationType
from insights.metrics.conversations.integrations.datalake.dataclass import (
    SalesFunnelData,
)
from insights.sources.dl_events.tests.mock_client import (
    ClassificationMockDataLakeEventsClient,
)
from insights.metrics.conversations.integrations.datalake.services import (
    DatalakeConversationsMetricsService,
)
from insights.sources.tests.mock import MockCacheClient


class DatalakeConversationsMetricsServiceTestCase(TestCase):
    def setUp(self):
        self.service = DatalakeConversationsMetricsService(
            events_client=ClassificationMockDataLakeEventsClient(),
            cache_client=MockCacheClient(),
            cache_results=True,
            cache_ttl=300,
        )

    def test_get_conversations_totals(self):
        results = self.service.get_conversations_totals(
            project_uuid=uuid.uuid4(),
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
        )

        self.assertIsInstance(results, ConversationsTotalsMetrics)

    def test_get_unclassified_label(self):
        label = self.service._get_unclassified_label("en")
        self.assertEqual(label, "Unclassified")

        label = self.service._get_unclassified_label("pt-br")
        self.assertEqual(label, "Não classificadas")

        label = self.service._get_unclassified_label("es")
        self.assertEqual(label, "No clasificadas")

    def test_get_csat_metrics(self):
        project_uuid = uuid.uuid4()
        agent_uuid = str(uuid.uuid4())
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        results = self.service.get_csat_metrics(
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        self.assertIsInstance(results, dict)
        self.assertIn("1", results)
        self.assertIn("2", results)
        self.assertIn("3", results)
        self.assertIn("4", results)
        self.assertIn("5", results)

    def test_get_csat_metrics_with_cache(self):
        project_uuid = uuid.uuid4()
        agent_uuid = str(uuid.uuid4())
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        # First call should cache the results
        results1 = self.service.get_csat_metrics(
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        # Second call should use cache
        results2 = self.service.get_csat_metrics(
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        self.assertEqual(results1, results2)

    def test_get_csat_metrics_with_exception(self):
        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:
            mock_get_events.side_effect = Exception("Test exception")

            with self.assertRaises(Exception):
                self.service.get_csat_metrics(
                    project_uuid=uuid.uuid4(),
                    agent_uuid=str(uuid.uuid4()),
                    start_date=datetime.now() - timedelta(days=1),
                    end_date=datetime.now(),
                )

    def test_get_csat_metrics_with_invalid_payload_values(self):
        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:
            mock_get_events.return_value = [
                {"payload_value": "invalid", "count": 5},
                {"payload_value": None, "count": 3},
                {"payload_value": 6, "count": 2},  # Invalid CSAT score
                {"payload_value": "1", "count": 10},
            ]

            results = self.service.get_csat_metrics(
                project_uuid=uuid.uuid4(),
                agent_uuid=str(uuid.uuid4()),
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
            )

            # Only valid CSAT scores should be included
            self.assertEqual(results["1"], 10)
            self.assertEqual(results["2"], 0)
            self.assertEqual(results["3"], 0)
            self.assertEqual(results["4"], 0)
            self.assertEqual(results["5"], 0)

    def test_get_nps_metrics(self):
        project_uuid = uuid.uuid4()
        agent_uuid = str(uuid.uuid4())
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        results = self.service.get_nps_metrics(
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        self.assertIsInstance(results, dict)
        # NPS scores range from 0-10
        for i in range(11):
            self.assertIn(str(i), results)

    def test_get_nps_metrics_with_cache(self):
        project_uuid = uuid.uuid4()
        agent_uuid = str(uuid.uuid4())
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        # First call should cache the results
        results1 = self.service.get_nps_metrics(
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        # Second call should use cache
        results2 = self.service.get_nps_metrics(
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        self.assertEqual(results1, results2)

    def test_get_nps_metrics_with_exception(self):
        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:
            mock_get_events.side_effect = Exception("Test exception")

            with self.assertRaises(Exception):
                self.service.get_nps_metrics(
                    project_uuid=uuid.uuid4(),
                    agent_uuid=str(uuid.uuid4()),
                    start_date=datetime.now() - timedelta(days=1),
                    end_date=datetime.now(),
                )

    def test_get_nps_metrics_with_invalid_payload_values(self):
        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:
            mock_get_events.return_value = [
                {"payload_value": "invalid", "count": 5},
                {"payload_value": None, "count": 3},
                {"payload_value": 11, "count": 2},  # Invalid NPS score
                {"payload_value": "5", "count": 10},
            ]

            results = self.service.get_nps_metrics(
                project_uuid=uuid.uuid4(),
                agent_uuid=str(uuid.uuid4()),
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
            )

            self.assertEqual(results["5"], 10)
            for i in range(11):
                if str(i) != "5":
                    self.assertEqual(results[str(i)], 0)

    def test_get_topics_distribution_ai(self):
        project_uuid = uuid.uuid4()
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        subtopics = [
            SubtopicTopicRelation(
                subtopic_uuid=str(uuid.uuid4()),
                subtopic_name="Test Subtopic",
                topic_uuid=str(uuid.uuid4()),
                topic_name="Test Topic",
            )
        ]

        results = self.service.get_topics_distribution(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
            conversation_type=ConversationType.AI,
            subtopics=subtopics,
            output_language="en",
        )

        self.assertIsInstance(results, dict)
        self.assertIn("OTHER", results)

    def test_get_topics_distribution_human(self):
        project_uuid = uuid.uuid4()
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        subtopics = [
            SubtopicTopicRelation(
                subtopic_uuid=str(uuid.uuid4()),
                subtopic_name="Test Subtopic",
                topic_uuid=str(uuid.uuid4()),
                topic_name="Test Topic",
            )
        ]

        results = self.service.get_topics_distribution(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
            conversation_type=ConversationType.HUMAN,
            subtopics=subtopics,
            output_language="en",
        )

        self.assertIsInstance(results, dict)
        self.assertIn("OTHER", results)

    def test_get_topics_distribution_with_cache(self):
        project_uuid = uuid.uuid4()
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        subtopics = [
            SubtopicTopicRelation(
                subtopic_uuid=str(uuid.uuid4()),
                subtopic_name="Test Subtopic",
                topic_uuid=str(uuid.uuid4()),
                topic_name="Test Topic",
            )
        ]

        results1 = self.service.get_topics_distribution(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
            conversation_type=ConversationType.AI,
            subtopics=subtopics,
            output_language="en",
        )

        results2 = self.service.get_topics_distribution(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
            conversation_type=ConversationType.AI,
            subtopics=subtopics,
            output_language="en",
        )

        self.assertEqual(results1, results2)

    def test_get_topics_distribution_with_exception(self):
        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:
            mock_get_events.side_effect = Exception("Test exception")

            with self.assertRaises(Exception):
                self.service.get_topics_distribution(
                    project_uuid=uuid.uuid4(),
                    start_date=datetime.now() - timedelta(days=1),
                    end_date=datetime.now(),
                    conversation_type=ConversationType.AI,
                    subtopics=[],
                    output_language="en",
                )

    def test_get_topics_distribution_with_empty_events(self):
        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:
            mock_get_events.return_value = [{}]

            results = self.service.get_topics_distribution(
                project_uuid=uuid.uuid4(),
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                conversation_type=ConversationType.AI,
                subtopics=[],
                output_language="en",
            )

            # Should return empty results when no events
            self.assertEqual(results, {})

    def test_get_topics_distribution_with_subtopics_events_empty(self):
        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:

            def side_effect(**kwargs):
                if kwargs.get("group_by") == "topic_uuid":
                    return [{"group_value": "topic1", "count": 5}]
                else:  # subtopics
                    return [{}]

            mock_get_events.side_effect = side_effect

            results = self.service.get_topics_distribution(
                project_uuid=uuid.uuid4(),
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                conversation_type=ConversationType.AI,
                subtopics=[],
                output_language="en",
            )

            self.assertIsInstance(results, dict)

    def test_get_topics_distribution_with_valid_events(self):
        topic_uuid = str(uuid.uuid4())
        subtopic_uuid = str(uuid.uuid4())

        subtopics = [
            SubtopicTopicRelation(
                subtopic_uuid=subtopic_uuid,
                subtopic_name="Test Subtopic",
                topic_uuid=topic_uuid,
                topic_name="Test Topic",
            )
        ]

        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:

            def side_effect(**kwargs):
                if kwargs.get("group_by") == "topic_uuid":
                    return [
                        {
                            "group_value": topic_uuid,
                            "count": 5,
                            "topic_name": "Test Topic",
                        }
                    ]
                else:  # subtopics
                    return [{"group_value": subtopic_uuid, "count": 3}]

            mock_get_events.side_effect = side_effect

            results = self.service.get_topics_distribution(
                project_uuid=uuid.uuid4(),
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                conversation_type=ConversationType.AI,
                subtopics=subtopics,
                output_language="en",
            )

            self.assertIsInstance(results, dict)
            self.assertIn(topic_uuid, results)

    def test_get_topics_distribution_with_unknown_topic(self):
        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:

            def side_effect(**kwargs):
                if kwargs.get("group_by") == "topic_uuid":
                    return [{"group_value": "unknown_topic", "count": 5}]
                else:  # subtopics
                    return [{"group_value": "unknown_subtopic", "count": 3}]

            mock_get_events.side_effect = side_effect

            results = self.service.get_topics_distribution(
                project_uuid=uuid.uuid4(),
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                conversation_type=ConversationType.AI,
                subtopics=[],
                output_language="en",
            )

            self.assertIn("OTHER", results)
            self.assertEqual(results["OTHER"]["count"], 8)  # 5 + 3

    def test_get_topics_distribution_with_unknown_subtopic(self):
        """Test topics distribution with unknown subtopic UUID"""
        topic_uuid = str(uuid.uuid4())

        subtopics = [
            SubtopicTopicRelation(
                subtopic_uuid=str(uuid.uuid4()),
                subtopic_name="Test Subtopic",
                topic_uuid=topic_uuid,
                topic_name="Test Topic",
            )
        ]

        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:

            def side_effect(**kwargs):
                if kwargs.get("group_by") == "topic_uuid":
                    return [
                        {
                            "group_value": topic_uuid,
                            "count": 5,
                            "topic_name": "Test Topic",
                        }
                    ]
                else:  # subtopics
                    return [{"group_value": "unknown_subtopic", "count": 3}]

            mock_get_events.side_effect = side_effect

            results = self.service.get_topics_distribution(
                project_uuid=uuid.uuid4(),
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                conversation_type=ConversationType.AI,
                subtopics=subtopics,
                output_language="en",
            )

            self.assertIn("OTHER", results)
            self.assertEqual(results["OTHER"]["count"], 3)

    def test_get_conversations_totals_with_cache(self):
        project_uuid = uuid.uuid4()
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        results1 = self.service.get_conversations_totals(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        results2 = self.service.get_conversations_totals(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        self.assertEqual(results1, results2)

    def test_get_conversations_totals_with_exception(self):
        with patch.object(
            self.service.events_client, "get_events_count"
        ) as mock_get_events:
            mock_get_events.side_effect = Exception("Test exception")

            with self.assertRaises(Exception):
                self.service.get_conversations_totals(
                    project_uuid=uuid.uuid4(),
                    start_date=datetime.now() - timedelta(days=1),
                    end_date=datetime.now(),
                )

    def test_get_conversations_totals_with_zero_total(self):
        with patch.object(
            self.service.events_client, "get_events_count"
        ) as mock_get_events:
            mock_get_events.return_value = [{"count": 0}]

            results = self.service.get_conversations_totals(
                project_uuid=uuid.uuid4(),
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
            )

            # Should handle zero total conversations
            self.assertEqual(results.total_conversations.value, 0)
            self.assertEqual(results.resolved.percentage, 0)
            self.assertEqual(results.unresolved.percentage, 0)
            self.assertEqual(results.transferred_to_human.percentage, 0)

    def test_get_generic_metrics_by_key(self):
        project_uuid = uuid.uuid4()
        agent_uuid = str(uuid.uuid4())
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        key = "test_key"

        results = self.service.get_generic_metrics_by_key(
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
            key=key,
        )

        self.assertIsInstance(results, dict)

    def test_get_generic_metrics_by_key_with_cache(self):
        project_uuid = uuid.uuid4()
        agent_uuid = str(uuid.uuid4())
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()
        key = "test_key"

        results1 = self.service.get_generic_metrics_by_key(
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
            key=key,
        )

        results2 = self.service.get_generic_metrics_by_key(
            project_uuid=project_uuid,
            agent_uuid=agent_uuid,
            start_date=start_date,
            end_date=end_date,
            key=key,
        )

        self.assertEqual(results1, results2)

    def test_get_generic_metrics_by_key_with_exception(self):
        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:
            mock_get_events.side_effect = Exception("Test exception")

            with self.assertRaises(Exception):
                self.service.get_generic_metrics_by_key(
                    project_uuid=uuid.uuid4(),
                    agent_uuid=str(uuid.uuid4()),
                    start_date=datetime.now() - timedelta(days=1),
                    end_date=datetime.now(),
                    key="test_key",
                )

    def test_get_generic_metrics_by_key_with_invalid_payload_values(self):
        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:
            mock_get_events.return_value = [
                {"payload_value": "valid_value", "count": 5},
                {"payload_value": None, "count": 3},
                {"payload_value": 123, "count": 2},
            ]

            results = self.service.get_generic_metrics_by_key(
                project_uuid=uuid.uuid4(),
                agent_uuid=str(uuid.uuid4()),
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                key="test_key",
            )

            self.assertIn("valid_value", results)
            self.assertIn("123", results)
            self.assertEqual(results["valid_value"], 5)
            self.assertEqual(results["123"], 2)

    def test_get_generic_metrics_by_key_with_duplicate_values(self):
        with patch.object(
            self.service.events_client, "get_events_count_by_group"
        ) as mock_get_events:
            mock_get_events.return_value = [
                {"payload_value": "same_value", "count": 5},
                {"payload_value": "same_value", "count": 3},
            ]

            results = self.service.get_generic_metrics_by_key(
                project_uuid=uuid.uuid4(),
                agent_uuid=str(uuid.uuid4()),
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                key="test_key",
            )

            self.assertEqual(results["same_value"], 8)

    def test_cache_key_generation(self):
        cache_key1 = self.service._get_cache_key(
            data_type="test",
            project_uuid=uuid.uuid4(),
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 2),
        )

        cache_key2 = self.service._get_cache_key(
            data_type="test",
            project_uuid=str(uuid.uuid4()),
            start_date="2025-01-01",
            end_date="2025-01-02",
        )

        self.assertIsInstance(cache_key1, str)
        self.assertIsInstance(cache_key2, str)
        self.assertIn("test_", cache_key1)
        self.assertIn("test_", cache_key2)

    def test_save_results_to_cache_with_exception(self):
        with patch.object(self.service.cache_client, "set") as mock_set:
            mock_set.side_effect = Exception("Cache error")

            # Should not raise exception, just log warning
            self.service._save_results_to_cache("test_key", {"test": "data"})

    def test_get_cached_results_with_exception(self):
        with patch.object(self.service.cache_client, "get") as mock_get:
            mock_get.side_effect = TypeError("Cache error")

            # Should return None on exception and not raise
            result = self.service._get_cached_results("test_key")
            self.assertIsNone(result)

    def test_get_cached_results_with_bytes_data(self):
        with patch.object(self.service.cache_client, "get") as mock_get:
            mock_get.return_value = b'{"test": "data"}'

            result = self.service._get_cached_results("test_key")
            self.assertEqual(result, {"test": "data"})

    def test_get_cached_results_with_string_data(self):
        with patch.object(self.service.cache_client, "get") as mock_get:
            mock_get.return_value = '{"test": "data"}'

            result = self.service._get_cached_results("test_key")
            self.assertEqual(result, {"test": "data"})

    def test_get_cached_results_with_dict_data(self):
        with patch.object(self.service.cache_client, "get") as mock_get:
            mock_get.return_value = {"test": "data"}

            result = self.service._get_cached_results("test_key")
            self.assertEqual(result, {"test": "data"})

    def test_get_cached_results_with_none_data(self):
        with patch.object(self.service.cache_client, "get") as mock_get:
            mock_get.return_value = None

            result = self.service._get_cached_results("test_key")
            self.assertIsNone(result)

    def test_get_cached_results_with_invalid_json(self):
        with patch.object(self.service.cache_client, "get") as mock_get:
            mock_get.return_value = "invalid json"

            result = self.service._get_cached_results("test_key")
            self.assertIsNone(result)

    def test_csat_metrics_with_cached_string_data(self):
        project_uuid = uuid.uuid4()
        agent_uuid = str(uuid.uuid4())
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        with patch.object(self.service, "_get_cached_results") as mock_get_cached:
            mock_get_cached.return_value = '{"1": 5, "2": 3}'

            results = self.service.get_csat_metrics(
                project_uuid=project_uuid,
                agent_uuid=agent_uuid,
                start_date=start_date,
                end_date=end_date,
            )

            self.assertEqual(results, {"1": 5, "2": 3})

    def test_nps_metrics_with_cached_string_data(self):
        project_uuid = uuid.uuid4()
        agent_uuid = str(uuid.uuid4())
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        # Mock cache to return string data
        with patch.object(self.service, "_get_cached_results") as mock_get_cached:
            mock_get_cached.return_value = '{"5": 10, "6": 5}'

            results = self.service.get_nps_metrics(
                project_uuid=project_uuid,
                agent_uuid=agent_uuid,
                start_date=start_date,
                end_date=end_date,
            )

            self.assertEqual(results, {"5": 10, "6": 5})

    def test_topics_distribution_with_cached_string_data(self):
        project_uuid = uuid.uuid4()
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        # Mock cache to return string data
        with patch.object(self.service, "_get_cached_results") as mock_get_cached:
            mock_get_cached.return_value = '{"OTHER": {"count": 5}}'

            results = self.service.get_topics_distribution(
                project_uuid=project_uuid,
                start_date=start_date,
                end_date=end_date,
                conversation_type=ConversationType.AI,
                subtopics=[],
                output_language="en",
            )

            self.assertEqual(results, {"OTHER": {"count": 5}})

    def test_generic_metrics_with_cached_string_data(self):
        project_uuid = uuid.uuid4()
        agent_uuid = str(uuid.uuid4())
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        # Mock cache to return string data
        with patch.object(self.service, "_get_cached_results") as mock_get_cached:
            mock_get_cached.return_value = '{"value1": 5, "value2": 3}'

            results = self.service.get_generic_metrics_by_key(
                project_uuid=project_uuid,
                agent_uuid=agent_uuid,
                start_date=start_date,
                end_date=end_date,
                key="test_key",
            )

            self.assertEqual(results, {"value1": 5, "value2": 3})

    def test_conversations_totals_cache_retrieval_exception(self):
        """Test conversations totals cache retrieval with exception"""
        project_uuid = uuid.uuid4()
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        with patch.object(self.service, "_get_cached_results") as mock_get_cached:
            mock_get_cached.side_effect = Exception("Cache error")

            # Should continue with normal flow when cache fails
            results = self.service.get_conversations_totals(
                project_uuid=project_uuid,
                start_date=start_date,
                end_date=end_date,
            )

            self.assertIsInstance(results, ConversationsTotalsMetrics)

    def test_conversations_totals_cache_retrieval_success(self):
        project_uuid = uuid.uuid4()
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        cached_data = {
            "total_conversations": {"value": 100, "percentage": 100},
            "resolved": {"value": 60, "percentage": 60},
            "unresolved": {"value": 40, "percentage": 40},
            "transferred_to_human": {"value": 20, "percentage": 20},
        }

        with patch.object(self.service, "_get_cached_results") as mock_get_cached:
            mock_get_cached.return_value = cached_data

            results = self.service.get_conversations_totals(
                project_uuid=project_uuid,
                start_date=start_date,
                end_date=end_date,
            )

            self.assertEqual(results.total_conversations.value, 100)
            self.assertEqual(results.resolved.value, 60)
            self.assertEqual(results.unresolved.value, 40)
            self.assertEqual(results.transferred_to_human.value, 20)

    @patch(
        "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events"
    )
    @patch(
        "insights.sources.dl_events.tests.mock_client.ClassificationMockDataLakeEventsClient.get_events_count"
    )
    def test_get_sales_funnel_data(
        self, mock_data_lake_events_count_client, mock_data_lake_events_client
    ):
        def get_events(**kwargs):
            if kwargs.get("offset") == 0:
                return [{"metadata": json.dumps({"currency": "BRL", "value": 100})}]

            return []

        mock_data_lake_events_client.side_effect = get_events
        mock_data_lake_events_count_client.return_value = [{"count": 10}]

        project_uuid = uuid.uuid4()
        start_date = datetime.now() - timedelta(days=1)
        end_date = datetime.now()

        results = self.service.get_sales_funnel_data(
            project_uuid=project_uuid,
            start_date=start_date,
            end_date=end_date,
        )

        self.assertIsInstance(results, SalesFunnelData)

        mock_data_lake_events_client.assert_has_calls(
            [
                call(
                    event_name="conversion_purchase",
                    project=project_uuid,
                    date_start=start_date,
                    date_end=end_date,
                    limit=settings.SALES_FUNNEL_EVENTS_PAGE_SIZE,
                    offset=settings.SALES_FUNNEL_EVENTS_PAGE_SIZE * 0,
                ),
                call(
                    event_name="conversion_purchase",
                    project=project_uuid,
                    date_start=start_date,
                    date_end=end_date,
                    limit=settings.SALES_FUNNEL_EVENTS_PAGE_SIZE,
                    offset=settings.SALES_FUNNEL_EVENTS_PAGE_SIZE * 1,
                ),
            ]
        )
        mock_data_lake_events_count_client.assert_called_once_with(
            event_name="conversion_lead",
            project=project_uuid,
            date_start=start_date,
            date_end=end_date,
        )

        self.assertEqual(results.leads_count, 10)
        self.assertEqual(results.total_orders_count, 1)
        self.assertEqual(results.total_orders_value, 10000)  # Converted to cents
        self.assertEqual(results.currency_code, "BRL")
