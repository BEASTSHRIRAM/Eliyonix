import json
import os
from typing import Any, Dict

import requests

TELEGRAM_API_BASE = "https://api.telegram.org"


def lambda_handler(event, context):
    """
    Generic Lambda handler for Bedrock AgentCore Gateway placeholder tool.

    Expected input:
        event: {
            # optional tool arguments
            "param_0": val0,
            "param_1": val1,
            ...
        }

    Context should contain:
        context.client_context.custom["bedrockAgentCoreToolName"]
        → e.g. "LambdaTarget___placeholder_tool"
    """
    try:
        extended_name = context.client_context.custom.get("bedrockAgentCoreToolName")
        tool_name = None

        # handle agentcore gateway tool naming convention
        # https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-tool-naming.html
        if extended_name and "___" in extended_name:
            tool_name = extended_name.split("___", 1)[1]

        if not tool_name:
            return _response(400, {"error": "Missing tool name"})

        if tool_name == "telegram_notify_farmer":
            result = telegram_notify_farmer(event)
            return _response(200, {"result": result})

        if tool_name != "placeholder_tool":
            return _response(400, {"error": f"Unknown tool '{tool_name}'"})

        result = placeholder_tool(event)
        return _response(200, {"result": result})

    except Exception as e:
        return _response(500, {"system_error": str(e)})


def _response(status_code: int, body: Dict[str, Any]):
    """Consistent JSON response wrapper."""
    return {"statusCode": status_code, "body": json.dumps(body)}


def placeholder_tool(event: Dict[str, Any]):
    """
    no-op placeholder tool.

    Demonstrates argument passing from AgentCore Gateway.
    """
    return {
        "message": "Placeholder tool executed.",
        "string_param": event.get("string_param"),
        "int_param": event.get("int_param"),
        "float_array_param": event.get("float_array_param"),
        "event_args_received": event,
    }


def telegram_notify_farmer(event: Dict[str, Any]):
    """
    Send a direct Telegram message to a farmer.

    Required:
        message: text to send
        chat_id: Telegram chat ID for the farmer or group

    Environment:
        TELEGRAM_BOT_TOKEN: Telegram bot token from BotFather
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = event.get("chat_id")
    message = event.get("message")

    if not bot_token:
        return {
            "enabled": False,
            "sent": False,
            "status": "disabled",
            "tool_name": "telegram_notify_farmer",
            "chat_id": chat_id,
            "error": "TELEGRAM_BOT_TOKEN is not configured",
        }

    if not chat_id:
        return {
            "enabled": True,
            "sent": False,
            "status": "missing_chat_id",
            "tool_name": "telegram_notify_farmer",
            "chat_id": None,
            "error": "chat_id is required",
        }

    if not message:
        return {
            "enabled": True,
            "sent": False,
            "status": "missing_message",
            "tool_name": "telegram_notify_farmer",
            "chat_id": chat_id,
            "error": "message is required",
        }

    try:
        response = requests.post(
            f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message,
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        response.raise_for_status()
        body = response.json()

        if not body.get("ok", False):
            return {
                "enabled": True,
                "sent": False,
                "status": "failed",
                "tool_name": "telegram_notify_farmer",
                "chat_id": str(chat_id),
                "error": body.get("description", "Telegram API returned ok=false"),
            }

        return {
            "enabled": True,
            "sent": True,
            "status": "sent",
            "tool_name": "telegram_notify_farmer",
            "chat_id": str(chat_id),
            "farmer_id": event.get("farmer_id"),
            "village_id": event.get("village_id"),
            "inverter_id": event.get("inverter_id"),
            "fault_type": event.get("fault_type"),
            "confidence": event.get("confidence"),
        }
    except Exception as e:
        return {
            "enabled": True,
            "sent": False,
            "status": "failed",
            "tool_name": "telegram_notify_farmer",
            "chat_id": str(chat_id),
            "error": str(e),
        }
