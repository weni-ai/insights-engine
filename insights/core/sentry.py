"""
Sentry helpers: filter expected/noisy events so they stay in logs only.
"""

from __future__ import annotations

import re
from typing import Optional

_IGNORED_EXCEPTION_NAMES = frozenset(
    {
        "WorkerLostError",
        "TemplateNotFound",
    }
)

_IGNORED_MESSAGE_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"Worker exited prematurely: signal 15 \(SIGTERM\)",
        r"accounts\.weni\.ai",
        r"chats-engine\.weni\.ai",
        r"graph\.facebook\.com",
        r"data-consumption",
        r"DC API",
        r"Error querying events silver",
        r"Failed to get csat metrics",
        r"Failed to get returning contacts",
        r"No abandoned cart template found",
        r"No templates_uuid found",
        r"Project does not have permission to access WABA",
        r"An error has occurred\. Event ID:",
        r"meta_api_error",
        r"VTEX API error processing page",
        r"\[VTEX Orders\] Response",
        r"Error making request:",
        r"Expecting value: line 1 column 1",
    )
)

_EXPECTED_VALIDATION_DETAILS = (
    "An error has occurred",
    "An error has occurred. Event ID:",
)


def is_expected_validation_error(exc: BaseException) -> bool:
    """True for known Meta/upstream ValidationErrors (not product bugs)."""
    detail = str(exc)
    return any(expected in detail for expected in _EXPECTED_VALIDATION_DETAILS)


def _event_text(event: dict, exc_value: Optional[BaseException]) -> str:
    parts = []
    if event.get("message"):
        parts.append(str(event["message"]))
    if exc_value is not None:
        parts.append(str(exc_value))
    for entry in event.get("exception", {}).get("values") or []:
        if entry.get("type"):
            parts.append(str(entry["type"]))
        if entry.get("value"):
            parts.append(str(entry["value"]))
    return " ".join(parts)


def sentry_before_send(event: dict, hint: dict) -> Optional[dict]:
    """
    Drop expected noise from Sentry. Real bugs must still pass through.
    """
    exc_info = hint.get("exc_info")
    exc_value = None
    if exc_info:
        exc_type, exc_value, _ = exc_info
        name = getattr(exc_type, "__name__", "")
        if name in _IGNORED_EXCEPTION_NAMES:
            return None
        if is_expected_validation_error(exc_value):
            return None

    text = _event_text(event, exc_value)
    if any(pattern.search(text) for pattern in _IGNORED_MESSAGE_PATTERNS):
        return None

    return event
