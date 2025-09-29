import base64
import logging

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from standardwebhooks import Webhook

logger = logging.getLogger(__name__)


class GrowthbookSignatureAuthentication(BaseAuthentication):
    def authenticate(self, request):
        secret = settings.GROWTHBOOK_WEBHOOK_SECRET
        raw = request.body
        headers = {k.lower(): v for k, v in request.headers.items()}
        try:
            wh = Webhook(base64.b64encode(secret.encode()).decode())
            wh.verify(raw, headers)
        except Exception as e:
            logger.error("Signature verification failed: %s", e)
            raise AuthenticationFailed("Signature verification failed") from e
        return (None, None)

    def authenticate_header(self, request):
        return "Growthbook-Signature"


class GrowthbookWebhookSecretAuthentication(BaseAuthentication):
    def authenticate(self, request):
        secret = request.headers.get("Secret")
        if secret != settings.GROWTHBOOK_WEBHOOK_SECRET:
            raise AuthenticationFailed("Invalid secret")
        return (None, None)

    def authenticate_header(self, request):
        return "Secret"
