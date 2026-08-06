from django.test import SimpleTestCase
from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError as DRFValidationError,
)

from insights.core.sentry import (
    is_expected_validation_error,
    sentry_before_send,
)
from insights.metrics.skills.exceptions import TemplateNotFound


class TestSentryBeforeSend(SimpleTestCase):
    def test_drops_meta_graph_http_error(self):
        event = {
            "message": (
                "400 Client Error: Bad Request for url: "
                "https://graph.facebook.com/v21.0/waba/template_analytics"
            )
        }
        self.assertIsNone(sentry_before_send(event, {}))

    def test_drops_chats_engine_and_keycloak_noise(self):
        self.assertIsNone(
            sentry_before_send(
                {
                    "message": (
                        "503 Server Error: Service Unavailable for url: "
                        "https://chats-engine.weni.ai/v1/internal/dashboard/x/csat_ratings/"
                    )
                },
                {},
            )
        )
        self.assertIsNone(
            sentry_before_send(
                {
                    "message": (
                        "HTTPSConnectionPool(host='accounts.weni.ai', port=443): "
                        "Max retries exceeded"
                    )
                },
                {},
            )
        )

    def test_drops_dc_api_noise(self):
        event = {
            "message": (
                "Error querying events silver: DC API Response [500] "
                "data-consumption-ext.vtex.com/weni-events-silver-count"
            )
        }
        self.assertIsNone(sentry_before_send(event, {}))

    def test_drops_template_not_found(self):
        exc = TemplateNotFound("No abandoned cart template found for the project")
        hint = {"exc_info": (TemplateNotFound, exc, None)}
        self.assertIsNone(sentry_before_send({"message": str(exc)}, hint))

    def test_drops_permission_denied_waba(self):
        exc = PermissionDenied(
            detail="Project does not have permission to access WABA"
        )
        hint = {"exc_info": (PermissionDenied, exc, None)}
        self.assertIsNone(sentry_before_send({"message": str(exc)}, hint))

    def test_drops_expected_meta_validation_error(self):
        exc = DRFValidationError(
            {"error": "An error has occurred. Event ID: None"}
        )
        hint = {"exc_info": (DRFValidationError, exc, None)}
        self.assertIsNone(sentry_before_send({"message": str(exc)}, hint))

    def test_drops_worker_lost_sigterm(self):
        class WorkerLostError(Exception):
            pass

        exc = WorkerLostError(
            "Worker exited prematurely: signal 15 (SIGTERM) Job: 1."
        )
        hint = {"exc_info": (WorkerLostError, exc, None)}
        self.assertIsNone(sentry_before_send({"message": str(exc)}, hint))

    def test_keeps_real_bugs(self):
        event = {"message": "'tuple' object has no attribute 'get'"}
        self.assertEqual(sentry_before_send(event, {}), event)

        exc = AttributeError("'tuple' object has no attribute 'get'")
        hint = {"exc_info": (AttributeError, exc, None)}
        self.assertEqual(
            sentry_before_send({"message": str(exc)}, hint),
            {"message": str(exc)},
        )

        system_exit = SystemExit(1)
        hint = {"exc_info": (SystemExit, system_exit, None)}
        self.assertEqual(
            sentry_before_send({"message": "1"}, hint),
            {"message": "1"},
        )


class TestSentryHelpers(SimpleTestCase):
    def test_is_expected_validation_error(self):
        self.assertTrue(
            is_expected_validation_error(
                DRFValidationError({"error": "An error has occurred"})
            )
        )
        self.assertFalse(
            is_expected_validation_error(
                DRFValidationError({"detail": "unexpected field"})
            )
        )
