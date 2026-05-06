"""
MCP tool bridge for Telegram farmer notifications.
"""
import asyncio
import logging
import os
from typing import Any, Dict, Optional

from .mcp_client.client import get_streamable_http_mcp_client
from .telegram_notifier import get_telegram_notifier, resolve_telegram_chat_id

logger = logging.getLogger(__name__)

TELEGRAM_NOTIFY_TOOL_NAME = "telegram_notify_farmer"


def build_telegram_tool_args(
    sensor_data: Dict[str, Any],
    alert_message: str,
    fault_type: Optional[str],
    confidence: float,
) -> Dict[str, Any]:
    """Build the argument payload expected by the Telegram MCP tool."""
    return {
        "tool_name": TELEGRAM_NOTIFY_TOOL_NAME,
        "message": alert_message,
        "chat_id": resolve_telegram_chat_id(sensor_data),
        "farmer_id": sensor_data.get("farmer_id") or sensor_data.get("farmerId"),
        "village_id": sensor_data.get("village_id"),
        "inverter_id": sensor_data.get("inverter_id"),
        "fault_type": fault_type,
        "confidence": confidence,
    }


async def execute_telegram_notify_tool(tool_args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Telegram delivery as an MCP tool.

    If GATEWAY_URL is configured, this calls the AgentCore MCP Gateway tool.
    In local development, it uses the same tool contract with a local fallback.
    """
    if os.getenv("GATEWAY_URL"):
        try:
            return await _execute_gateway_tool(tool_args)
        except Exception as exc:
            logger.error("Telegram MCP Gateway call failed: %s", exc)
            return {
                "enabled": True,
                "sent": False,
                "status": "mcp_failed",
                "tool_name": TELEGRAM_NOTIFY_TOOL_NAME,
                "transport": "mcp_gateway",
                "chat_id": tool_args.get("chat_id"),
                "error": str(exc),
            }

    return await _execute_local_tool_contract(tool_args)


async def _execute_gateway_tool(tool_args: Dict[str, Any]) -> Dict[str, Any]:
    client = get_streamable_http_mcp_client()
    tools = await client.get_tools()
    tool = _find_tool(tools, TELEGRAM_NOTIFY_TOOL_NAME)

    if hasattr(tool, "ainvoke"):
        result = await tool.ainvoke(tool_args)
    else:
        result = await asyncio.to_thread(tool.invoke, tool_args)

    if isinstance(result, dict):
        result.setdefault("tool_name", TELEGRAM_NOTIFY_TOOL_NAME)
        result.setdefault("transport", "mcp_gateway")
        return result

    return {
        "enabled": True,
        "sent": True,
        "status": "sent",
        "tool_name": TELEGRAM_NOTIFY_TOOL_NAME,
        "transport": "mcp_gateway",
        "chat_id": tool_args.get("chat_id"),
        "raw_result": result,
    }


def _find_tool(tools: Any, expected_name: str):
    for tool in tools:
        tool_name = getattr(tool, "name", "")
        if tool_name == expected_name or tool_name.endswith(f"___{expected_name}"):
            return tool

    available = [getattr(tool, "name", "<unnamed>") for tool in tools]
    raise RuntimeError(f"MCP tool '{expected_name}' not found. Available tools: {available}")


async def _execute_local_tool_contract(tool_args: Dict[str, Any]) -> Dict[str, Any]:
    result = await get_telegram_notifier().send_message(
        text=str(tool_args.get("message", "")),
        chat_id=tool_args.get("chat_id"),
    )
    payload = result.to_dict()
    payload["tool_name"] = TELEGRAM_NOTIFY_TOOL_NAME
    payload["transport"] = "local_mcp_contract"
    return payload
