from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from django.utils.timezone import timedelta

from insights.metrics.skills.exceptions import (
    InvalidDateRangeError,
    MissingFiltersError,
)
from insights.metrics.skills.services.abandoned_cart import (
    ABANDONED_CART_METRICS_START_DATE_MAX_DAYS,
    AbandonedCartSkillService,
)
from insights.projects.models import Project
from insights.sources.meta_message_templates.utils import (
    format_messages_metrics_data,
)


class TestAbandonedCartSkillService(TestCase):
    def setUp(self):
        self.service_class = AbandonedCartSkillService
        self.project = Project.objects.create()

    def test_missing_filters_on_validation(self):
        filters = {}
        service = self.service_class(self.project, filters)

        with self.assertRaisesMessage(
            MissingFiltersError, "Missing required fields: start_date, end_date"
        ):
            service.validate_filters(filters)

    def test_validate_filters_with_start_date_greater_than_end_date(self):
        filters = {
            "start_date": (timezone.now()).date().isoformat(),
            "end_date": (timezone.now() - timedelta(days=5)).date().isoformat(),
        }
        service = self.service_class(self.project, filters)

        with self.assertRaisesMessage(
            InvalidDateRangeError, "End date must be greater than start date"
        ):
            service.validate_filters(filters)

    def test_validate_filters_with_invalid_start_date(self):
        filters = {
            "start_date": (
                timezone.now()
                - timedelta(days=ABANDONED_CART_METRICS_START_DATE_MAX_DAYS + 1)
            )
            .date()
            .isoformat(),
            "end_date": (
                timezone.now()
                - timedelta(days=ABANDONED_CART_METRICS_START_DATE_MAX_DAYS - 10)
            )
            .date()
            .isoformat(),
        }
        service = self.service_class(self.project, filters)

        with self.assertRaisesMessage(
            InvalidDateRangeError,
            f"Start date must be within the last {ABANDONED_CART_METRICS_START_DATE_MAX_DAYS} days",
        ):
            service.validate_filters(filters)

    @patch("insights.sources.orders.clients.VtexOrdersRestClient.list")
    @patch("insights.sources.vtexcredentials.clients.AuthRestClient.get_vtex_auth")
    @patch(
        "insights.sources.meta_message_templates.clients.MetaAPIClient.get_messages_analytics"
    )
    @patch(
        "insights.sources.meta_message_templates.clients.MetaAPIClient.get_templates_list"
    )
    @patch(
        "insights.sources.wabas.clients.WeniIntegrationsClient.get_wabas_for_project"
    )
    def test_get_metrics(
        self,
        mock_wabas,
        mock_templates_list,
        mock_messages_analytics,
        mock_get_vtex_auth,
        mock_vtex_orders_list,
    ):
        mock_wabas.return_value = [
            {
                "waba_id": "123456789098765",
            },
        ]
        mock_templates_list.return_value = {
            "data": [
                {
                    "name": "weni_abandoned_cart",
                    "id": "123456789098765",
                },
            ]
        }

        data_points_for_period = [
            {
                "template_id": "123456789098765",
                "start": 1733011200,
                "end": 1733097600,
                "sent": 10,
                "delivered": 9,
                "read": 8,
                "clicked": [
                    {
                        "type": "quick_reply_button",
                        "button_content": "Access service",
                        "count": 7,
                    },
                ],
            }
            for _ in range(5)
        ]
        data_points_for_past_period = [
            {
                "template_id": "123456789098765",
                "start": 1733011200,
                "end": 1733097600,
                "sent": 5,
                "delivered": 4,
                "read": 3,
                "clicked": [
                    {
                        "type": "quick_reply_button",
                        "button_content": "Access service",
                        "count": 2,
                    },
                ],
            }
            for _ in range(5)
        ]

        data_points = data_points_for_past_period + data_points_for_period
        mock_messages_analytics.return_value = {
            "data": format_messages_metrics_data({"data_points": data_points}),
        }

        mock_get_vtex_auth.return_value = {
            "app_token": "fake_token",
            "app_key": "fake_key",
            "domain": "fake_domain",
        }

        expected_count = 2
        expected_utm_revenue = 50.21

        mock_vtex_orders_list.return_value = {
            "countSell": expected_count,
            "accumulatedTotal": expected_utm_revenue,
            "ticketMax": 50.21,
            "ticketMin": 50.21,
            "medium_ticket": 50.21,
        }

        filters = {
            "start_date": (timezone.now() - timedelta(days=5)).date().isoformat(),
            "end_date": (timezone.now()).date().isoformat(),
        }
        service = self.service_class(self.project, filters)
        metrics = service.get_metrics()

        expected_metrics = [
            {
                "id": "sent-messages",
                "value": 50,
                "percentage": 50.0,
            },
            {
                "id": "delivered-messages",
                "value": 45,
                "percentage": 125.0,
            },
            {
                "id": "read-messages",
                "value": 40,
                "percentage": 166.67,
            },
            {
                "id": "interactions",
                "value": 35,
                "percentage": 250,
            },
            {
                "id": "utm-revenue",
                "value": expected_utm_revenue,
                "percentage": 0,
                "prefix": "R$",
            },
            {
                "id": "orders-placed",
                "value": expected_count,
                "percentage": 0,
            },
        ]

        self.assertEqual(metrics, expected_metrics)
