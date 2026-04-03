import re
import json
import urllib.request
import urllib.error
import os
import sys

webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
if not webhook_url:
    print("ERROR: DISCORD_WEBHOOK_URL secret is not set.")
    sys.exit(1)

with open("changelog.mdx", "r", encoding="utf-8") as f:
    content = f.read()

# Strip MDX frontmatter (--- ... ---)
content = re.sub(r"^---\n.*?\n---\n\n?", "", content, flags=re.DOTALL)

# Split into sections on ## headers — first section is the latest release
sections = re.split(r"\n(?=## )", content.strip())
if not sections or not sections[0].strip():
    print("ERROR: No changelog entry found.")
    sys.exit(0)

latest = sections[0].strip()

# Build the full message as plain content
# @everyone as a separate first line so Discord resolves the mention
message = f"@everyone\n\n**CZ AUTOZ HELICOPTER FLIGHT SYSTEM**\n\n{latest}"

print(f"Message length: {len(message)} chars")

# Discord webhook content field limit is 2000 chars.
# If over, use an embed (description limit is 4096).
if len(message) <= 2000:
    payload = {"content": message}
else:
    # @everyone in content (triggers the ping), full entry in embed description
    description = f"**CZ AUTOZ HELICOPTER FLIGHT SYSTEM**\n\n{latest}"
    if len(description) > 4000:
        description = description[:3950] + "\n\n*[Full changelog](https://docs.czautoz.co.uk/changelog)*"
    payload = {
        "content": "@everyone",
        "embeds": [
            {
                "description": description,
                "color": 13386752,
                "url": "https://docs.czautoz.co.uk/changelog",
            }
        ],
    }

print(f"Payload size: {len(json.dumps(payload))} bytes")

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    webhook_url,
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST",
)

try:
    with urllib.request.urlopen(req) as resp:
        print(f"SUCCESS — HTTP {resp.status}")
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    print(f"ERROR — HTTP {e.code}: {body}")
    sys.exit(1)
except urllib.error.URLError as e:
    print(f"ERROR — URL error: {e.reason}")
    sys.exit(1)
