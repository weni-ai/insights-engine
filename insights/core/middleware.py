import traceback
import logging

import sentry_sdk
from django.conf import settings
from django.http import JsonResponse


logger = logging.getLogger(__name__)


class InternalErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        logger.exception(f"Internal error: {exception}")
        event_id = sentry_sdk.capture_exception(exception)

        response_data = {
            "code": "INTERNAL_ERROR",
            "message": "An internal error has occurred",
            "event_id": event_id,
        }

        if settings.DEBUG:
            response_data["detail"] = traceback.format_exc()

        return JsonResponse(response_data, status=500)
