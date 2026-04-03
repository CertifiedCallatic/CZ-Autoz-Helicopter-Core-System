import re
import json
import urllib.request
import urllib.error
import os
import sys

webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
if not webhook_url:
    print("DISCORD_WEBHOOK_URL secret is not set.")
    sys.exit(1)

with open("changelog.mdx", "r", encoding="utf-8") as f:
    content = f.read()

# Strip MDX frontmatter (--- ... ---)
content = re.sub(r"^---\n.*?\n---\n\n?", "", content, flags=re.DOTALL)

# Split into sections on ## headers — first section is the latest release
sections = re.split(r"\n(?=## )", content.strip())
if not sections or not sections[0].strip():
    print("No changelog entry found.")
    sys.exit(0)

latest = sections[0].strip()

# Build the Discord embed description
description = f"**CZ AUTOZ HELICOPTER FLIGHT SYSTEM**\n\n{latest}"

# Discord embed description cap is 4096 — truncate gracefully if needed
if len(description) > 4000:
    description = description[:3950] + "\n\n*[Full changelog](https://docs.czautoz.co.uk/changelog)*"

payload = {
    "content": "@everyone",
    "allowed_mentions": {"parse": ["everyone"]},
    "embeds": [
        {
            "description": description,
            "color": 0xCC4500,
            "url": "https://docs.czautoz.co.uk/changelog",
        }
    ],
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    webhook_url,
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(req) as resp:
        print(f"Discord webhook sent successfully — HTTP {resp.status}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"Discord webhook failed — HTTP {e.code}: {body}")
    sys.exit(1)
