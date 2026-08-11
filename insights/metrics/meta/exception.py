from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException


class MarketingMessagesStatusError(Exception):
    pass


META_ERROR_FIELDS = (
    "message",
    "type",
    "code",
    "error_subcode",
    "error_user_title",
    "error_user_msg",
    "fbtrace_id",
    "is_transient",
    "error_data",
)


def parse_meta_error_payload(response) -> dict[str, Any]:
    """Extract the Graph API `error` object from an HTTP response.

    Falls back to a minimal payload when the body is missing or not JSON.
    """
    if response is None:
        return {"message": "Unknown Meta API error"}

    try:
        body = response.json()
    except (ValueError, TypeError):
        text = getattr(response, "text", None) or "Unknown Meta API error"
        return {"message": text}

    if not isinstance(body, dict):
        return {"message": str(body)}

    meta_error = body.get("error")
    if not isinstance(meta_error, dict):
        return {"message": str(body) if body else "Unknown Meta API error"}

    return {
        field: meta_error[field] for field in META_ERROR_FIELDS if field in meta_error
    }


class MetaAPIError(APIException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_code = "meta_api_error"
    default_detail = "An error occurred while calling the Meta API"

    def __init__(
        self,
        meta_error: dict[str, Any] | None = None,
        event_id: str | None = None,
    ):
        meta_error = meta_error or {}
        message = meta_error.get("message") or str(self.default_detail)

        # Set detail as a plain dict so Meta numeric fields (code, error_subcode)
        # are not coerced to ErrorDetail strings by DRF's _get_error_details.
        self.detail = {
            "error": {
                "code": self.default_code,
                "message": message,
                "meta": meta_error,
                "event_id": event_id,
            }
        }
        self.meta_error = meta_error
        self.event_id = event_id
        Exception.__init__(self, self.detail)
