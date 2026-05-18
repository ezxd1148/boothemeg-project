import re
import json
import datetime
from adbutils import adb # type: ignore

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
    "org.telegram.messenger":           "Telegram",
    "org.telegram.messenger.web":       "Telegram Web",
    "com.whatsapp":                     "WhatsApp",
    "com.whatsapp.w4b":                 "WhatsApp Business",
    "com.instagram.android":            "Instagram",
    "com.facebook.katana":              "Facebook",
    "com.facebook.orca":                "Messenger",
    "com.twitter.android":              "Twitter/X",
    "com.google.android.gm":            "Gmail",
    "com.microsoft.teams":              "Microsoft Teams",
    "com.slack":                        "Slack",
    "com.discord":                      "Discord",
    "com.tencent.mm":                   "WeChat",
    "com.snapchat.android":             "Snapchat",
    "com.linkedin.android":             "LinkedIn",
    "com.google.android.apps.messaging":"Google Messages",
}

notifications = []

def get_active_notifications():
    devices = adb.device_list()
    if not devices:
        print("No phone detected!")
        return

    device = devices[0]
    print(f"Connected: {device.serial}")

    try:
        raw = device.shell("dumpsys notification --noredact")
        if not raw or not raw.strip():
            raw = device.shell("dumpsys notification")
    except Exception as e:
        print(f"Shell command failed: {e}")
        return

    records = re.split(r'(?=NotificationRecord\()', raw)
    seen = set()

    for record in records:
        if not record.strip().startswith("NotificationRecord("):
            continue

        pkg_match = re.search(r'pkg=([^\s]+)\s+user=', record)
        if not pkg_match:
            continue
        package = pkg_match.group(1).strip()

        if any(package.startswith(p) for p in SYSTEM_PACKAGES):
            continue

        notif_id = re.search(r'\bid=(-?\d+)', record)
        notif_id = notif_id.group(1) if notif_id else "?"
        if (package, notif_id) in seen:
            continue
        seen.add((package, notif_id))

        title_match  = re.search(r'android\.title\s*=\s*(.+?)(?=\n|android\.)', record)
        text_match   = re.search(r'android\.text\s*=\s*(.+?)(?=\n|android\.)', record)
        ticker_match = re.search(r'tickerText=(?!null)(.+)', record)
        when_match   = re.search(r'when=(\d+)/', record)
        cat_match    = re.search(r'category=(\w+)', record)

        sender  = title_match.group(1).strip()  if title_match  else None
        message = text_match.group(1).strip()   if text_match   else None
        if not message and ticker_match:
            message = ticker_match.group(1).strip()

        if when_match:
            dt = datetime.datetime.fromtimestamp(int(when_match.group(1)) / 1000)
            time = dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            time = None

        notifications.append({
            "app":      APP_LABELS.get(package, package.split(".")[-1].capitalize()),
            "sender":   sender,
            "message":  message,
            "time":     time,
            "category": cat_match.group(1) if cat_match else None,
        })

if __name__ == "__main__":
    get_active_notifications()

with open("notifications.json", "w", encoding="utf-8") as f:
    json.dump(notifications, f, indent=2, ensure_ascii=False)