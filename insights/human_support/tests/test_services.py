from datetime import date
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
        result = self.service._normalize_filters(
            {
                "sectors": [sector_uuid],
                "queues": [queue_uuid],
                "tags": [tag_uuid],
            }
        )
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
        self.assertNotIn("waiting_time_goal", result["average_time_is_waiting"])
        self.assertNotIn(
            "first_response_time_goal", result["average_time_first_response"]
        )
        self.assertNotIn("conversation_duration_goal", result["average_time_chat"])
        self.assertEqual(result["average_time_is_waiting"]["average"], 10.0)
        self.assertEqual(result["average_time_is_waiting"]["max"], 30.0)
        self.assertEqual(result["average_time_first_response"]["average"], 20.0)
        self.assertEqual(result["average_time_chat"]["average"], 300.0)

    @patch("insights.human_support.services.ChatsTimeMetricsClient")
    def test_get_time_metrics_with_goals(self, mock_client_class):
        mock_client = MagicMock()
        waiting_goal = {
            "threshold_seconds": 300,
            "threshold_value": 5,
            "unit": "m",
            "is_breached": True,
            "breached_rooms_count": 7,
        }
        first_response_goal = {
            "threshold_seconds": 600,
            "threshold_value": 10,
            "unit": "m",
            "is_breached": True,
            "breached_rooms_count": 3,
        }
        mock_client.retrieve_time_metrics.return_value = {
            "avg_waiting_time": 10.0,
            "max_waiting_time": 30.0,
            "avg_first_response_time": 20.0,
            "max_first_response_time": 60.0,
            "avg_conversation_duration": 300.0,
            "max_conversation_duration": 600.0,
            "waiting_time_goal": waiting_goal,
            "first_response_time_goal": first_response_goal,
        }
        mock_client_class.return_value = mock_client
        result = self.service.get_time_metrics()
        self.assertEqual(
            result["average_time_is_waiting"]["waiting_time_goal"], waiting_goal
        )
        self.assertEqual(
            result["average_time_first_response"]["first_response_time_goal"],
            first_response_goal,
        )
        self.assertNotIn("conversation_duration_goal", result["average_time_chat"])

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
                    "pending_response": True,
                    "goals_metrics": {
                        "first_response_time": {"exceeded": True},
                        "duration": {"exceeded": True},
                        "awaiting_time": {"exceeded": False},
                    },
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
        self.assertTrue(result["results"][0]["pending_response"])
        self.assertEqual(
            result["results"][0]["goals_metrics"],
            {
                "first_response_time": {"exceeded": True},
                "duration": {"exceeded": True},
            },
        )
        self.assertNotIn("awaiting_time", result["results"][0]["goals_metrics"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_detailed_monitoring_on_going_without_goals_metrics(self, mock_rooms):
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
                    "pending_response": True,
                },
            ],
            "next": None,
            "previous": None,
            "count": 1,
        }
        result = self.service.get_detailed_monitoring_on_going(filters={})
        self.assertEqual(result["results"][0]["goals_metrics"], {})

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_detailed_monitoring_on_going_with_filters_and_ordering(
        self, mock_rooms
    ):
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
    def test_get_detailed_monitoring_on_going_with_pending_response_ordering(
        self, mock_rooms
    ):
        mock_rooms.execute.return_value = {
            "results": [],
            "next": None,
            "previous": None,
            "count": 0,
        }
        self.service.get_detailed_monitoring_on_going(
            filters={"ordering": "-pending_response"}
        )
        call_kwargs = mock_rooms.execute.call_args[0][0]
        self.assertEqual(call_kwargs.get("ordering"), "-pending_response")

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
                    "goals_metrics": {
                        "awaiting_time": {"exceeded": False},
                        "first_response_time": {"exceeded": True},
                        "duration": {"exceeded": True},
                    },
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
        self.assertEqual(
            result["results"][0]["goals_metrics"],
            {"awaiting_time": {"exceeded": False}},
        )
        self.assertNotIn("first_response_time", result["results"][0]["goals_metrics"])
        self.assertNotIn("duration", result["results"][0]["goals_metrics"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_detailed_monitoring_awaiting_without_goals_metrics(self, mock_rooms):
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
        self.assertEqual(result["results"][0]["goals_metrics"], {})

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

    @patch("insights.human_support.services.ChatsRESTClient")
    def test_get_detailed_monitoring_status_v2(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.get_status_by_agent.return_value = {
            "results": [{"agent": "a1", "custom_status": []}],
            "next": None,
            "previous": None,
            "count": 1,
        }
        mock_client_class.return_value = mock_client
        result = self.service.get_detailed_monitoring_status_v2()
        self.assertEqual(result["count"], 1)
        mock_client.get_status_by_agent.assert_called_once()

    def test_csat_score_by_agents_with_mock_chats_client(self):
        mock_chats = MagicMock()
        mock_chats.csat_score_by_agents.return_value = {"results": []}
        service = HumanSupportDashboardService(
            project=self.project, chats_client=mock_chats
        )
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

    @patch("insights.human_support.services.ChatsRESTClient")
    def test_get_analysis_detailed_monitoring_status_v2(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.get_status_by_agent.return_value = {
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
        result = self.service.get_analysis_detailed_monitoring_status_v2(filters={})
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["custom_status"], [{"name": "Break"}])
        mock_client.get_status_by_agent.assert_called_once()

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

    def test_get_finished_rooms_v2(self):
        mock_chats = MagicMock()
        mock_chats.get_internal_rooms_v2.return_value = {
            "count": 1,
            "next": "http://chats/v2/internal/rooms/?limit=10&offset=10&project=x",
            "previous": None,
            "results": [
                {
                    "agent": {
                        "name": "Agent 1",
                        "email": "a@x.com",
                        "is_deleted": False,
                    },
                    "sector": {"name": "S1", "is_deleted": False},
                    "queue": {"name": "Q1", "is_deleted": False},
                    "contact": "C1",
                    "protocol": "TICKET-001",
                    "waiting_time": 10,
                    "first_response_time": 5,
                    "duration": 100,
                    "ended_at": "2025-02-06T12:00:00",
                    "csat_rating": 5,
                    "link": {"url": "chats:closed-chats/uuid", "type": "internal"},
                    "automatic_closed": True,
                },
            ],
        }
        service = HumanSupportDashboardService(
            project=self.project, chats_client=mock_chats
        )
        result = service.get_finished_rooms_v2()
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["next"], "limit=10&offset=10&project=x")
        self.assertIsNone(result["previous"])
        row = result["results"][0]
        self.assertEqual(row["ticket_id"], "TICKET-001")
        self.assertEqual(row["agent"]["name"], "Agent 1")
        self.assertFalse(row["agent"]["is_deleted"])
        self.assertEqual(row["sector"]["name"], "S1")
        self.assertEqual(row["awaiting_time"], 10)
        self.assertTrue(row["automatic_closed"])
        mock_chats.get_internal_rooms_v2.assert_called_once()
        call_params = mock_chats.get_internal_rooms_v2.call_args[0][0]
        self.assertEqual(call_params["project"], str(self.project.uuid))
        self.assertEqual(call_params["is_active"], False)

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
        service = HumanSupportDashboardService(
            project=self.project, chats_client=mock_chats
        )
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
        call_args = (
            mock_client_class.return_value.list_custom_status_by_agent.call_args[0][0]
        )
        self.assertEqual(call_args.get("ordering"), "agent")
        self.assertEqual(call_args.get("limit"), 5)
        self.assertEqual(call_args.get("offset"), 10)

    @patch("insights.human_support.services.ChatsRESTClient")
    def test_get_detailed_monitoring_status_v2_with_ordering(self, mock_client_class):
        mock_client_class.return_value.get_status_by_agent.return_value = {
            "results": [],
            "next": None,
            "previous": None,
            "count": 0,
        }
        self.service.get_detailed_monitoring_status_v2(
            filters={"ordering": "agent", "limit": 5, "offset": 10}
        )
        call_args = mock_client_class.return_value.get_status_by_agent.call_args
        params = call_args[0][1]
        self.assertEqual(params.get("ordering"), "agent")
        self.assertEqual(params.get("limit"), 5)
        self.assertEqual(params.get("offset"), 10)

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

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_attendance_status_with_scalar_filters(self, mock_rooms):
        mock_rooms.execute.return_value = {"value": 3}
        sec, que, tag = str(uuid4()), str(uuid4()), str(uuid4())
        result = self.service.get_attendance_status(
            filters={"sectors": sec, "queues": que, "tags": tag}
        )
        self.assertEqual(result["is_waiting"], 3)
        call_filters = mock_rooms.execute.call_args[0][0]
        self.assertIn("sector__in", call_filters)
        self.assertIn("queue__in", call_filters)
        self.assertIn("tags__in", call_filters)

    @patch("insights.human_support.services.ChatsTimeMetricsClient")
    def test_get_time_metrics_with_scalar_sector_filter(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.retrieve_time_metrics.return_value = {}
        mock_client_class.return_value = mock_client
        sec, que, tag = str(uuid4()), str(uuid4()), str(uuid4())
        self.service.get_time_metrics(
            filters={"sectors": sec, "queues": que, "tags": tag}
        )
        call_params = mock_client.retrieve_time_metrics.call_args[1]["params"]
        self.assertIn("sector", call_params)
        self.assertIn("queue", call_params)
        self.assertIn("tag", call_params)

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_peaks_with_scalar_filters(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": []}
        sec, que, tag = str(uuid4()), str(uuid4()), str(uuid4())
        self.service.get_peaks_in_human_service(
            filters={"sectors": sec, "queues": [que], "tags": tag}
        )
        call_filters = mock_rooms.execute.call_args[1]["filters"]
        self.assertIn("sector__in", call_filters)
        self.assertIn("queue__in", call_filters)
        self.assertIn("tags__in", call_filters)

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_analysis_peaks_with_dates_and_filters(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": []}
        sec, que, tag = str(uuid4()), str(uuid4()), str(uuid4())
        self.service.get_analysis_peaks_in_human_service(
            filters={
                "start_date": date(2025, 3, 1),
                "end_date": date(2025, 3, 31),
                "sectors": sec,
                "queues": que,
                "tags": tag,
            }
        )
        call_filters = mock_rooms.execute.call_args[1]["filters"]
        self.assertIn("created_on__gte", call_filters)
        self.assertIn("created_on__lte", call_filters)
        self.assertIn("sector__in", call_filters)
        self.assertIn("queue__in", call_filters)
        self.assertIn("tags__in", call_filters)

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_detailed_monitoring_on_going_with_agent_contact_urn(self, mock_rooms):
        mock_rooms.execute.return_value = {
            "results": [],
            "next": None,
            "previous": None,
            "count": 0,
        }
        self.service.get_detailed_monitoring_on_going(
            filters={
                "sectors": "s1",
                "agent": "agent-uuid",
                "contact": "contact-uuid",
                "urn": "tel:+5511",
            }
        )
        call_filters = mock_rooms.execute.call_args[0][0]
        self.assertEqual(call_filters["agent"], "agent-uuid")
        self.assertEqual(call_filters["contact"], "contact-uuid")
        self.assertEqual(call_filters["urn"], "tel:+5511")

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_detailed_monitoring_awaiting_with_filters(self, mock_rooms):
        mock_rooms.execute.return_value = {
            "results": [],
            "next": None,
            "previous": None,
            "count": 0,
        }
        self.service.get_detailed_monitoring_awaiting(
            filters={
                "contact": "c-uuid",
                "urn": "tel:+5511",
                "limit": 10,
                "offset": 5,
                "ordering": "-Awaiting time",
            }
        )
        call_filters = mock_rooms.execute.call_args[0][0]
        self.assertEqual(call_filters["contact"], "c-uuid")
        self.assertEqual(call_filters["urn"], "tel:+5511")
        self.assertEqual(call_filters["limit"], 10)
        self.assertEqual(call_filters["offset"], 5)
        self.assertEqual(call_filters["ordering"], "-queue_time")

    def test_get_detailed_monitoring_agents_filters_with_dates_and_lists(self):
        from datetime import datetime as dt
        import pytz

        start = pytz.UTC.localize(dt(2025, 3, 1))
        end = pytz.UTC.localize(dt(2025, 3, 31))
        sec = str(uuid4())
        que = str(uuid4())
        tag1, tag2 = str(uuid4()), str(uuid4())
        params = self.service._get_detailed_monitoring_agents_filters(
            {
                "sectors": [sec],
                "queues": que,
                "tags": [tag1, tag2],
                "status": "online",
                "custom_status": "break",
                "start_date": start,
                "end_date": end,
                "agent": "agent-uuid",
                "user_request": "search-term",
                "limit": 10,
                "offset": 5,
                "ordering": "-first_name",
            }
        )
        self.assertEqual(params["start_date"], "2025-03-01")
        self.assertEqual(params["end_date"], "2025-03-31")
        self.assertIn("sector", params)
        self.assertEqual(params["agent"], "agent-uuid")
        self.assertEqual(params["user_request"], "search-term")
        self.assertEqual(params["limit"], 10)
        self.assertEqual(params["offset"], 5)
        self.assertEqual(params["ordering"], "-first_name")

    @patch("insights.human_support.services.ChatsRESTClient")
    def test_get_detailed_monitoring_agents_v2(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.get_agents.return_value = {
            "results": [
                {
                    "agent": {
                        "name": "Agent A",
                        "email": "a@x.com",
                        "is_deleted": False,
                    },
                    "status": {"status": "online", "label": "Available"},
                    "opened": 3,
                    "closed": 7,
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
        result = self.service.get_detailed_monitoring_agents_v2()
        self.assertEqual(result["count"], 1)
        agent = result["results"][0]
        self.assertEqual(agent["agent"]["name"], "Agent A")
        self.assertEqual(agent["status"]["status"], "online")
        self.assertEqual(agent["ongoing"], 3)
        self.assertEqual(agent["finished"], 7)

    @patch("insights.human_support.services.ChatsRESTClient")
    def test_get_detailed_monitoring_status_v2_with_filters(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.get_status_by_agent.return_value = {
            "results": [],
            "next": None,
            "previous": None,
            "count": 0,
        }
        mock_client_class.return_value = mock_client
        from datetime import datetime as dt
        import pytz

        self.service.get_detailed_monitoring_status_v2(
            filters={
                "agent": "agent-uuid",
                "start_date": pytz.UTC.localize(dt(2025, 3, 1)),
                "end_date": pytz.UTC.localize(dt(2025, 3, 31)),
                "user_request": "search",
                "limit": 5,
                "offset": 10,
            }
        )
        mock_client.get_status_by_agent.assert_called_once()
        params = mock_client.get_status_by_agent.call_args.args[1]
        self.assertEqual(params["user_request"], "search")
        self.assertEqual(params["limit"], 5)
        self.assertEqual(params["offset"], 10)
        self.assertEqual(params["agent"], "agent-uuid")

    @patch("insights.human_support.services.AgentsRESTClient")
    def test_get_detailed_monitoring_agents_totals(self, mock_client_class):
        mock_client = MagicMock()
        mock_client.agents_totals.return_value = {"online": 5, "offline": 3}
        mock_client_class.return_value = mock_client
        result = self.service.get_detailed_monitoring_agents_totals()
        self.assertEqual(result, {"online": 5, "offline": 3})
        mock_client.agents_totals.assert_called_once()

    @patch("insights.human_support.services.CustomStatusRESTClient")
    def test_get_detailed_monitoring_status_with_user_request_and_filters(
        self, mock_client_class
    ):
        mock_client_class.return_value.list_custom_status_by_agent.return_value = {
            "results": [],
            "next": None,
            "previous": None,
            "count": 0,
        }
        from datetime import datetime as dt
        import pytz

        self.service.get_detailed_monitoring_status(
            filters={
                "user_request": "test",
                "agent": "agent-uuid",
                "start_date": pytz.UTC.localize(dt(2025, 3, 1)),
                "end_date": pytz.UTC.localize(dt(2025, 3, 31)),
            }
        )
        call_args = (
            mock_client_class.return_value.list_custom_status_by_agent.call_args[0][0]
        )
        self.assertEqual(call_args["user_request"], "test")
        self.assertEqual(call_args["agent"], "agent-uuid")

    def test_params_for_finished_rooms_list_with_agent_contact_ticket(self):
        from datetime import datetime as dt
        import pytz

        start = pytz.UTC.localize(dt(2025, 3, 1))
        end = pytz.UTC.localize(dt(2025, 3, 31))
        normalized = {
            "sectors": ["s1"],
            "agent": "agent-uuid",
            "contact": "contact-uuid",
            "ticket_id": "TICKET-001",
            "start_date": start,
            "end_date": end,
        }
        result = self.service._params_for_finished_rooms_list(
            normalized,
            filters={
                "limit": 20,
                "offset": 5,
                "ordering": "-agent",
            },
        )
        self.assertEqual(result["agent"], "agent-uuid")
        self.assertEqual(result["contact_external_id"], "contact-uuid")
        self.assertEqual(result["protocol"], "TICKET-001")
        self.assertIn("ended_at__gte", result)
        self.assertIn("ended_at__lte", result)
        self.assertEqual(result["ordering"], "-user_full_name")
        self.assertEqual(result["limit"], 20)
        self.assertEqual(result["offset"], 5)

    def test_format_finished_room_v2_item_without_agent(self):
        room = {
            "agent": None,
            "sector": {"name": "S1", "is_deleted": False},
            "queue": {"name": "Q1", "is_deleted": False},
            "contact": "C1",
            "protocol": "TICKET-001",
            "waiting_time": 10,
            "first_response_time": 5,
            "duration": 100,
            "ended_at": "2025-02-06T12:00:00",
            "csat_rating": 5,
            "link": {"url": "chats:closed-chats/uuid", "type": "internal"},
        }
        result = self.service._format_finished_room_v2_item(room)
        self.assertIsNone(result["agent"])
        self.assertEqual(result["sector"]["name"], "S1")

    def test_get_analysis_status_finished_filters_scalar_values(self):
        normalized = {
            "sectors": "s1",
            "queues": "q1",
            "tags": "t1",
        }
        result = self.service._get_analysis_status_finished_filters(normalized)
        self.assertEqual(result["sector__in"], ["s1"])
        self.assertEqual(result["queue__in"], ["q1"])
        self.assertEqual(result["tags__in"], ["t1"])

    def test_get_analysis_status_metrics_filters_scalar_values(self):
        normalized = {
            "sectors": "s1",
            "queues": "q1",
            "tags": "t1",
            "start_date": date(2025, 1, 1),
            "end_date": date(2025, 1, 31),
        }
        result = self.service._get_analysis_status_metrics_filters(normalized)
        self.assertEqual(result["sector"], ["s1"])
        self.assertEqual(result["queue"], ["q1"])
        self.assertEqual(result["tag"], ["t1"])

    def test_build_volume_by_queue_base_filters(self):
        normalized = {
            "sectors": "s1",
            "queues": ["q1", "q2"],
            "tags": "t1",
        }
        result = self.service._build_volume_by_queue_base_filters(normalized)
        self.assertEqual(result["project"], str(self.project.uuid))
        self.assertEqual(result["sector__in"], ["s1"])
        self.assertEqual(result["queue__in"], ["q1", "q2"])
        self.assertEqual(result["tags__in"], ["t1"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_volume_by_queue_waiting(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [], "count": 0}
        self.service.get_volume_by_queue(filters={"chip_name": "waiting", "limit": 10})
        call_kwargs = mock_rooms.execute.call_args[1]
        self.assertTrue(call_kwargs["filters"]["is_active"])
        self.assertTrue(call_kwargs["filters"]["user_id__isnull"])
        self.assertEqual(call_kwargs["query_kwargs"]["limit"], 10)

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_volume_by_queue_ongoing(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [], "count": 0}
        self.service.get_volume_by_queue(filters={"chip_name": "ongoing"})
        call_kwargs = mock_rooms.execute.call_args[1]
        self.assertTrue(call_kwargs["filters"]["is_active"])
        self.assertFalse(call_kwargs["filters"]["user_id__isnull"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_volume_by_queue_closed(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [], "count": 0}
        self.service.get_volume_by_queue(filters={"chip_name": "closed"})
        call_kwargs = mock_rooms.execute.call_args[1]
        self.assertFalse(call_kwargs["filters"]["is_active"])
        self.assertIn("ended_at__gte", call_kwargs["filters"])
        self.assertIn("ended_at__lte", call_kwargs["filters"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_analysis_volume_by_queue_waiting_with_dates(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [], "count": 0}
        from datetime import datetime as dt
        import pytz

        self.service.get_analysis_volume_by_queue(
            filters={
                "chip_name": "waiting",
                "start_date": pytz.UTC.localize(dt(2025, 3, 1)),
                "end_date": pytz.UTC.localize(dt(2025, 3, 31)),
            }
        )
        call_kwargs = mock_rooms.execute.call_args[1]
        self.assertTrue(call_kwargs["filters"]["is_active"])
        self.assertTrue(call_kwargs["filters"]["user_id__isnull"])
        self.assertIn("created_on__gte", call_kwargs["filters"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_analysis_volume_by_queue_ongoing(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [], "count": 0}
        from datetime import datetime as dt
        import pytz

        self.service.get_analysis_volume_by_queue(
            filters={
                "chip_name": "ongoing",
                "start_date": pytz.UTC.localize(dt(2025, 3, 1)),
                "end_date": pytz.UTC.localize(dt(2025, 3, 31)),
            }
        )
        call_kwargs = mock_rooms.execute.call_args[1]
        self.assertTrue(call_kwargs["filters"]["is_active"])
        self.assertFalse(call_kwargs["filters"]["user_id__isnull"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_analysis_volume_by_queue_closed(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [], "count": 0}
        from datetime import datetime as dt
        import pytz

        self.service.get_analysis_volume_by_queue(
            filters={
                "chip_name": "closed",
                "start_date": pytz.UTC.localize(dt(2025, 3, 1)),
                "end_date": pytz.UTC.localize(dt(2025, 3, 31)),
            }
        )
        call_kwargs = mock_rooms.execute.call_args[1]
        self.assertFalse(call_kwargs["filters"]["is_active"])
        self.assertIn("ended_at__gte", call_kwargs["filters"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_analysis_volume_by_queue_no_chip(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [], "count": 0}
        from datetime import datetime as dt
        import pytz

        self.service.get_analysis_volume_by_queue(
            filters={
                "start_date": pytz.UTC.localize(dt(2025, 3, 1)),
                "end_date": pytz.UTC.localize(dt(2025, 3, 31)),
            }
        )
        call_kwargs = mock_rooms.execute.call_args[1]
        self.assertIn("created_on__gte", call_kwargs["filters"])
        self.assertNotIn("is_active", call_kwargs["filters"])

    def test_build_volume_by_tag_base_filters(self):
        normalized = {
            "sectors": "s1",
            "queues": ["q1"],
            "tags": "t1",
        }
        result = self.service._build_volume_by_tag_base_filters(normalized)
        self.assertEqual(result["project"], str(self.project.uuid))
        self.assertEqual(result["sector__in"], ["s1"])
        self.assertEqual(result["tags__in"], ["t1"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_volume_by_tag_ongoing(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [], "count": 0}
        self.service.get_volume_by_tag(filters={"chip_name": "ongoing"})
        call_kwargs = mock_rooms.execute.call_args[1]
        self.assertTrue(call_kwargs["filters"]["is_active"])
        self.assertFalse(call_kwargs["filters"]["user_id__isnull"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_volume_by_tag_closed(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [], "count": 0}
        self.service.get_volume_by_tag(filters={"chip_name": "closed"})
        call_kwargs = mock_rooms.execute.call_args[1]
        self.assertFalse(call_kwargs["filters"]["is_active"])
        self.assertIn("ended_at__gte", call_kwargs["filters"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_analysis_volume_by_tag_ongoing_with_dates(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [], "count": 0}
        from datetime import datetime as dt
        import pytz

        self.service.get_analysis_volume_by_tag(
            filters={
                "chip_name": "ongoing",
                "start_date": pytz.UTC.localize(dt(2025, 3, 1)),
                "end_date": pytz.UTC.localize(dt(2025, 3, 31)),
            }
        )
        call_kwargs = mock_rooms.execute.call_args[1]
        self.assertTrue(call_kwargs["filters"]["is_active"])
        self.assertIn("created_on__gte", call_kwargs["filters"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_analysis_volume_by_tag_closed_with_dates(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [], "count": 0}
        from datetime import datetime as dt
        import pytz

        self.service.get_analysis_volume_by_tag(
            filters={
                "chip_name": "closed",
                "start_date": pytz.UTC.localize(dt(2025, 3, 1)),
                "end_date": pytz.UTC.localize(dt(2025, 3, 31)),
            }
        )
        call_kwargs = mock_rooms.execute.call_args[1]
        self.assertFalse(call_kwargs["filters"]["is_active"])
        self.assertIn("ended_at__gte", call_kwargs["filters"])

    @patch("insights.human_support.services.RoomsQueryExecutor")
    def test_get_analysis_volume_by_tag_no_chip(self, mock_rooms):
        mock_rooms.execute.return_value = {"results": [], "count": 0}
        from datetime import datetime as dt
        import pytz

        self.service.get_analysis_volume_by_tag(
            filters={
                "start_date": pytz.UTC.localize(dt(2025, 3, 1)),
                "end_date": pytz.UTC.localize(dt(2025, 3, 31)),
            }
        )
        call_kwargs = mock_rooms.execute.call_args[1]
        self.assertIn("created_on__gte", call_kwargs["filters"])
        self.assertNotIn("is_active", call_kwargs["filters"])

    def test_get_csat_ratings_skips_invalid_rating(self):
        mock_chats = MagicMock()
        mock_chats.csat_ratings.return_value = {
            "csat_ratings": [
                {"rating": 1, "value": 2, "full_value": 2},
                {"rating": 99, "value": 5, "full_value": 5},
            ],
        }
        service = HumanSupportDashboardService(
            project=self.project, chats_client=mock_chats
        )
        result = service.get_csat_ratings()
        self.assertEqual(result["1"]["value"], 2)
        self.assertEqual(result["2"]["value"], 0)

    @patch("insights.human_support.services.RoomsQueryExecutor")
    @patch("insights.human_support.services.ChatsTimeMetricsClient")
    def test_get_analysis_status_with_dates(self, mock_time_class, mock_rooms):
        mock_rooms.execute.return_value = {"value": 10}
        mock_time = MagicMock()
        mock_time.retrieve_time_metrics_for_analysis.return_value = {
            "avg_waiting_time": 1.0,
            "avg_first_response_time": 2.0,
            "avg_message_response_time": 3.0,
            "avg_conversation_duration": 4.0,
        }
        mock_time_class.return_value = mock_time
        from datetime import datetime as dt
        import pytz

        result = self.service.get_analysis_status(
            filters={
                "start_date": pytz.UTC.localize(dt(2025, 3, 1)),
                "end_date": pytz.UTC.localize(dt(2025, 3, 31)),
            }
        )
        self.assertEqual(result["finished"], 10)
        self.assertEqual(result["average_waiting_time"], 1.0)

    @patch("insights.human_support.services.CustomStatusRESTClient")
    def test_get_analysis_detailed_monitoring_status_with_filters(
        self, mock_client_class
    ):
        mock_client_class.return_value.list_custom_status_by_agent.return_value = {
            "results": [],
            "next": None,
            "previous": None,
            "count": 0,
        }
        from datetime import datetime as dt
        import pytz

        self.service.get_analysis_detailed_monitoring_status(
            filters={
                "user_request": "search",
                "sectors": ["sec-1"],
                "queues": ["q-1"],
                "agent": "agent-uuid",
                "start_date": pytz.UTC.localize(dt(2025, 3, 1)),
                "end_date": pytz.UTC.localize(dt(2025, 3, 31)),
                "limit": 5,
                "offset": 10,
            }
        )
        call_args = (
            mock_client_class.return_value.list_custom_status_by_agent.call_args[0][0]
        )
        self.assertEqual(call_args["user_request"], "search")
        self.assertEqual(call_args["limit"], 5)
        self.assertEqual(call_args["offset"], 10)

    @patch("insights.human_support.services.ChatsRESTClient")
    def test_get_analysis_detailed_monitoring_status_v2_with_filters(
        self, mock_client_class
    ):
        mock_client_class.return_value.get_status_by_agent.return_value = {
            "results": [
                {
                    "agent": "a1",
                    "agent_email": "a@x.com",
                    "custom_status": [],
                    "link": "https://link",
                }
            ],
            "next": None,
            "previous": None,
            "count": 1,
        }
        result = self.service.get_analysis_detailed_monitoring_status_v2(
            filters={
                "sectors": ["sec-1"],
                "agent": "agent-uuid",
            }
        )
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["agent"], "a1")
