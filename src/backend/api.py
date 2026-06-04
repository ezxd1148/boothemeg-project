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

import sys

from flask import Flask, jsonify, request

# ── App factory ────────────────────────────────────────────────────────────────
app = Flask(__name__)

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
    if not isinstance(body, list):
        return jsonify(
            {"error": "Request body must be a JSON array of notifications"}
        ), 400

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
    from calendar_api import build_event

    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    if isinstance(body, dict):
        body = [body]
    if not isinstance(body, list):
        return jsonify({"error": "Request body must be a JSON array of events"}), 400

    added = 0
    skipped = 0
    event_links = []

    try:
        from calendar_api import get_calendar_service

        service = get_calendar_service()
    except Exception as e:
        return jsonify(
            {"error": f"Failed to connect to Google Calendar: {str(e)}"}
        ), 500

    for item in body:
        if not item.get("is_schedulable", False):
            skipped += 1
            continue
        try:
            event = build_event(item)
            result = service.events().insert(calendarId="primary", body=event).execute()
            event_links.append(
                {
                    "summary": event.get("summary"),
                    "start": event["start"]["dateTime"],
                    "link": result.get("htmlLink"),
                }
            )
            added += 1
        except Exception as e:
            event_links.append(
                {"summary": item.get("title", "unknown"), "error": str(e)}
            )

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
    from calendar_api import build_event, get_calendar_service
    from processing import process_notifications as proc_notifs

    body = request.get_json(silent=True)
    if body is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    if isinstance(body, dict):
        body = [body]
    if not isinstance(body, list):
        return jsonify(
            {"error": "Request body must be a JSON array of notifications"}
        ), 400

    # Step 1: Process with AI
    try:
        events = proc_notifs(body, source_name="api_pipeline")
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    processed = len(events)
    schedulable_events = [e for e in events if e.get("is_schedulable")]

    # Step 2: Add to Calendar
    added = 0
    skipped = 0
    event_links = []

    try:
        service = get_calendar_service()
    except Exception as e:
        return jsonify(
            {
                "error": f"Processing succeeded but calendar connection failed: {str(e)}",
                "processed": processed,
                "schedulable": len(schedulable_events),
                "events": events,
            }
        ), 500

    for item in events:
        if not item.get("is_schedulable", False):
            skipped += 1
            continue
        try:
            event = build_event(item)
            result = service.events().insert(calendarId="primary", body=event).execute()
            event_links.append(
                {
                    "summary": event.get("summary"),
                    "start": event["start"]["dateTime"],
                    "link": result.get("htmlLink"),
                }
            )
            added += 1
        except Exception as e:
            event_links.append(
                {"summary": item.get("title", "unknown"), "error": str(e)}
            )

    return jsonify(
        {
            "processed": processed,
            "schedulable": len(schedulable_events),
            "added": added,
            "skipped": skipped,
            "events": event_links,
        }
    )


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
    app.run(host="0.0.0.0", port=5000, debug=True)
