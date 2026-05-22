"""
Usage: python set_github_secret.py SECRET_NAME SECRET_VALUE
Reads GITHUB_TOKEN from pipeline/.env or environment.
"""
import sys, os, requests, base64
from pathlib import Path
from dotenv import load_dotenv
from nacl.encoding import Base64Encoder
from nacl.public import PublicKey, SealedBox

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "cyberhanks/hanqing"

if len(sys.argv) != 3:
    print("Usage: python set_github_secret.py SECRET_NAME SECRET_VALUE")
    sys.exit(1)

secret_name, secret_value = sys.argv[1], sys.argv[2]

if not GITHUB_TOKEN:
    import subprocess
    # try git credential manager
    try:
        r2 = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            capture_output=True, text=True
        )
        for line in r2.stdout.splitlines():
            if line.startswith("password="):
                GITHUB_TOKEN = line.split("=", 1)[1].strip()
    except Exception:
        pass

if not GITHUB_TOKEN:
    print("ERROR: Cannot find GitHub token. Add GITHUB_TOKEN=ghp_xxx to pipeline/.env")
    sys.exit(1)

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Get repo public key
r = requests.get(f"https://api.github.com/repos/{REPO}/actions/secrets/public-key", headers=headers)
r.raise_for_status()
pub = r.json()

pub_key = PublicKey(pub["key"], Base64Encoder)
box = SealedBox(pub_key)
encrypted = base64.b64encode(box.encrypt(secret_value.encode())).decode()

resp = requests.put(
    f"https://api.github.com/repos/{REPO}/actions/secrets/{secret_name}",
    headers=headers,
    json={"encrypted_value": encrypted, "key_id": pub["key_id"]},
)
if resp.status_code in (201, 204):
    print(f"OK: {secret_name} set successfully (HTTP {resp.status_code})")
else:
    print(f"FAIL: {resp.status_code}: {resp.text}")
