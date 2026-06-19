"""
api.py

Flask API for the notification → processing → calendar pipeline.

Endpoints:
  GET  /                        Health check
  POST /notifications/process   Process raw notifications into calendar events
  POST /calendar/add            Add events to Google Calendar
  POST /pipeline/run            Full pipeline: notifications → process → calendar

Run with:
  python api.py
  # or
  flask --app api run --port 5000
"""

import os
import sys

from flask import Flask, jsonify, request

# ── App factory ────────────────────────────────────────────────────────────────
app = Flask(__name__)

# ── CORS ───────────────────────────────────────────────────────────────────────
try:
    from flask_cors import CORS

    # Allow the Expo app (both dev and web) to call the API.
    # In production, restrict origins to your actual domain.
    CORS(
        app,
        origins=os.getenv(
            "CORS_ORIGINS",
            "http://localhost:8081,http://localhost:19006,exp://",
        ).split(","),
    )
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("[WARN] flask-cors not installed — CORS headers disabled", file=sys.stderr)

# ── Rate limiter ───────────────────────────────────────────────────────────────
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )
    RATE_LIMIT_AVAILABLE = True
except ImportError:
    limiter = None
    RATE_LIMIT_AVAILABLE = False
    print(
        "[WARN] flask-limiter not installed — rate limiting disabled", file=sys.stderr
    )


# ── Decorator helper so code works with or without flask-limiter ───────────────
def rate_limit(limit_string: str):
    """Apply a rate limit. Falls back to a no-op if flask-limiter not installed."""

    def decorator(f):
        if limiter is not None:
            return limiter.limit(limit_string)(f)
        return f

    return decorator


# ── Health ─────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "cors": CORS_AVAILABLE,
            "rate_limiting": RATE_LIMIT_AVAILABLE,
            "endpoints": [
                "POST /notifications/process",
                "POST /calendar/add",
                "POST /pipeline/run",
            ],
        }
    )


# ── Process notifications ──────────────────────────────────────────────────────
@app.route("/notifications/process", methods=["POST"])
@rate_limit("30 per hour")
def process_notifications():
    """
    Accept raw Android notifications (JSON array), run them through the
    AI extraction engine, and return calendar-compatible event objects.

    Request body:
      [{"app": "...", "sender": "...", "message": "...", "time": "...", "category": "..."}]

    Response:
      [{"title": "...", "date": "...", "is_schedulable": true, ... }]
    """
    from processing import process_notifications as proc_notifs

    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    if isinstance(body, dict):
        body = [body]

    err, body = _validate_array(body, NOTIFICATION_SCHEMA, "notification")
    if err:
        return jsonify({"error": err}), 400

    try:
        results = proc_notifs(body, source_name="api")
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    return jsonify(results)


# ── Add to calendar ────────────────────────────────────────────────────────────
@app.route("/calendar/add", methods=["POST"])
@rate_limit("10 per hour")
def calendar_add():
    """
    Accept a list of calendar event objects and add the schedulable ones
    to Google Calendar.

    Request body:
      [{"title": "...", "date": "...", "is_schedulable": true, ...}]

    Response:
      {"added": N, "skipped": M, "events": [...]}
    """

    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    if isinstance(body, dict):
        body = [body]

    err, body = _validate_array(body, EVENT_SCHEMA, "event")
    if err:
        return jsonify({"error": err}), 400

    try:
        from calendar_api import add_events_to_calendar

        added, skipped, event_links = add_events_to_calendar(body)
    except Exception as e:
        return jsonify(
            {"error": f"Failed to connect to Google Calendar: {str(e)}"}
        ), 500

    return jsonify({"added": added, "skipped": skipped, "events": event_links})


# ── Full pipeline ──────────────────────────────────────────────────────────────
@app.route("/pipeline/run", methods=["POST"])
@rate_limit("10 per hour")
def pipeline_run():
    """
    Full end-to-end pipeline: raw notifications → AI processing → Google Calendar.

    Request body:
      [{"app": "...", "sender": "...", "message": "...", "time": "...", "category": "..."}]

    Response:
      {"processed": N, "schedulable": M, "added": A, "skipped": S, "events": [...]}
    """
    from calendar_api import add_events_to_calendar
    from processing import process_notifications as proc_notifs

    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    if isinstance(body, dict):
        body = [body]

    err, body = _validate_array(body, NOTIFICATION_SCHEMA, "notification")
    if err:
        return jsonify({"error": err}), 400

    # Step 1: Process with AI
    try:
        events = proc_notifs(body, source_name="api_pipeline")
    except RuntimeError as e:
        return jsonify({"error": f"AI processing failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    processed = len(events)
    schedulable_count = sum(1 for e in events if e.get("is_schedulable"))

    # Step 2: Add to Calendar (shared implementation)
    try:
        added, skipped, event_links = add_events_to_calendar(events)
    except Exception as e:
        return jsonify(
            {
                "error": f"Processing succeeded but calendar connection failed: {str(e)}",
                "processed": processed,
                "schedulable": schedulable_count,
                "events": events,
            }
        ), 500

    return jsonify(
        {
            "processed": processed,
            "schedulable": schedulable_count,
            "added": added,
            "skipped": skipped,
            "events": event_links,
        }
    )


# ── Input validation ───────────────────────────────────────────────────────────

# Try Cython-accelerated versions first; fall back to pure Python.
try:
    from ._speedups import validate_event as _validate_event_cy
    from ._speedups import (
        validate_notification as _validate_notif_cy,  # type: ignore[import-not-found]
    )

    _HAS_SPEEDUPS = True
except ImportError:
    _HAS_SPEEDUPS = False

NOTIFICATION_SCHEMA = {
    "app": (str,),
    "sender": (str, type(None)),
    "message": (str, type(None)),
    "time": (str, type(None)),
    "category": (str, type(None)),
}

EVENT_SCHEMA = {
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


def _validate_item(item: dict, schema: dict, label: str) -> str | None:
    """Validate a single dict against a schema. Returns error message or None."""
    if not isinstance(item, dict):
        return f"Each {label} must be a JSON object, got {type(item).__name__}"

    # Use Cython-accelerated validation for known schemas
    if _HAS_SPEEDUPS:
        if schema is NOTIFICATION_SCHEMA:
            valid, err = _validate_notif_cy(item)  # type: ignore[possibly-undefined]
            if not valid:
                return f"{label}: {err}"
            return None
        elif schema is EVENT_SCHEMA:
            valid, err = _validate_event_cy(item)  # type: ignore[possibly-undefined]
            if not valid:
                return f"{label}: {err}"
            return None

    # Pure Python fallback

    for field, expected_types in schema.items():
        if field not in item:
            return f"{label} is missing required field: {field}"
        if not isinstance(item[field], expected_types):
            type_names = " | ".join(t.__name__ for t in expected_types)
            return (
                f"{label}.{field} must be {type_names}, "
                f"got {type(item[field]).__name__}"
            )

    # Warn on unexpected fields (client may be sending garbage)
    allowed = set(schema.keys())
    extra = set(item.keys()) - allowed
    if extra:
        print(f"[WARN] Unexpected fields in {label}: {extra}", file=sys.stderr)

    return None


def _validate_array(body: list, schema: dict, label: str) -> tuple[str | None, list]:
    """Validate an array of items. Returns (error, items) — error is None on success."""
    if not isinstance(body, list):
        return f"Request body must be a JSON array of {label}s", []

    for i, item in enumerate(body):
        err = _validate_item(item, schema, f"{label}[{i}]")
        if err:
            return err, []

    return None, body


# ── Error handlers ─────────────────────────────────────────────────────────────
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded. Please try again later."}), 429


@app.errorhandler(500)
def internal_error_handler(e):
    return jsonify({"error": "Internal server error."}), 500


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[INFO] Starting Flask API server...", file=sys.stderr)
    print(
        f"[INFO] Rate limiting: {'enabled' if RATE_LIMIT_AVAILABLE else 'DISABLED'}",
        file=sys.stderr,
    )
    # Debug mode is a security risk — enables arbitrary code execution via Werkzeug debugger.
    # Only enable it when the env var is explicitly set (e.g. during local development).
    debug = os.getenv("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=5000, debug=debug)
