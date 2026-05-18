import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import processing
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

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
    """Convert your friend's JSON format into a Google Calendar event."""

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


def add_events(events_json):
    """Takes the list of events and adds schedulable ones to Google Calendar."""
    service = get_calendar_service()

    added = 0
    skipped = 0

    for item in events_json:
        # Skip if not schedulable
        if not item.get("is_schedulable", False):
            print(
                f"⏭️  Skipped (not schedulable): {item.get('title')} — {item.get('description')}"
            )
            skipped += 1
            continue

        event = build_event(item)
        result = service.events().insert(calendarId="primary", body=event).execute()
        print(f"✅ Added to calendar: {item.get('title')} → {result.get('htmlLink')}")
        added += 1

    print(f"\nDone! {added} added, {skipped} skipped.")


# --- MAIN ---
if __name__ == "__main__":
    # Load your JSON (from a file or paste directly)
    with open("events.json", "r") as f:
        events = json.load(f)

    add_events(events)
