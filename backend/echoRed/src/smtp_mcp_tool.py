"""
MCP tool contract for SMTP farmer notifications.
"""
import asyncio
import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

SMTP_NOTIFY_TOOL_NAME = "smtp_notify_farmer"


def _normalize_env_key(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value.strip()).upper().strip("_")


def resolve_farmer_email(sensor_data: Dict[str, Any]) -> Optional[str]:
    direct_email = sensor_data.get("farmer_email") or sensor_data.get("farmerEmail")
    if direct_email:
        return str(direct_email)

    for key_name in ("farmer_id", "farmerId", "village_id"):
        identifier = sensor_data.get(key_name)
        if not identifier:
            continue

        env_key = f"FARMER_EMAIL_{_normalize_env_key(str(identifier))}"
        email = os.getenv(env_key)
        if email:
            return email

    return os.getenv("FARMER_DEFAULT_EMAIL")


def build_smtp_tool_args(
    sensor_data: Dict[str, Any],
    alert_message: str,
    fault_type: Optional[str],
    confidence: float,
) -> Dict[str, Any]:
    return {
        "tool_name": SMTP_NOTIFY_TOOL_NAME,
        "to_email": resolve_farmer_email(sensor_data),
        "subject": f"VidyutSeva Alert: {fault_type or 'Fault detected'}",
        "message": alert_message,
        "farmer_id": sensor_data.get("farmer_id") or sensor_data.get("farmerId"),
        "village_id": sensor_data.get("village_id"),
        "inverter_id": sensor_data.get("inverter_id"),
        "fault_type": fault_type,
        "confidence": confidence,
    }


async def execute_smtp_notify_tool(tool_args: Dict[str, Any]) -> Dict[str, Any]:
    return await asyncio.to_thread(_send_email, tool_args)


def _send_email(tool_args: Dict[str, Any]) -> Dict[str, Any]:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL") or username
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")

    to_email = tool_args.get("to_email")
    message_text = tool_args.get("message")

    if not host or not from_email:
        return _result(False, "disabled", to_email, "SMTP_HOST and SMTP_FROM_EMAIL/SMTP_USERNAME are required")

    if not to_email:
        return _result(False, "missing_email", None, "No farmer email configured")

    if not message_text:
        return _result(False, "missing_message", to_email, "message is required")

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = str(to_email)
    msg["Subject"] = str(tool_args.get("subject") or "VidyutSeva Alert")
    msg.set_content(str(message_text))

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            if use_tls:
                server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(msg)

        result = _result(True, "sent", str(to_email), None)
        result.update({
            "farmer_id": tool_args.get("farmer_id"),
            "village_id": tool_args.get("village_id"),
            "inverter_id": tool_args.get("inverter_id"),
            "fault_type": tool_args.get("fault_type"),
            "confidence": tool_args.get("confidence"),
        })
        return result
    except Exception as exc:
        logger.error("SMTP send failed: %s", exc)
        return _result(False, "failed", str(to_email), str(exc))


def _result(sent: bool, status: str, to_email: Optional[str], error: Optional[str]) -> Dict[str, Any]:
    return {
        "enabled": True,
        "sent": sent,
        "status": status,
        "tool_name": SMTP_NOTIFY_TOOL_NAME,
        "transport": "smtp",
        "to_email": to_email,
        "error": error,
    }
