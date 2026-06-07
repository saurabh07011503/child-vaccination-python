"""Test WhatsApp delivery without importing the full app stack.

Usage (from server_py folder):
  python test_whatsapp.py 9370914938

Reads TEXTMEBOT_API_KEY (and optional fallbacks) from this folder's .env file.
No pydantic / FastAPI dependencies required.
"""
import os
import sys
import urllib.parse
import urllib.request


def load_dotenv_simple(path: str) -> None:
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    load_dotenv_simple(os.path.join(here, ".env"))

    apikey = os.environ.get("TEXTMEBOT_API_KEY", "").strip()
    phone = sys.argv[1] if len(sys.argv) > 1 else "9876543210"

    print("TEXTMEBOT_API_KEY:", "set" if apikey else "MISSING — add to server_py/.env")
    print(f"Testing WhatsApp to: {phone}\n")

    if not apikey:
        print("Install app deps with: python -m pip install -r requirements.txt")
        print("Or set TEXTMEBOT_API_KEY in server_py/.env")
        return 1

    recipient = str(phone).replace(" ", "").strip()
    if recipient and not recipient.startswith("+"):
        recipient = f"+91{recipient}" if len(recipient) == 10 else f"+{recipient}"

    body = "NeoVax test: WhatsApp notifications are working."
    url = (
        "https://api.textmebot.com/send.php?"
        + urllib.parse.urlencode({"recipient": recipient, "apikey": apikey, "text": body})
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read().decode("utf-8", errors="replace").strip().lower()
    except Exception as e:
        print("[ERROR] Request failed:", e)
        return 1

    error_markers = (
        "error", "fail", "invalid", "not connected", "not linked", "expired",
        "dont have", "don't have", "not associated", "asociated", "addphone",
        "not active", "subscribe", "click <a href",
    )
    if any(m in data for m in error_markers):
        print("[ERROR] TextMeBot response:", data[:400])
        print("\nIf it says no phone associated: add + link WhatsApp at TextMeBot (see WHATSAPP_SETUP.md)")
        return 1

    print("[SUCCESS] TextMeBot:", data[:200] or "ok")
    print("Check WhatsApp on:", recipient)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
