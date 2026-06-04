"""
test.py

End-to-end test for the notification → processing → calendar pipeline.
Run with:  python test.py
Or:        python test.py --mock    (no phone needed)
"""

import sys
from datetime import datetime

# ── Mock data for offline testing ──────────────────────────────────────────────
MOCK_NOTIFICATIONS = [
    {
        "app": "Telegram",
        "sender": "Alice",
        "message": "Hey, meeting tomorrow at 3pm at the office. Bring the slides.",
        "time": "2025-02-15 14:30:00",
        "category": "msg",
    },
    {
        "app": "WhatsApp",
        "sender": "Bob",
        "message": "Dinner this Friday at 7pm at Nando's?",
        "time": "2025-02-15 12:00:00",
        "category": "msg",
    },
    {
        "app": "Gmail",
        "sender": "HR",
        "message": "Your performance review is scheduled for next Monday at 10am.",
        "time": None,
        "category": "email",
    },
    {
        "app": "Calendar",
        "sender": None,
        "message": "",
        "time": "2025-02-15 09:00:00",
        "category": "reminder",
    },
]


def test_get_notif_shape():
    """Verify get_active_notifications returns the correct shape."""
    from get_notif import APP_LABELS, SYSTEM_PACKAGES, make_fingerprint

    # Fingerprint should be deterministic
    fp1 = make_fingerprint("Telegram", "Alice", "hello")
    fp2 = make_fingerprint("Telegram", "Alice", "hello")
    fp3 = make_fingerprint("Telegram", "Bob", "hello")
    assert fp1 == fp2, "Fingerprint must be deterministic"
    assert fp1 != fp3, "Fingerprint must differ on different senders"

    # APP_LABELS should be a dict
    assert isinstance(APP_LABELS, dict)
    assert "org.telegram.messenger" in APP_LABELS
    assert APP_LABELS["org.telegram.messenger"] == "Telegram"

    # SYSTEM_PACKAGES should be a set
    assert isinstance(SYSTEM_PACKAGES, set)
    assert "android" in SYSTEM_PACKAGES
    assert "com.android.systemui" in SYSTEM_PACKAGES

    print("[PASS] test_get_notif_shape")


def test_get_notif_with_mock(notifications):
    """Verify notifications list has the right schema."""
    for i, n in enumerate(notifications):
        assert isinstance(n, dict), f"Notification {i} must be a dict"
        assert "app" in n, f"Notification {i} missing 'app'"
        assert "message" in n, f"Notification {i} missing 'message'"
        # sender, time, category can be None
        valid_keys = {"app", "sender", "message", "time", "category"}
        assert set(n.keys()).issubset(valid_keys), (
            f"Unexpected keys in notification {i}: {n.keys() - valid_keys}"
        )
    print(f"[PASS] test_get_notif_with_mock ({len(notifications)} notifications)")


def test_processing_shape(notifications):
    """Verify process_notifications produces correct output shape."""
    from processing import process_notifications

    results = process_notifications(notifications, source_name="test")

    assert isinstance(results, list), "process_notifications must return a list"
    for i, event in enumerate(results):
        assert isinstance(event, dict), f"Event {i} must be a dict"
        required_keys = {
            "title",
            "date",
            "time",
            "duration_minutes",
            "sender",
            "description",
            "location",
            "attendees",
            "recurrence",
            "is_schedulable",
            "_source",
        }
        missing = required_keys - set(event.keys())
        assert not missing, f"Event {i} missing keys: {missing}"

        # is_schedulable must be boolean
        assert isinstance(event["is_schedulable"], bool), (
            f"Event {i}: is_schedulable must be bool"
        )

        # If is_schedulable, title AND date must be non-null
        if event["is_schedulable"]:
            assert event["title"] is not None, f"Event {i}: schedulable with null title"
            assert event["date"] is not None, f"Event {i}: schedulable with null date"

    schedulable = sum(1 for r in results if r["is_schedulable"])
    print(
        f"[PASS] test_processing_shape ({len(results)} events, {schedulable} schedulable)"
    )
    return results


def test_build_event_shape(events):
    """Verify build_event produces valid Google Calendar API event dicts."""
    from calendar_api import build_event

    for i, item in enumerate(events):
        if not item.get("is_schedulable"):
            continue

        event = build_event(item)
        assert isinstance(event, dict), f"build_event {i} must return a dict"

        # Required GCAL fields
        assert "summary" in event
        assert "description" in event
        assert "start" in event
        assert "end" in event

        # start/end must have dateTime and timeZone
        assert "dateTime" in event["start"]
        assert "timeZone" in event["start"]
        assert "dateTime" in event["end"]
        assert "timeZone" in event["end"]

        # end must be after start
        start_dt = datetime.fromisoformat(event["start"]["dateTime"])
        end_dt = datetime.fromisoformat(event["end"]["dateTime"])
        assert end_dt > start_dt, f"Event {i}: end must be after start"

        print(f"  [OK] build_event: {event['summary']} ({start_dt} → {end_dt})")

    print("[PASS] test_build_event_shape")


def test_full_pipeline(notifications):
    """End-to-end: notifications → process → build_event."""
    from calendar_api import build_event
    from processing import process_notifications

    results = process_notifications(notifications, source_name="e2e_test")
    schedulable = [r for r in results if r["is_schedulable"]]

    print(
        f"\n[PIPELINE] {len(notifications)} notifs → {len(results)} events → {len(schedulable)} schedulable"
    )

    for item in schedulable:
        event = build_event(item)
        print(
            f"  📅 {event['summary']} | {event['start']['dateTime']} | {event.get('location', 'no location')}"
        )

    print(f"[PASS] test_full_pipeline ({len(schedulable)} events built)")


def test_empty_input():
    """Edge case: empty notification list."""
    from processing import process_notifications

    results = process_notifications([], source_name="test")
    assert results == [], "Empty input must produce empty output"
    print("[PASS] test_empty_input")


def main():
    use_mock = "--mock" in sys.argv

    print("=" * 60)
    print("Pipeline Tests")
    print("=" * 60)

    # ── Stage 1: get_notif ────────────────────────────────────────────────────
    print("\n─── Stage 1: get_notif ───")
    test_get_notif_shape()

    if use_mock:
        notifications = MOCK_NOTIFICATIONS
        print(f"[INFO] Using {len(notifications)} mock notifications (--mock)")
    else:
        from get_notif import get_active_notifications

        result = get_active_notifications()
        if result is None:
            print("[WARN] No phone detected — falling back to mock data")
            notifications = MOCK_NOTIFICATIONS
        else:
            notifications, new_count, skip_count = result
            print(f"[INFO] Fetched {new_count} new, {skip_count} skipped from phone")

    test_get_notif_with_mock(notifications)

    # ── Stage 2: processing ───────────────────────────────────────────────────
    print("\n─── Stage 2: processing ───")
    events = test_processing_shape(notifications)

    # ── Stage 3: calendar_api ─────────────────────────────────────────────────
    print("\n─── Stage 3: calendar_api ───")
    test_build_event_shape(events)

    # ── Full pipeline ─────────────────────────────────────────────────────────
    print("\n─── Full Pipeline ───")
    test_full_pipeline(notifications)

    # ── Edge cases ────────────────────────────────────────────────────────────
    print("\n─── Edge Cases ───")
    test_empty_input()

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
