"""
processing.py

this file is for openrouter api call and reformat
"""

import json
import os
from datetime import date
from pathlib import Path

import get_notif
from dotenv import load_dotenv
from openai import OpenAI

## Config
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

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("DEEPSEEK_API_KEY"),  # change
)


def build_prompt(notification_text: str) -> str:
    return f"""
Today's date: {date.today().isoformat()}. Day: {date.today().strftime("%A")}
Notification: {notification_text}
"""


def extract_event(notification_text: str) -> dict:
    response = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(notification_text)},
        ],
    )
    raw = response.choices[0].message.content.strip()

    # Strip markdown fences if model wraps in ```json ... ```
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)


def process_file(input_file):
    results = []

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)  # load whole file at once

    # handle both single object {} and array [{}]
    if isinstance(data, dict):
        data = [data]

    for notif in data:
        try:
            text = notif.get("message", "")  # changed from "text" to "message"
            if not text:
                print(f"[SKIP] Empty message in {input_file.name}")
                continue

            event = extract_event(text)
            event["_source"] = input_file.name
            results.append(event)
            print(
                f"[OK] {event.get('title')} | schedulable={event.get('is_schedulable')}"
            )

        except json.JSONDecodeError as e:
            print(f"[PARSE ERROR] {input_file.name}: {e}")
        except Exception as e:
            print(f"[API ERROR] {e}")

    return results


def save_results(results: list, input_file: Path):
    OUTPUT_FILE_DIR.mkdir(parents=True, exist_ok=True)
    # One output file per input file
    output_path = OUTPUT_FILE_DIR / f"{input_file.stem}_processed.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] {output_path}")


## Main
# for sample_file in SAMPLE_FILE_DIR.iterdir():
#     if sample_file.suffix not in (".jsonl", ".json"):
#         continue
#     print(f"\n[PROCESSING] {sample_file.name}")
#     results = process_file(sample_file)
#     save_results(results, sample_file)
