"""
Telegram delivery helper for farmer alerts.
"""
import asyncio
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


@dataclass
class TelegramDeliveryResult:
    """Result of a Telegram send attempt."""

    enabled: bool
    sent: bool
    status: str
    chat_id: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "sent": self.sent,
            "status": self.status,
            "chat_id": self.chat_id,
            "error": self.error,
        }


def _normalize_env_key(value: str) -> str:
    """Convert village/farmer identifiers into safe env var suffixes."""
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).upper()
    return normalized.strip("_")


def resolve_telegram_chat_id(sensor_data: Dict[str, Any]) -> Optional[str]:
    """
    Resolve the Telegram chat ID for the farmer.

    Priority:
    1. sensor_data.telegram_chat_id
    2. TELEGRAM_CHAT_ID_<FARMER_ID>
    3. TELEGRAM_CHAT_ID_<VILLAGE_ID>
    4. TELEGRAM_DEFAULT_CHAT_ID
    """
    direct_chat_id = sensor_data.get("telegram_chat_id")
    if direct_chat_id:
        return str(direct_chat_id)

    for key_name in ("farmer_id", "farmerId", "village_id"):
        identifier = sensor_data.get(key_name)
        if not identifier:
            continue

        env_key = f"TELEGRAM_CHAT_ID_{_normalize_env_key(str(identifier))}"
        chat_id = os.getenv(env_key)
        if chat_id:
            return chat_id

    return os.getenv("TELEGRAM_DEFAULT_CHAT_ID")


class TelegramNotifier:
    """Small wrapper around Telegram Bot API."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        timeout_seconds: int = 10,
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.timeout_seconds = timeout_seconds

    def is_enabled(self) -> bool:
        return bool(self.bot_token)

    async def send_message(
        self,
        text: str,
        chat_id: Optional[str],
    ) -> TelegramDeliveryResult:
        if not self.bot_token:
            return TelegramDeliveryResult(
                enabled=False,
                sent=False,
                status="disabled",
                error="TELEGRAM_BOT_TOKEN is not configured",
            )

        if not chat_id:
            return TelegramDeliveryResult(
                enabled=True,
                sent=False,
                status="missing_chat_id",
                error="No Telegram chat ID configured for this farmer or village",
            )

        url = f"{TELEGRAM_API_BASE}/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }

        try:
            response = await asyncio.to_thread(
                requests.post,
                url,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body = response.json()

            if not body.get("ok", False):
                description = body.get("description", "Telegram API returned ok=false")
                return TelegramDeliveryResult(
                    enabled=True,
                    sent=False,
                    status="failed",
                    chat_id=str(chat_id),
                    error=description,
                )

            return TelegramDeliveryResult(
                enabled=True,
                sent=True,
                status="sent",
                chat_id=str(chat_id),
            )
        except Exception as exc:
            logger.error("Telegram send failed: %s", exc)
            return TelegramDeliveryResult(
                enabled=True,
                sent=False,
                status="failed",
                chat_id=str(chat_id),
                error=str(exc),
            )


_telegram_notifier: Optional[TelegramNotifier] = None


def get_telegram_notifier() -> TelegramNotifier:
    global _telegram_notifier
    if _telegram_notifier is None:
        _telegram_notifier = TelegramNotifier()
    return _telegram_notifier


def set_telegram_notifier(notifier: Optional[TelegramNotifier]):
    global _telegram_notifier
    _telegram_notifier = notifier
