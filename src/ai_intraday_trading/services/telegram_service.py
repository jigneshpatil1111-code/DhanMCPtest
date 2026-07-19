from __future__ import annotations

import json
import urllib.request


class TelegramService:
    def __init__(self, bot_token: str | None, chat_id: str | None) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_signal(self, signal: dict[str, object]) -> bool:
        if not self.enabled:
            return False
        message = (
            "N5 DESK SIGNAL\n"
            f"Stock: {signal['symbol']}\n"
            f"Strategy: {signal['strategy_name']}\n"
            f"Entry: {float(signal['entry_price']):.2f}\n"
            f"Stop Loss: {float(signal['stop_loss']):.2f}\n"
            f"Target: {float(signal['target_price']):.2f}\n"
            f"Quantity: {int(signal['quantity'])}\n"
            f"Score: {float(signal['score']):.2f}\n"
            f"Time: {signal['created_at']}\n\n"
            "Signal only. Verify in Dhan before placing any order."
        )
        body = json.dumps({"chat_id": self.chat_id, "text": message}).encode("utf-8")
        request = urllib.request.Request(
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300
