"""
Twilio-based alerts for violence, accident, and weapon detection.
Sends a voice call when an incident is confirmed.
"""

import os
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


def build_alert_message(incident_type: str, location: str, confidence: float) -> str:
    """
    Build a TwiML XML voice message for the alert.

    Args:
        incident_type: "Violence", "Accident", or "Weapon"
        location: System location string
        confidence: Detection confidence score (0-1)

    Returns:
        TwiML XML string
    """
    response = VoiceResponse()
    response.pause(length=1)
    response.say(
        f"Alert. {incident_type} detected at {location}. "
        f"Confidence level {int(confidence * 100)} percent. "
        "This is an automated alert from the AI monitoring system. "
        "Please respond immediately.",
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


def send_alert_call(incident_type: str, location: str, confidence: float) -> bool:
    """
    Send a voice call alert for a detected incident.

    Args:
        incident_type: "Violence", "Accident", or "Weapon"
        location: System location
        confidence: Detection confidence (0-1)

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

        twiml_body = build_alert_message(incident_type, location, confidence)

        call = client.calls.create(twiml=twiml_body, to=to_number, from_=from_number)

        print(f"[NOTIFIER] {incident_type} alert call initiated. SID: {call.sid}", flush=True)
        return True

    except Exception as e:
        print(f"[NOTIFIER] Failed to send alert call: {e}", flush=True)
        return False


def send_alert_sms(incident_type: str, location: str, confidence: float, scene_description: str = "") -> bool:
    """
    Send an SMS alert with incident details and scene description.

    Args:
        incident_type: "Violence", "Accident", or "Weapon"
        location: System location
        confidence: Detection confidence (0-1)
        scene_description: Detailed scene analysis

    Returns:
        True if SMS sent, False if failed or disabled
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

        # Build detailed SMS message
        confidence_percent = int(confidence * 100)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        message_body = f"SECURITY ALERT - {incident_type.upper()}\n"
        message_body += f"Time: {timestamp}\n"
        message_body += f"Location: {location}\n"
        message_body += f"Confidence: {confidence_percent}%\n\n"
        
        if scene_description:
            truncated_desc = scene_description[:900]
            message_body += f"Scene Analysis:\n{truncated_desc}"
        else:
            message_body += f"{incident_type} incident detected. Check location immediately."

        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )
        print(f"[NOTIFIER] {incident_type} alert SMS sent. SID: {message.sid}", flush=True)
        
        return True

    except Exception as e:
        print(f"[NOTIFIER] Failed to send alert SMS: {e}", flush=True)
        return False


def trigger_alert(incident_type: str, location: str, confidence: float, scene_description: str = ""):
    """
    Trigger an alert for a detected incident (voice call + SMS).

    Args:
        incident_type: "Violence", "Accident", or "Weapon"
        location: System location
        confidence: Detection confidence (0-1)
        scene_description: Detailed scene analysis text

    Returns:
        dict with alert status
    """
    if incident_type not in ["Violence", "Accident", "Weapon"]:
        return {"status": "invalid_incident_type"}

    if confidence < 0.5:
        print(f"[NOTIFIER] Confidence {confidence} below threshold, skipping alert.", flush=True)
        return {"status": "confidence_too_low"}

    timestamp = datetime.now().isoformat(timespec="seconds")
    
    # Send both voice call and SMS
    call_ok = send_alert_call(incident_type, location, confidence)
    sms_ok = send_alert_sms(incident_type, location, confidence, scene_description)

    return {
        "status": "alert_sent" if (call_ok or sms_ok) else "alert_failed",
        "incident_type": incident_type,
        "location": location,
        "confidence": confidence,
        "timestamp": timestamp,
        "call_initiated": call_ok,
        "sms_sent": sms_ok,
    }
