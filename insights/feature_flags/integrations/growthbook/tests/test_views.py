import json
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class TestGrowthbookWebhook(APITestCase):
    def url(self):
        return reverse("growthbook_webhook-list")

    def receive(self, body: str, secret: str | None = None):
        headers = {}
        if secret is not None:
            headers["HTTP_SECRET"] = secret
        return self.client.post(self.url(), data=body, content_type="application/json", **headers)

    def test_unauthorized_without_secret(self):
        response = self.receive(json.dumps({"ping": True}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch(
        "insights.feature_flags.integrations.growthbook.tasks.update_growthbook_feature_flags.delay"
    )
    def test_ok_with_secret_triggers_task(self, mock_delay):
        with patch("insights.feature_flags.integrations.growthbook.auth.settings") as mock_settings:
            mock_settings.GROWTHBOOK_WEBHOOK_SECRET = "s3cr3t"
            response = self.receive(json.dumps({"event": "test"}), secret="s3cr3t")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_delay.assert_called_once()