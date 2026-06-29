"""
ACIP-X1 — Real SMS Notifications via Twilio (Day 18 / C4 extension)

This sends ACTUAL text messages through Twilio's API when a crash is
detected — to the vehicle's emergency contacts and to nearby phones
(NearbyDevice) within the 1km radius. This is separate from, and sits
on top of, the simulated "contacts_notified" / "nearby_vehicles_alerted"
records that accident_service.py already builds and stores — those
records remain the source of truth for what the dashboard displays;
this module's only job is to additionally fire the same information out
as real SMS, best-effort.

Trial-account reality check:
  - Twilio trial accounts can only send to phone numbers that have been
    manually verified in the Twilio console (Verified Caller IDs).
  - Every message will be prefixed with "Sent from your Twilio trial
    account" — that's added by Twilio itself, not something we control.
  - If a number isn't verified, or credentials/network aren't available,
    the send fails gracefully — it's logged and skipped, never raised,
    so a missing SMS gateway can never block crash detection or the
    rest of the response pipeline from working.

WhatsApp fallback (added when SMS delivery proved unreliable):
  - If SMS fails for a recipient, we automatically try WhatsApp via
    Twilio's WhatsApp Sandbox as a second attempt for that same person.
  - Real constraint, not something code can route around: each
    recipient must first send a "join <code>" message to Twilio's
    shared sandbox number (shown in your Twilio Console under
    Messaging → Try it out → Send a WhatsApp message) ONE TIME before
    they can receive anything from it. Until they do that, WhatsApp
    sends to them will also fail — which is expected, not a bug.
  - The sandbox is for testing/demo use, not production — exactly the
    right fit for a 30-day demo project.

Configuration is read from environment variables (.env file), never
hardcoded:
    TWILIO_ACCOUNT_SID
    TWILIO_AUTH_TOKEN
    TWILIO_FROM_NUMBER
    TWILIO_WHATSAPP_FROM   (e.g. "whatsapp:+14155238886" — the Sandbox
                             number shown in your Twilio Console)
    SMS_ENABLED          ("true"/"false" — lets you demo without
                           actually sending/spending trial credit)
    WHATSAPP_ENABLED     ("true"/"false" — separate toggle, so you can
                           enable WhatsApp fallback independently of SMS)
"""
import os
import logging

logger = logging.getLogger("acip.sms")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # if python-dotenv isn't installed, env vars can still be set another way

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")  # Twilio's shared Sandbox number
SMS_ENABLED = os.getenv("SMS_ENABLED", "false").lower() == "true"
WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"

_client = None


def _get_client():
    """Lazily creates the Twilio client only when actually needed."""
    global _client
    if _client is not None:
        return _client

    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER):
        logger.warning("SMS not configured — missing TWILIO_ACCOUNT_SID/AUTH_TOKEN/FROM_NUMBER in .env")
        return None

    try:
        from twilio.rest import Client
        _client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        return _client
    except ImportError:
        logger.warning("twilio package not installed — run: pip install twilio")
        return None


def _normalize_number(phone: str) -> str:
    """
    Converts a stored number like '9148732715' or '+91-9148732715' into
    the E.164 format Twilio requires, e.g. '+919148732715'. Assumes
    India (+91) for any 10-digit number with no country code, since
    that's this project's context — adjust if contacts use other
    country codes.
    """
    digits = "".join(c for c in phone if c.isdigit())
    if phone.strip().startswith("+"):
        return "+" + digits
    if len(digits) == 10:
        return "+91" + digits
    return "+" + digits


def _build_alert_body(severity: str, gps_lat: float, gps_lon: float, distance_km: float = None) -> str:
    maps_link = f"https://maps.google.com/?q={gps_lat},{gps_lon}"
    distance_line = f"\nDistance from you: ~{distance_km} km" if distance_km is not None else ""
    return (
        f"ACIP-X1 ALERT: {severity} accident detected.\n"
        f"Location: {maps_link}{distance_line}\n"
        f"This is an automated alert from ACIP-X1."
    )


def send_whatsapp_message(to_phone: str, recipient_name: str, severity: str,
                           gps_lat: float, gps_lon: float, distance_km: float = None) -> dict:
    """
    Sends the same crash alert via Twilio's WhatsApp Sandbox. Real
    constraint: the recipient must have already sent a "join <code>"
    message to the Sandbox number once — until they do, this will fail
    with a real Twilio error (not a bug, just the opt-in requirement),
    which gets recorded here exactly like any other failure.
    """
    result = {"to": to_phone, "recipient": recipient_name, "sent": False, "reason": None, "channel": "whatsapp"}

    if not WHATSAPP_ENABLED:
        result["reason"] = "WHATSAPP_ENABLED is false in .env"
        return result

    client = _get_client()
    if client is None:
        result["reason"] = "Twilio not configured"
        return result

    body = _build_alert_body(severity, gps_lat, gps_lon, distance_km)

    try:
        to_number = _normalize_number(to_phone)
        message = client.messages.create(
            body=body,
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
        )
        result["sent"] = True
        result["sid"] = message.sid
        result["status"] = message.status
        logger.info(f"WhatsApp sent to {recipient_name} ({to_number}) — SID {message.sid}")
    except Exception as e:
        result["reason"] = str(e)
        logger.error(f"WhatsApp failed for {recipient_name} ({to_phone}): {e}")

    return result


def send_crash_sms(to_phone: str, recipient_name: str, severity: str,
                    gps_lat: float, gps_lon: float, distance_km: float = None) -> dict:
    """
    Sends one real SMS for a detected crash. Returns a dict describing
    what happened (sent / skipped / failed) — never raises, so a bad
    number or network hiccup can't break the rest of the accident
    response pipeline.

    If SMS fails AND WhatsApp fallback is enabled, automatically tries
    WhatsApp as a second attempt for the same recipient — the result
    includes both attempts so it's clear which channel (if any) reached
    them.
    """
    result = {"to": to_phone, "recipient": recipient_name, "sent": False, "reason": None, "channel": "sms"}

    if not SMS_ENABLED:
        result["reason"] = "SMS_ENABLED is false in .env"
    else:
        client = _get_client()
        if client is None:
            result["reason"] = "Twilio not configured"
        else:
            body = _build_alert_body(severity, gps_lat, gps_lon, distance_km)
            try:
                to_number = _normalize_number(to_phone)
                message = client.messages.create(
                    body=body,
                    from_=TWILIO_FROM_NUMBER,
                    to=to_number,
                )
                result["sent"] = True
                result["sid"] = message.sid
                result["status"] = message.status
                logger.info(f"SMS sent to {recipient_name} ({to_number}) — SID {message.sid}")
            except Exception as e:
                result["reason"] = str(e)
                logger.error(f"SMS failed for {recipient_name} ({to_phone}): {e}")

    if not result["sent"] and WHATSAPP_ENABLED:
        whatsapp_result = send_whatsapp_message(to_phone, recipient_name, severity, gps_lat, gps_lon, distance_km)
        result["whatsapp_fallback"] = whatsapp_result
        if whatsapp_result["sent"]:
            result["sent"] = True
            result["delivered_via"] = "whatsapp"

    return result


def send_crash_alerts(contacts_notified: list, nearby_alerted: list,
                       severity: str, gps_lat: float, gps_lon: float) -> dict:
    """
    Sends real SMS to every emergency contact and every nearby phone
    from the records accident_service.py already built. Returns a
    summary of what was actually sent vs skipped/failed, which gets
    stored alongside the simulated notification records so the
    dashboard can show real delivery status, not just "would notify."
    """
    sent_results = []

    for c in contacts_notified:
        sent_results.append(
            send_crash_sms(c["phone"], c["name"], severity, gps_lat, gps_lon)
        )

    for a in nearby_alerted:
        if a.get("type") == "phone":
            sent_results.append(
                send_crash_sms(a["phone"], a["name"], severity, gps_lat, gps_lon, a.get("distance_km"))
            )

    return {
        "sms_enabled": SMS_ENABLED,
        "whatsapp_enabled": WHATSAPP_ENABLED,
        "total_attempted": len(sent_results),
        "total_sent": sum(1 for r in sent_results if r["sent"]),
        "total_sent_via_sms": sum(1 for r in sent_results if r["sent"] and r.get("delivered_via") != "whatsapp"),
        "total_sent_via_whatsapp": sum(1 for r in sent_results if r.get("delivered_via") == "whatsapp"),
        "results": sent_results,
    }