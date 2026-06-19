"""
processing.py

this file is for openrouter api call and reformat

Usage: reads JSON notifications from stdin, processes via OpenRouter, outputs JSON to stdout.
Pipe: python get_notif.py | python processing.py | python calendar_api.py
"""

import json
import logging
import os
import re
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# ── Logging ────────────────────────────────────────────────────────────────────
logger = logging.getLogger("processing")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)

# ── Config ─────────────────────────────────────────────────────────────────────
SAMPLE_FILE_DIR = Path(__file__).parent.parent / "samples"
OUTPUT_FILE_DIR = Path(__file__).parent / "output" / "processed"
SYSTEM_PROMPT = """
You are an event extraction engine.
You must extract scheduling information from Android notification text
Return ONLY a valid JSON object. Make sure to return Google Calendar API Compatible JSON object

Schema:
{
  "title": string | null,
  "date": "YYYY-MM-DD" | null,
  "time": "HH:MM:SS" | null,
  "duration_minutes": integer | null,
  "sender": string | null
  "description": string | null,
  "location": string | null,
  "attendees": [email strings] | [],
  "recurrence": "RRULE string" | null,
  "is_schedulable": boolean
}

Rules:
- is_schedulable = true only if title AND date are both present
- If date is relative ("tomorrow", "next Monday"), resolve it to YYYY-MM-DD based on today's date
- If no duration found, use null (caller will default to 60 min)
- If no time found but date exists, use null for time
- attendees only if actual emails are present in the text
- recurrence only if explicitly stated ("every week", "daily", etc.)
- if recurrence exist, is_schedulable MUST be true for every notification
"""

# Schema the AI output must conform to
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

# Date format the AI must return (YYYY-MM-DD)
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

load_dotenv()

# ── API client ─────────────────────────────────────────────────────────────────
_openai_api_key = os.getenv("OPENROUTER_API_KEY")
if not _openai_api_key:
    logger.critical(
        "OPENROUTER_API_KEY is not set. "
        "Set it in your .env file or environment. "
        "The AI processing pipeline will fail."
    )
    # Don't raise here — let the caller decide whether to proceed.
    # Calls to extract_event() will raise a clear error.

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Lazily create the OpenAI client so missing keys are caught at call time."""
    global _client
    if _client is None:
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. "
                "Create a .env file with OPENROUTER_API_KEY=your-key"
            )
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=key,
        )
    return _client


# ── Validation ─────────────────────────────────────────────────────────────────
# Try Cython-accelerated versions first; fall back to pure Python.
try:
    from ._speedups import strip_markdown_fences  # type: ignore[import-not-found]
    from ._speedups import validate_event as _validate_event_cy

    _HAS_SPEEDUPS = True
except ImportError:
    _HAS_SPEEDUPS = False


def _strip_markdown_fences(raw: str) -> str:
    """Strip ```json ... ``` fences from AI output."""
    if _HAS_SPEEDUPS:
        return strip_markdown_fences(raw)  # type: ignore[possibly-undefined]
    raw = raw.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        if len(parts) >= 2:
            inner = parts[1]
            if inner.startswith("json"):
                inner = inner[4:]
            return inner.strip()
    return raw


def _validate_event(event: dict, source: str = "") -> dict:
    """Validate and coerce an AI-extracted event dict to the expected schema.

    Returns the event unchanged if valid. Logs warnings for fixable issues.
    Raises ValueError if the event is structurally invalid.
    """
    if _HAS_SPEEDUPS:
        valid, err = _validate_event_cy(event)  # type: ignore[possibly-undefined]
        if not valid:
            raise ValueError(err)
        # Cython version does basic validation; apply additional coercions here
        if event["is_schedulable"]:
            if not event.get("title"):
                logger.warning(
                    "is_schedulable=true but title is null — forcing to false"
                )
                event["is_schedulable"] = False
            elif not event.get("date"):
                logger.warning(
                    "is_schedulable=true but date is null — forcing to false"
                )
                event["is_schedulable"] = False
        return event

    # Pure Python fallback
    for field, expected_types in EVENT_SCHEMA.items():
        if field not in event:
            raise ValueError(f"AI output missing required field: {field}")
        if not isinstance(event[field], expected_types):
            raise ValueError(
                f"AI output field '{field}' has wrong type: "
                f"expected {' | '.join(t.__name__ for t in expected_types)}, "
                f"got {type(event[field]).__name__}"
            )

    # Validate is_schedulable consistency
    if event["is_schedulable"]:
        if not event.get("title"):
            logger.warning("is_schedulable=true but title is null — forcing to false")
            event["is_schedulable"] = False
        elif not event.get("date"):
            logger.warning("is_schedulable=true but date is null — forcing to false")
            event["is_schedulable"] = False

    # Validate date format
    if event.get("date") and not DATE_PATTERN.match(event["date"]):
        logger.warning(
            "Date '%s' does not match YYYY-MM-DD format — setting to null",
            event["date"],
        )
        event["date"] = None
        event["is_schedulable"] = False

    # Validate time format (HH:MM:SS)
    if event.get("time") and not re.match(r"^\d{2}:\d{2}:\d{2}$", event["time"]):
        logger.warning(
            "Time '%s' does not match HH:MM:SS format — setting to null",
            event["time"],
        )
        event["time"] = None

    # Warn on unexpected fields
    allowed = set(EVENT_SCHEMA.keys())
    extra = set(event.keys()) - allowed
    if extra:
        logger.warning("AI returned unexpected fields: %s", extra)

    return event


# ── Core ───────────────────────────────────────────────────────────────────────


def build_prompt(notification_text: str) -> str:
    return f"""
Today's date: {date.today().isoformat()}. Day: {date.today().strftime("%A")}
Notification: {notification_text}
"""


def extract_event(notification_text: str) -> dict:
    """Send a notification text to the AI and return a validated event dict.

    Raises RuntimeError if the API key is missing.
    Raises ValueError if the AI output can't be parsed or validated.
    """
    client = _get_client()

    response = client.chat.completions.create(
        model="poolside/laguna-m.1:free",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(notification_text)},
        ],
    )
    raw = response.choices[0].message.content.strip()
    logger.debug("Raw AI response: %s", raw[:200])

    # Strip markdown fences
    raw = _strip_markdown_fences(raw)

    # Parse JSON
    try:
        event = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("AI returned invalid JSON: %s\nRaw: %s", e, raw[:500])
        raise ValueError(
            f"AI returned invalid JSON: {e}. "
            f"Raw response (first 200 chars): {raw[:200]}"
        ) from e

    # Validate schema
    event = _validate_event(event)
    return event


def process_notifications(notifications: list, source_name: str = "stdin") -> list:
    """Process a list of notification dicts and return a list of extracted event dicts."""
    results = []

    for notif in notifications:
        try:
            text = notif.get("message", "")
            if not text:
                logger.info("Skipping notification with empty message")
                continue

            event = extract_event(text)
            event["_source"] = source_name
            results.append(event)
            logger.info(
                "%s | schedulable=%s", event.get("title"), event.get("is_schedulable")
            )

        except RuntimeError as e:
            # API key missing — fatal, don't continue
            logger.critical("%s", e)
            raise
        except ValueError as e:
            logger.error("Validation error: %s", e)
        except Exception as e:
            logger.error("Unexpected error processing notification: %s", e)

    return results


def process_file(input_file) -> list:
    """Process a file (kept for backward compatibility)."""
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    source_name = getattr(input_file, "name", str(input_file))
    return process_notifications(data, source_name)


def save_results(results: list, input_file: Path):
    OUTPUT_FILE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_FILE_DIR / f"{input_file.stem}_processed.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info("Saved results to %s", output_path)


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        logger.error("No input received on stdin")
        sys.exit(1)

    try:
        data = json.loads(raw_input)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON on stdin: %s", e)
        sys.exit(1)

    if isinstance(data, dict):
        data = [data]

    logger.info("Processing %d notification(s)...", len(data))

    try:
        results = process_notifications(data)
    except RuntimeError:
        logger.critical("Aborting due to missing API key")
        sys.exit(1)

    # Output JSON array to stdout
    json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.flush()

    schedulable = sum(1 for r in results if r.get("is_schedulable"))
    logger.info("%d processed, %d schedulable", len(results), schedulable)
