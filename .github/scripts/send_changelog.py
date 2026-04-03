import re
import json
import os
import sys
import subprocess

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

payload_json = json.dumps(payload)
print(f"Payload size: {len(payload_json)} bytes")

# Use curl — Python's urllib is blocked by Cloudflare on GitHub Actions (error 1010)
result = subprocess.run(
    [
        "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", payload_json,
        webhook_url,
    ],
    capture_output=True,
    text=True,
)

http_code = result.stdout.strip()
print(f"HTTP {http_code}")

if http_code in ("200", "204"):
    print("SUCCESS")
else:
    print(f"ERROR — HTTP {http_code}")
    if result.stderr:
        print(f"curl stderr: {result.stderr}")
    sys.exit(1)
