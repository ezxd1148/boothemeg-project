# cython: language_level=3
"""
_speedups.pyx — Cython-accelerated utility functions for BooTheSchedule.

Compile with:  python build_speedups.py build_ext --inplace
Then import as: from _speedups import make_fingerprint, ...

These functions are pure CPU computation — the only parts of the codebase
that could meaningfully benefit from C compilation. All I/O-bound functions
(API calls, ADB shell, file I/O) remain in pure Python.
"""

import hashlib
import re


# ── Fingerprinting (used by get_notif.py for dedup) ───────────────────────────

def make_fingerprint(app: str, sender: str, message: str) -> str:
    """Hash of app+sender+message to catch same content with different ADB IDs."""
    raw = f"{app}|{sender}|{message}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()


# ── Markdown fence stripping (used by processing.py) ──────────────────────────

def strip_markdown_fences(raw: str) -> str:
    """Strip ```json ... ``` fences from AI output."""
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        if len(parts) >= 2:
            inner = parts[1]
            if inner.startswith("json"):
                inner = inner[4:]
            return inner.strip()
    return raw


# ── Schema validation (used by api.py and processing.py) ──────────────────────

# Pre-compile the date/time regex patterns for speed
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}:\d{2}$")


def validate_event(event: dict) -> tuple[bool, str]:
    """Validate an AI-extracted event dict. Returns (is_valid, error_message).

    The schema checked:
      title: str|None, date: str|None, time: str|None,
      duration_minutes: int|None, sender: str|None,
      description: str|None, location: str|None,
      attendees: list, recurrence: str|None,
      is_schedulable: bool
    """
    schema = {
        "title": (str, type(None)),
        "date": (str, type(None)),
        "time": (str, type(None)),
        "duration_minutes": (int, type(None)),
        "sender": (str, type(None)),
        "description": (str, type(None)),
        "location": (str, type(None)),
        "attendees": (list,),
        "recurrence": (str, type(None)),
        "is_schedulable": (bool,),
    }

    for field, expected_types in schema.items():
        if field not in event:
            return False, f"AI output missing required field: {field}"
        if not isinstance(event[field], expected_types):
            type_names = " | ".join(t.__name__ for t in expected_types)
            return False, (
                f"Field '{field}' has wrong type: "
                f"expected {type_names}, got {type(event[field]).__name__}"
            )

    # Consistency: is_schedulable requires title + date
    if event["is_schedulable"]:
        if not event.get("title") or not event.get("date"):
            return False, "is_schedulable=true but title/date is null"

    # Validate date format
    if event.get("date") is not None and not _DATE_PATTERN.match(event["date"]):
        return False, f"Date '{event['date']}' does not match YYYY-MM-DD"

    # Validate time format
    if event.get("time") is not None and not _TIME_PATTERN.match(event["time"]):
        return False, f"Time '{event['time']}' does not match HH:MM:SS"

    return True, ""


def validate_notification(item: dict) -> tuple[bool, str]:
    """Validate a notification dict. Returns (is_valid, error_message)."""
    schema = {
        "app": (str,),
        "sender": (str, type(None)),
        "message": (str, type(None)),
        "time": (str, type(None)),
        "category": (str, type(None)),
    }

    for field, expected_types in schema.items():
        if field not in item:
            return False, f"Notification missing required field: {field}"
        if not isinstance(item[field], expected_types):
            type_names = " | ".join(t.__name__ for t in expected_types)
            return False, (
                f"Notification.{field} must be {type_names}, "
                f"got {type(item[field]).__name__}"
            )

    return True, ""
