import re
import json
import os
import sys
import subprocess

MESSAGES_FILE = ".github/discord_messages.json"

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

# Extract version string from header (e.g. "v0.1.3")
version_match = re.search(r"v\d+\.\d+\.\d+", latest.splitlines()[0])
version = version_match.group(0) if version_match else "unknown"
print(f"Version: {version}")

# Build message
message = f"@everyone\n\n**CZ AUTOZ HELICOPTER FLIGHT SYSTEM**\n\n{latest}"
print(f"Message length: {len(message)} chars")

# Discord webhook content field limit is 2000 chars.
# If over, use an embed (description limit is 4096).
if len(message) <= 2000:
    payload = {"content": message}
else:
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

# Load existing message IDs
try:
    with open(MESSAGES_FILE) as f:
        message_ids = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    message_ids = {}

existing_id = message_ids.get(version)

if existing_id:
    # Edit the existing Discord message
    url = f"{webhook_url}/messages/{existing_id}"
    method = "PATCH"
    print(f"Editing existing message {existing_id} for {version}")
else:
    # Post a new message — ?wait=true returns the message object so we can save the ID
    url = f"{webhook_url}?wait=true"
    method = "POST"
    print(f"Posting new message for {version}")

result = subprocess.run(
    [
        "curl", "-s", "-w", "\n%{http_code}",
        "-X", method,
        "-H", "Content-Type: application/json",
        "-d", payload_json,
        url,
    ],
    capture_output=True,
    text=True,
)

lines = result.stdout.strip().split("\n")
http_code = lines[-1]
response_body = "\n".join(lines[:-1])

print(f"HTTP {http_code}")

if http_code in ("200", "204"):
    if method == "POST" and response_body:
        try:
            msg = json.loads(response_body)
            message_ids[version] = msg["id"]
            with open(MESSAGES_FILE, "w") as f:
                json.dump(message_ids, f, indent=2)
            print(f"Saved message ID {msg['id']} for {version}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"WARNING: Could not save message ID — {e}")
    print("SUCCESS")
else:
    print(f"ERROR — HTTP {http_code}: {response_body}")
    if result.stderr:
        print(f"curl stderr: {result.stderr}")
    sys.exit(1)
