import re
import sys
import json
import hashlib
import datetime
from adbutils import adb  # type: ignore

# sys.stdout.reconfigure(encoding='utf-8')

SYSTEM_PACKAGES = {
    "android",
    "com.android.systemui",
    "com.android.phone",
    "com.android.settings",
    "com.android.launcher",
    "com.android.shell",
    "com.android.bluetooth",
    "com.android.server",
}

APP_LABELS = {
    "org.telegram.messenger":            "Telegram",
    "org.telegram.messenger.web":        "Telegram Web",
    "com.whatsapp":                      "WhatsApp",
    "com.whatsapp.w4b":                  "WhatsApp Business",
    "com.instagram.android":             "Instagram",
    "com.facebook.katana":               "Facebook",
    "com.facebook.orca":                 "Messenger",
    "com.twitter.android":               "Twitter/X",
    "com.google.android.gm":             "Gmail",
    "com.microsoft.teams":               "Microsoft Teams",
    "com.slack":                         "Slack",
    "com.discord":                       "Discord",
    "com.tencent.mm":                    "WeChat",
    "com.snapchat.android":              "Snapchat",
    "com.linkedin.android":              "LinkedIn",
    "com.google.android.apps.messaging": "Google Messages",
}

SEEN_IDS_FILE = "seen_ids.txt"
FILE_DIR_JSON_OUTPUT = (
    "notifications.json"  # Nanti buat persistence directory to output/
)


def load_seen_ids() -> set:
    try:
        with open(SEEN_IDS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()


def save_seen_id(seen_id: str):
    with open(SEEN_IDS_FILE, "a", encoding="utf-8") as f:
        f.write(seen_id + "\n")


def make_fingerprint(app: str, sender: str, message: str) -> str:
    """Hash of app+sender+message to catch same content with different ADB IDs."""
    raw = f"{app}|{sender}|{message}".lower().strip()
    return hashlib.md5(raw.encode()).hexdigest()


def get_active_notifications():
    # ── Connect ───────────────────────────────────────────────────────────────
    devices = adb.device_list()
    if not devices:
        print("No phone detected!")
        return

    device = devices[0]
    print(f"Connected: {device.serial}")

    # ── Fetch dump ────────────────────────────────────────────────────────────
    try:
        raw = device.shell("dumpsys notification --noredact")
        if not raw or not raw.strip():
            raw = device.shell("dumpsys notification")
    except Exception as e:
        print(f"Shell command failed: {e}")
        return

    # ── Load already-processed IDs ────────────────────────────────────────────
    seen_ids = load_seen_ids()

    records    = re.split(r'(?=NotificationRecord\()', raw)
    new_count  = 0
    skip_count = 0
    notifications = []

    for record in records:
        if not record.strip().startswith("NotificationRecord("):
            continue

        # ── Package ───────────────────────────────────────────────────────────
        pkg_match = re.search(r'pkg=([^\s]+)\s+user=', record)
        if not pkg_match:
            continue
        package = pkg_match.group(1).strip()

        if any(package.startswith(p) for p in SYSTEM_PACKAGES):
            continue

        # ── Notification ID ───────────────────────────────────────────────────
        notif_id_match = re.search(r'\bid=(-?\d+)', record)
        notif_id       = notif_id_match.group(1) if notif_id_match else "?"
        adb_key        = f"{package}|{notif_id}"

        # ── Extract fields ────────────────────────────────────────────────────
        title_match  = re.search(r'android\.title\s*=\s*(.+?)(?=\n|android\.)', record)
        text_match   = re.search(r'android\.text\s*=\s*(.+?)(?=\n|android\.)',  record)
        ticker_match = re.search(r'tickerText=(?!null)(.+)', record)
        when_match   = re.search(r'when=(\d+)/', record)
        cat_match    = re.search(r'category=(\w+)', record)

        app     = APP_LABELS.get(package, package.split(".")[-1].capitalize())
        sender  = title_match.group(1).strip() if title_match  else None
        message = text_match.group(1).strip()  if text_match   else None
        if not message and ticker_match:
            message = ticker_match.group(1).strip()

        if when_match:
            dt   = datetime.datetime.fromtimestamp(int(when_match.group(1)) / 1000)
            time = dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            time = None

        category = cat_match.group(1) if cat_match else None

        # ── Dedup layer 1: ADB notification ID ───────────────────────────────
        if adb_key in seen_ids:
            skip_count += 1
            continue

        # ── Dedup layer 2: content fingerprint ───────────────────────────────
        fingerprint = make_fingerprint(app, sender or "", message or "")
        if fingerprint in seen_ids:
            skip_count += 1
            continue

        # ── Collect notification ──────────────────────────────────────────────
        notifications.append({
            "app":      app,
            "sender":   sender,
            "message":  message,
            "time":     time,
            "category": category,
        })

        # ── Mark both keys as seen ────────────────────────────────────────────
        save_seen_id(adb_key)
        save_seen_id(fingerprint)
        seen_ids.add(adb_key)
        seen_ids.add(fingerprint)

        print(f"  [{app}] {sender}: {message}")
        new_count += 1

    # ── Write all new notifications to JSON ───────────────────────────────────
    with open(FILE_DIR_JSON_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(notifications, f, indent=2, ensure_ascii=False)

    print(f"\nDone -- {new_count} new, {skip_count} skipped (duplicates)")
    print(f"Saved to: {FILE_DIR_JSON_OUTPUT}")

if __name__ == "__main__":
    get_active_notifications()