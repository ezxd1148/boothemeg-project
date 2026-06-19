import json
import logging
import os
import sys
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ── Logging ────────────────────────────────────────────────────────────────────
logger = logging.getLogger("calendar_api")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIMEZONE = "Asia/Kuala_Lumpur"


def get_calendar_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def build_event(item):
    """Convert a calendar event dict into a Google Calendar API event resource."""

    # --- Build start dateTime ---
    # If date is null, use today as fallback
    date_str = item.get("date") or datetime.today().strftime("%Y-%m-%d")
    time_str = item.get("time") or "09:00:00"
    start_dt = datetime.fromisoformat(f"{date_str}T{time_str}")

    # --- Build end dateTime ---
    duration = item.get("duration_minutes") or 30  # default 30 mins if null
    end_dt = start_dt + timedelta(minutes=duration)

    # --- Base event ---
    event = {
        "summary": item.get("title", "Untitled Event"),
        "description": item.get("description", ""),
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": TIMEZONE,
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": TIMEZONE,
        },
    }

    # --- Optional fields ---
    if item.get("location"):
        event["location"] = item["location"]

    if item.get("attendees"):
        event["attendees"] = [{"email": a} for a in item["attendees"]]

    if item.get("recurrence"):
        event["recurrence"] = [f"RRULE:{item['recurrence']}"]

    return event


def add_events_to_calendar(events: list, service=None) -> tuple[int, int, list[dict]]:
    """Add a list of calendar event dicts to Google Calendar.

    This is the shared implementation used by both the CLI pipe and the Flask API.

    Args:
        events: List of event dicts with at least (title, date, is_schedulable).
        service: A Google Calendar API service instance. If None, one is created.

    Returns:
        (added_count, skipped_count, event_links)
        event_links is a list of dicts: {summary, start, link} or {summary, error}
    """
    if service is None:
        service = get_calendar_service()

    added = 0
    skipped = 0
    event_links = []

    for item in events:
        if not item.get("is_schedulable", False):
            logger.info("Skipped (not schedulable): %s", item.get("title"))
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
            logger.info(
                "Added to calendar: %s → %s",
                event.get("summary"),
                result.get("htmlLink"),
            )
        except Exception as e:
            logger.error("Failed to add event '%s': %s", item.get("title", "?"), e)
            event_links.append(
                {"summary": item.get("title", "unknown"), "error": str(e)}
            )

    logger.info(
        "%d added, %d skipped, %d errors",
        added,
        skipped,
        len([e for e in event_links if "error" in e]),
    )
    return added, skipped, event_links


# --- MAIN ---
if __name__ == "__main__":
    # Read JSON array from stdin (piped from processing.py)
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        logger.error("No input received on stdin")
        sys.exit(1)

    try:
        events = json.loads(raw_input)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON on stdin: %s", e)
        sys.exit(1)

    add_events_to_calendar(events)
