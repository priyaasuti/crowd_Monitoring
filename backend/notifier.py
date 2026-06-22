"""
Twilio-based alerts for violence, accident, and weapon detection.
Sends a voice call + MMS (image + text) when an incident is confirmed.
Image is uploaded to imgbb (free) to get a public URL for Twilio MMS.
"""

import base64
import io
import os
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

# Load .env from the same directory as this file
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path))


def get_twilio_client():
    """Create and return an authenticated Twilio client."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        print("[NOTIFIER] Warning: Twilio credentials not set. Alerts disabled.")
        return None

    return Client(account_sid, auth_token)


def upload_scene_image(image_base64: str) -> str | None:
    """
    Upload a base64-encoded JPEG image to freeimage.host and return a public URL.

    Twilio MMS requires a publicly accessible image URL. freeimage.host
    provides a free public API — no signup or API key needed.

    Args:
        image_base64: Base64-encoded JPEG image string

    Returns:
        Public image URL string, or None if upload fails
    """
    try:
        response = requests.post(
            "https://freeimage.host/api/1/upload",
            data={
                "key": "6d207e02198a847aa98d0a2a901485a5",  # public API key
                "image": image_base64,
                "format": "json",
            },
            timeout=25,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("status_code") == 200:
            url = result["image"]["url"]
            print(f"[NOTIFIER] Scene image uploaded: {url}", flush=True)
            return url
        else:
            print(f"[NOTIFIER] Image upload failed: {result}", flush=True)
            return None

    except Exception as e:
        print(f"[NOTIFIER] Image upload error: {e}", flush=True)
        return None


def build_alert_message(incident_type: str, location: str, confidence: float, scene_description: str = "") -> str:
    """
    Build a TwiML XML voice message for the alert.

    Args:
        incident_type: "Violence", "Accident", or "Weapon"
        location: System location string
        confidence: Detection confidence score (0-1)
        scene_description: Optional scene context to read out

    Returns:
        TwiML XML string
    """
    response = VoiceResponse()
    response.pause(length=1)
    response.say(
        f"Security alert. {incident_type} detected at {location}. "
        f"Confidence level {int(confidence * 100)} percent. "
        "This is an automated alert from the AI monitoring system. "
        "Please respond immediately.",
        voice="alice",
        language="en-US"
    )

    # Read out the first sentence of the scene description for immediate context
    if scene_description:
        first_sentence = scene_description.split(".")[0].strip()
        if first_sentence:
            response.pause(length=1)
            response.say(
                f"Scene report: {first_sentence}.",
                voice="alice",
                language="en-US"
            )

    response.pause(length=1)
    response.say(
        f"Repeating: {incident_type} detected at {location}. "
        "Please check the location immediately.",
        voice="alice",
        language="en-US"
    )
    return str(response)


def send_alert_call(incident_type: str, location: str, confidence: float, scene_description: str = "") -> bool:
    """
    Send a voice call alert for a detected incident.

    Args:
        incident_type: "Violence", "Accident", or "Weapon"
        location: System location
        confidence: Detection confidence (0-1)
        scene_description: Optional scene context to read out in the call

    Returns:
        True if call initiated, False if failed or disabled
    """
    try:
        client = get_twilio_client()
        if not client:
            return False

        from_number = os.getenv("TWILIO_FROM_NUMBER")
        to_number = os.getenv("TWILIO_TO_NUMBER")

        if not from_number or not to_number:
            print("[NOTIFIER] Warning: Phone numbers not configured in .env")
            return False

        twiml_body = build_alert_message(incident_type, location, confidence, scene_description)

        call = client.calls.create(twiml=twiml_body, to=to_number, from_=from_number)

        print(f"[NOTIFIER] {incident_type} alert call initiated. SID: {call.sid}", flush=True)
        return True

    except Exception as e:
        print(f"[NOTIFIER] Failed to send alert call: {e}", flush=True)
        return False


def send_alert_sms(
    incident_type: str,
    location: str,
    confidence: float,
    scene_description: str = "",
    scene_frame_base64: str = "",
) -> bool:
    """
    Send an MMS alert with the scene image + incident details.

    If an imgbb API key is configured, the scene frame is uploaded and
    attached as an MMS image. Otherwise falls back to plain SMS.

    Args:
        incident_type: "Violence", "Accident", or "Weapon"
        location: System location
        confidence: Detection confidence (0-1)
        scene_description: Detailed scene analysis text
        scene_frame_base64: Base64-encoded JPEG of the detected scene frame

    Returns:
        True if message sent, False if failed or disabled
    """
    try:
        client = get_twilio_client()
        if not client:
            return False

        from_number = os.getenv("TWILIO_FROM_NUMBER")
        to_number = os.getenv("TWILIO_TO_NUMBER")

        if not from_number or not to_number:
            print("[NOTIFIER] Warning: Phone numbers not configured in .env")
            return False

        # Build SMS text body
        confidence_percent = int(confidence * 100)
        timestamp = datetime.now().strftime("%d %b %Y  %H:%M:%S")

        message_body = (
            f"🚨 SECURITY ALERT — {incident_type.upper()}\n"
            f"📍 Location : {location}\n"
            f"🕐 Time     : {timestamp}\n"
            f"📊 Confidence: {confidence_percent}%\n"
        )

        if scene_description:
            # Trim so the full message stays under Twilio's 1600-char MMS limit
            max_desc_len = 900
            truncated = scene_description[:max_desc_len]
            if len(scene_description) > max_desc_len:
                truncated += "…"
            message_body += f"\n📋 Scene Analysis:\n{truncated}"
        else:
            message_body += f"\n{incident_type} incident detected. Check location immediately."

        # Try to attach scene image
        media_url = None
        if scene_frame_base64:
            media_url = upload_scene_image(scene_frame_base64)

        # Build Twilio message params
        msg_params = {
            "body": message_body,
            "from_": from_number,
            "to": to_number,
        }

        if media_url:
            # MMS — image attached
            msg_params["media_url"] = [media_url]
            print(f"[NOTIFIER] Sending MMS with scene image for {incident_type}...", flush=True)
        else:
            print(f"[NOTIFIER] Sending SMS (no image) for {incident_type}...", flush=True)

        message = client.messages.create(**msg_params)
        print(f"[NOTIFIER] {incident_type} alert {'MMS' if media_url else 'SMS'} sent. SID: {message.sid}", flush=True)
        return True

    except Exception as e:
        print(f"[NOTIFIER] Failed to send alert SMS/MMS: {e}", flush=True)
        return False


def trigger_alert(
    incident_type: str,
    location: str,
    confidence: float,
    scene_description: str = "",
    scene_frame_base64: str = "",
):
    """
    Trigger a full alert for a detected incident: voice call + MMS with image.

    Args:
        incident_type: "Violence", "Accident", or "Weapon"
        location: System location
        confidence: Detection confidence (0-1)
        scene_description: Detailed scene analysis text (for SMS body + voice)
        scene_frame_base64: Base64-encoded JPEG of the scene frame (for MMS image)

    Returns:
        dict with alert status
    """
    if incident_type not in ["Violence", "Accident", "Weapon"]:
        return {"status": "invalid_incident_type"}

    if confidence < 0.5:
        print(f"[NOTIFIER] Confidence {confidence} below threshold, skipping alert.", flush=True)
        return {"status": "confidence_too_low"}

    timestamp = datetime.now().isoformat(timespec="seconds")

    # Voice call (reads scene description aloud)
    call_ok = send_alert_call(incident_type, location, confidence, scene_description)

    # MMS: image + text (uploads scene frame to imgbb first)
    sms_ok = send_alert_sms(
        incident_type,
        location,
        confidence,
        scene_description,
        scene_frame_base64,
    )

    return {
        "status": "alert_sent" if (call_ok or sms_ok) else "alert_failed",
        "incident_type": incident_type,
        "location": location,
        "confidence": confidence,
        "timestamp": timestamp,
        "call_initiated": call_ok,
        "sms_sent": sms_ok,
        "image_attached": bool(scene_frame_base64),
    }
