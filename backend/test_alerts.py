"""
Quick test for Twilio SMS/MMS + imgbb + Gemini credentials.
Run this BEFORE starting the full backend to check all keys work.

Usage:
    python test_alerts.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path), override=True)

print("=" * 55)
print("  CROWD MONITORING — CREDENTIAL CHECK")
print("=" * 55)

# ── 1. Check all keys are present ────────────────────────────
keys = {
    "GOOGLE_API_KEY":       os.getenv("GOOGLE_API_KEY", ""),
    "IMGBB_API_KEY":        os.getenv("IMGBB_API_KEY", ""),
    "TWILIO_ACCOUNT_SID":   os.getenv("TWILIO_ACCOUNT_SID", ""),
    "TWILIO_AUTH_TOKEN":    os.getenv("TWILIO_AUTH_TOKEN", ""),
    "TWILIO_FROM_NUMBER":   os.getenv("TWILIO_FROM_NUMBER", ""),
    "TWILIO_TO_NUMBER":     os.getenv("TWILIO_TO_NUMBER", ""),
}

placeholders = {"YOUR_GOOGLE_API_KEY_HERE", "YOUR_IMGBB_API_KEY_HERE",
                "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "your_auth_token_here",
                "+1XXXXXXXXXX", "+91XXXXXXXXXX"}

print("\n[1] Checking .env keys...")
all_ok = True
for key, val in keys.items():
    filled = bool(val) and val not in placeholders
    status = "✅" if filled else "❌ NOT SET"
    preview = val[:12] + "..." if filled and len(val) > 12 else val
    print(f"    {status}  {key:30s} {preview}")
    if not filled:
        all_ok = False

if not all_ok:
    print("\n❌ Fix the missing keys in backend/.env first, then re-run.\n")
    exit(1)

# ── 2. Test Twilio credentials ───────────────────────────────
print("\n[2] Testing Twilio credentials...")
try:
    from twilio.rest import Client
    client = Client(keys["TWILIO_ACCOUNT_SID"], keys["TWILIO_AUTH_TOKEN"])
    account = client.api.accounts(keys["TWILIO_ACCOUNT_SID"]).fetch()
    print(f"    ✅ Twilio OK — Account: {account.friendly_name}")
except Exception as e:
    print(f"    ❌ Twilio FAILED: {e}")
    all_ok = False

# ── 3. Test imgbb upload ─────────────────────────────────────
print("\n[3] Testing imgbb image upload...")
try:
    import requests, base64
    # Tiny 1×1 red pixel JPEG (no real image needed for the test)
    tiny_jpeg_b64 = (
        "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8U"
        "HRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAARC"
        "AABAAEDASIA"
        "AhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAABgUE/8QAIhAAAQMEAwEBAAAAAAAAAAAA"
        "AQIDBBESITFBUf/EABQBAQAAAAAAAAAAAAAAAAAAAAD/xAAUEQEAAAAAAAAAAAAAAAAA"
        "AAAA/9oADAMBAAIRAxEAPwCxVr1SnFMbRBt8kLlbHUNuJUFJIPQg9CD6EH1ooorA"
        "KKKKAooooAooooA/9k="
    )
    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": keys["IMGBB_API_KEY"], "image": tiny_jpeg_b64, "expiration": 60},
        timeout=15,
    )
    result = resp.json()
    if result.get("success"):
        print(f"    ✅ imgbb OK — test image URL: {result['data']['url']}")
    else:
        print(f"    ❌ imgbb FAILED: {result}")
        all_ok = False
except Exception as e:
    print(f"    ❌ imgbb FAILED: {e}")
    all_ok = False

# ── 4. Test Gemini API ───────────────────────────────────────
print("\n[4] Testing Google Gemini API...")
try:
    import requests as req
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={keys['GOOGLE_API_KEY']}"
    )
    payload = {"contents": [{"parts": [{"text": "Say OK in one word."}]}]}
    r = req.post(url, json=payload, timeout=15)
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    print(f"    ✅ Gemini OK — response: {text}")
except Exception as e:
    print(f"    ❌ Gemini FAILED: {e}")
    all_ok = False

# ── 5. Send real test SMS ─────────────────────────────────────
if all_ok:
    print(f"\n[5] Sending TEST SMS to {keys['TWILIO_TO_NUMBER']}...")
    answer = input("    Send a real test SMS now? (y/n): ").strip().lower()
    if answer == "y":
        try:
            from notifier import send_alert_sms
            ok = send_alert_sms(
                incident_type="Violence",
                location="Test Location",
                confidence=0.92,
                scene_description="This is a test alert from the crowd monitoring system. If you received this, SMS is working correctly.",
                scene_frame_base64="",   # no image for this quick test
            )
            print(f"    {'✅ SMS sent! Check your phone.' if ok else '❌ SMS failed — check logs above.'}")
        except Exception as e:
            print(f"    ❌ SMS error: {e}")
    else:
        print("    Skipped.")

print("\n" + "=" * 55)
if all_ok:
    print("  ✅ ALL CHECKS PASSED — you can start the backend!")
    print("     Run:  python api.py")
else:
    print("  ❌ Some checks failed — fix the errors above first.")
print("=" * 55 + "\n")
