from datetime import date, datetime
from uuid import uuid4
from unittest.mock import MagicMock, patch

from django.test import TestCase

from insights.human_support.services import HumanSupportDashboardService
from insights.projects.models import Project


class TestHumanSupportDashboardService(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Test Project",
            timezone="America/Sao_Paulo",
        )
        self.service = HumanSupportDashboardService(project=self.project)

    def test_init_stores_project_and_clients(self):
        self.assertEqual(self.service.project, self.project)
        self.assertEqual(str(self.service.project.uuid), str(self.project.uuid))

    def test_normalize_filters_empty_or_none(self):
        result = self.service._normalize_filters(None)
        self.assertEqual(result, {})
        result = self.service._normalize_filters({})
        self.assertEqual(result, {})

    def test_normalize_filters_with_sectors_queues_tags(self):
        sector_uuid = str(uuid4())
        queue_uuid = str(uuid4())
        tag_uuid = str(uuid4())
        result = self.service._normalize_filters({
            "sectors": [sector_uuid],
            "queues": [queue_uuid],
            "tags": [tag_uuid],
        })
        self.assertIn("sectors", result)
        self.assertIn("queues", result)
        self.assertIn("tags", result)

    @patch("insights.human_support.services.SectorsQueryExecutor")
    @patch("insights.human_support.services.QueuesQueryExecutor")
    @patch("insights.human_support.services.TagsQueryExecutor")
    def test_expand_all_tokens_sectors(self, mock_tags, mock_queues, mock_sectors):
        mock_sectors.execute.return_value = {
            "results": [{"uuid": "sec-1"}, {"uuid": "sec-2"}],
        }
        mock_queues.execute.return_value = {"results": []}
        mock_tags.execute.return_value = {"results": []}
        result = self.service._expand_all_tokens({"sectors": "__all__"})
        self.assertEqual(result["sectors"], ["sec-1", "sec-2"])

    @patch("insights.human_support.services.SectorsQueryExecutor")
    @patch("insights.human_support.services.QueuesQueryExecutor")
    @patch("insights.human_support.services.TagsQueryExecutor")
    def test_expand_all_tokens_queues(self, mock_tags, mock_queues, mock_sectors):
        mock_sectors.execute.return_value = {"results": []}
        mock_queues.execute.return_value = {
            "results": [{"uuid": "q-1"}],
        }
        mock_tags.execute.return_value = {"results": []}
        result = self.service._expand_all_tokens({"queues": "__all__"})
        self.assertEqual(result["queues"], ["q-1"])

    @patch("insights.human_support.services.SectorsQueryExecutor")
    @patch("insights.human_support.services.QueuesQueryExecutor")
    @patch("insights.human_support.services.TagsQueryExecutor")
    def test_expand_all_tokens_tags(self, mock_tags, mock_queues, mock_sectors):
        mock_sectors.execute.return_value = {"results": []}
        mock_queues.execute.return_value = {"results": []}
        mock_tags.execute.return_value = {
            "results": [{"uuid": "t-1"}, {"uuid": "t-2"}],
        }
        result = self.service._expand_all_tokens({"tags": ["__all__"]})
        self.assertEqual(result["tags"], ["t-1", "t-2"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_attendance_status(self, mock_rooms):
        mock_rooms.execute.return_value = {"value": 5}
        result = self.service.get_attendance_status()
        self.assertEqual(result["is_waiting"], 5)
        self.assertEqual(result["in_progress"], 5)
        self.assertEqual(result["finished"], 5)

    @patch("insights.human_support.services.ChatsTimeMetricsClient")
    def test_get_time_metrics(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.retrieve_time_metrics.return_value = {
            "avg_waiting_time": 10.0,
            "max_waiting_time": 30.0,
            "avg_first_response_time": 20.0,
            "max_first_response_time": 60.0,
            "avg_conversation_duration": 300.0,
            "max_conversation_duration": 600.0,
        }
        mock_client_class.return_value = mock_client
        result = self.service.get_time_metrics()
        self.assertEqual(result["average_time_is_waiting"]["average"], 10.0)
        self.assertEqual(result["average_time_is_waiting"]["max"], 30.0)
        self.assertEqual(result["average_time_first_response"]["average"], 20.0)
        self.assertEqual(result["average_time_chat"]["average"], 300.0)

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_peaks_in_human_service(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [{"hour": 10, "count": 5}]}
        result = self.service.get_peaks_in_human_service()
        self.assertEqual(result, [{"hour": 10, "count": 5}])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_analysis_peaks_in_human_service(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [{"hour": 14, "count": 3}]}
        result = self.service.get_analysis_peaks_in_human_service()
        self.assertEqual(result, [{"hour": 14, "count": 3}])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_detailed_monitoring_on_going(self, mock_rooms):
        mock_rooms.execute.return_value = {
            "results": [
                {
                    "agent": "Agent 1",
                    "duration": 120,
                    "waiting_time": 10,
                    "first_response_time": 5,
                    "sector": "S1",
                    "queue": "Q1",
                    "contact": "C1",
                    "link": "https://link/1",
                },
            ],
            "next": None,
            "previous": None,
            "count": 1,
        }
        result = self.service.get_detailed_monitoring_on_going(filters={})
        self.assertEqual(result["count"], 1)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["agent"], "Agent 1")
        self.assertEqual(result["results"][0]["duration"], 120)
        self.assertEqual(result["results"][0]["link"], "https://link/1")

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_detailed_monitoring_on_going_with_filters_and_ordering(self, mock_rooms):
        mock_rooms.execute.return_value = {
            "results": [],
            "next": None,
            "previous": None,
            "count": 0,
        }
        result = self.service.get_detailed_monitoring_on_going(
            filters={"limit": 10, "offset": 0, "ordering": "-duration"}
        )
        self.assertEqual(result["count"], 0)
        call_kwargs = mock_rooms.execute.call_args[0][0]
        self.assertEqual(call_kwargs.get("limit"), 10)
        self.assertEqual(call_kwargs.get("offset"), 0)
        self.assertEqual(call_kwargs.get("ordering"), "-duration")

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_detailed_monitoring_awaiting(self, mock_rooms):
        mock_rooms.execute.return_value = {
            "results": [
                {
                    "queue_time": 30,
                    "contact": "Contact A",
                    "sector": "S1",
                    "queue": "Q1",
                    "link": "https://link/a",
                },
            ],
            "next": None,
            "previous": None,
            "count": 1,
        }
        result = self.service.get_detailed_monitoring_awaiting()
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["awaiting_time"], 30)
        self.assertEqual(result["results"][0]["contact"], "Contact A")

    @patch("insights.human_support.services.AgentsRESTClient")
    def test_get_detailed_monitoring_agents(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.list.return_value = {
            "results": [
                {
                    "agent": "agent-uuid",
                    "agent_email": "a@b.com",
                    "status": {"status": "online", "label": "Available"},
                    "opened": 2,
                    "closed": 10,
                    "avg_first_response_time": 5.0,
                    "avg_message_response_time": 10.0,
                    "avg_interaction_time": 120.0,
                    "time_in_service": 3600,
                    "link": "https://agent/link",
                },
            ],
            "next": None,
            "previous": None,
            "count": 1,
        }
        mock_client_class.return_value = mock_client
        result = self.service.get_detailed_monitoring_agents()
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["status"], "online")
        self.assertEqual(result["results"][0]["status_label"], "Available")
        self.assertEqual(result["results"][0]["ongoing"], 2)
        self.assertEqual(result["results"][0]["finished"], 10)

    @patch("insights.human_support.services.AgentsRESTClient")
    def test_get_detailed_monitoring_agents_status_non_dict(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.list.return_value = {
            "results": [
                {
                    "agent": "agent-uuid",
                    "agent_email": "a@b.com",
                    "status": "busy",
                    "opened": 0,
                    "closed": 0,
                    "link": None,
                },
            ],
            "next": None,
            "previous": None,
            "count": 1,
        }
        mock_client_class.return_value = mock_client
        result = self.service.get_detailed_monitoring_agents()
        self.assertEqual(result["results"][0]["status"], "busy")
        self.assertNotIn("status_label", result["results"][0])

    @patch("insights.human_support.services.CustomStatusRESTClient")
    def test_get_detailed_monitoring_status(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.list_custom_status_by_agent.return_value = {
            "results": [{"agent": "a1", "custom_status": []}],
            "next": None,
            "previous": None,
            "count": 1,
        }
        mock_client_class.return_value = mock_client
        result = self.service.get_detailed_monitoring_status()
        self.assertEqual(result["count"], 1)

    def test_csat_score_by_agents_with_mock_chats_client(self):
        mock_chats = MagicMock()
        mock_chats.csat_score_by_agents.return_value = {"results": []}
        service = HumanSupportDashboardService(project=self.project, chats_client=mock_chats)
        result = service.csat_score_by_agents(user_request="test", filters={})
        self.assertEqual(result, {"results": []})
        mock_chats.csat_score_by_agents.assert_called_once()
        call_kwargs = mock_chats.csat_score_by_agents.call_args[1]
        self.assertEqual(call_kwargs["project_uuid"], str(self.project.uuid))

    @patch("insights.human_support.services.CustomStatusRESTClient")
    def test_get_analysis_detailed_monitoring_status(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.list_custom_status_by_agent.return_value = {
            "results": [
                {
                    "agent": "a1",
                    "agent_email": "a1@x.com",
                    "custom_status": [{"name": "Break"}],
                    "link": "https://link",
                },
            ],
            "next": None,
            "previous": None,
            "count": 1,
        }
        mock_client_class.return_value = mock_client
        result = self.service.get_analysis_detailed_monitoring_status(filters={})
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["custom_status"], [{"name": "Break"}])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_finished_rooms(self, mock_rooms):
        mock_rooms.execute.return_value = {
            "results": [
                {
                    "agent": "Agent 1",
                    "sector": "S1",
                    "queue": "Q1",
                    "contact": "C1",
                    "protocol": "TICKET-001",
                    "waiting_time": 10,
                    "first_response_time": 5,
                    "duration": 100,
                    "ended_at": "2025-02-06T12:00:00",
                    "csat_rating": 5,
                    "link": "https://link/1",
                },
            ],
            "next": None,
            "previous": None,
            "count": 1,
        }
        result = self.service.get_finished_rooms()
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["ticket_id"], "TICKET-001")
        self.assertEqual(result["results"][0]["csat_rating"], 5)

    @patch("insights.human_support.services.RoomsQueryExecutor")
    @patch("insights.human_support.services.ChatsTimeMetricsClient")
    def test_get_analysis_status(self, mock_time_client_class, mock_rooms):
        mock_rooms.execute.return_value = {"value": 42}
        mock_time_client = MagicMock()
        mock_time_client.retrieve_time_metrics_for_analysis.return_value = {
            "avg_waiting_time": 5.0,
            "avg_first_response_time": 10.0,
            "avg_message_response_time": 15.0,
            "avg_conversation_duration": 200.0,
        }
        mock_time_client_class.return_value = mock_time_client
        result = self.service.get_analysis_status()
        self.assertEqual(result["finished"], 42)
        self.assertEqual(result["average_waiting_time"], 5.0)
        self.assertEqual(result["average_first_response_time"], 10.0)
        self.assertEqual(result["average_response_time"], 15.0)
        self.assertEqual(result["average_conversation_duration"], 200.0)

    def test_get_csat_ratings_with_mock_chats_client(self):
        mock_chats = MagicMock()
        mock_chats.csat_ratings.return_value = {
            "csat_ratings": [
                {"rating": 1, "value": 2, "full_value": 2},
                {"rating": 5, "value": 10, "full_value": 10},
            ],
        }
        service = HumanSupportDashboardService(project=self.project, chats_client=mock_chats)
        result = service.get_csat_ratings()
        self.assertEqual(result["1"]["value"], 2)
        self.assertEqual(result["5"]["value"], 10)
        self.assertEqual(result["3"]["value"], 0)

    def test_get_attendance_status_with_sectors_queues_tags_as_lists(self):
        with patch("insights.human_support.services.RoomsQueryExecutor") as mock_rooms:
            mock_rooms.execute.return_value = {"value": 0}
            result = self.service.get_attendance_status(
                filters={
                    "sectors": "sector-uuid-1",
                    "queues": "queue-uuid-1",
                    "tags": "tag-uuid-1",
                }
            )
            self.assertEqual(result["is_waiting"], 0)
            self.assertEqual(result["in_progress"], 0)
            self.assertEqual(result["finished"], 0)

    @patch("insights.human_support.services.ChatsTimeMetricsClient")
    def test_get_time_metrics_with_date_filters(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.retrieve_time_metrics.return_value = {}
        mock_client_class.return_value = mock_client
        self.service.get_time_metrics(
            filters={
                "start_date": date(2025, 1, 1),
                "end_date": date(2025, 1, 31),
            }
        )
        call_args = mock_client.retrieve_time_metrics.call_args[1]
        self.assertEqual(call_args["params"].get("start_date"), "2025-01-01")
        self.assertEqual(call_args["params"].get("end_date"), "2025-01-31")

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_peaks_with_sectors_queues_tags_filters(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": []}
        sector_uuid = str(uuid4())
        queue_uuid_1, queue_uuid_2 = str(uuid4()), str(uuid4())
        tag_uuid = str(uuid4())
        self.service.get_peaks_in_human_service(
            filters={
                "sectors": sector_uuid,
                "queues": [queue_uuid_1, queue_uuid_2],
                "tags": tag_uuid,
            }
        )
        call_kwargs = mock_rooms.execute.call_args[1]
        filters_arg = call_kwargs["filters"]
        self.assertIn("sector__in", filters_arg)
        self.assertIn("queue__in", filters_arg)
        self.assertIn("tags__in", filters_arg)

    def test_get_detailed_monitoring_agents_filters_ordering(self):
        params = self.service._get_detailed_monitoring_agents_filters(
            {"ordering": "-first_name"}
        )
        self.assertEqual(params.get("ordering"), "-first_name")

    @patch("insights.human_support.services.CustomStatusRESTClient")
    def test_get_detailed_monitoring_status_with_ordering(self, mock_client_class):
        mock_client_class.return_value.list_custom_status_by_agent.return_value = {
            "results": [],
            "next": None,
            "previous": None,
            "count": 0,
        }
        self.service.get_detailed_monitoring_status(
            filters={"ordering": "agent", "limit": 5, "offset": 10}
        )
        call_args = mock_client_class.return_value.list_custom_status_by_agent.call_args[0][0]
        self.assertEqual(call_args.get("ordering"), "agent")
        self.assertEqual(call_args.get("limit"), 5)
        self.assertEqual(call_args.get("offset"), 10)

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_finished_rooms_with_ordering_and_dates(self, mock_rooms):
        mock_rooms.execute.return_value = {
            "results": [],
            "next": None,
            "previous": None,
            "count": 0,
        }
        self.service.get_finished_rooms(
            filters={
                "start_date": date(2025, 1, 1),
                "end_date": date(2025, 1, 31),
                "ordering": "-ended_at",
                "limit": 20,
                "offset": 0,
            }
        )
        call_args = mock_rooms.execute.call_args[0][0]
        self.assertIn("ended_at__gte", call_args)
        self.assertIn("ended_at__lte", call_args)
        self.assertEqual(call_args.get("ordering"), "-ended_at")

    def test_get_analysis_status_finished_filters(self):
        normalized = {
            "sectors": ["s1"],
            "queues": ["q1"],
            "tags": ["t1"],
            "agent": "agent-uuid",
        }
        result = self.service._get_analysis_status_finished_filters(normalized)
        self.assertEqual(result["sector__in"], ["s1"])
        self.assertEqual(result["queue__in"], ["q1"])
        self.assertEqual(result["tags__in"], ["t1"])
        self.assertEqual(result["agent"], "agent-uuid")
        self.assertEqual(result["project"], str(self.project.uuid))

    def test_get_analysis_status_metrics_filters(self):
        normalized = {
            "sectors": ["s1"],
            "queues": ["q1"],
            "tags": ["t1"],
            "start_date": date(2025, 1, 1),
            "end_date": date(2025, 1, 31),
        }
        result = self.service._get_analysis_status_metrics_filters(normalized)
        self.assertEqual(result["sector"], ["s1"])
        self.assertEqual(result["queue"], ["q1"])
        self.assertEqual(result["tag"], ["t1"])
        self.assertIn("start_date", result)
        self.assertIn("end_date", result)

    def test_project_without_timezone_uses_utc(self):
        project_utc = Project.objects.create(name="No TZ Project", timezone=None)
        service = HumanSupportDashboardService(project=project_utc)
        with patch("insights.human_support.services.RoomsQueryExecutor") as mock_rooms:
            mock_rooms.execute.return_value = {"value": 1}
            result = service.get_attendance_status()
            self.assertEqual(result["is_waiting"], 1)
