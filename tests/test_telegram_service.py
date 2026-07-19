from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from ai_intraday_trading.services.telegram_service import TelegramService


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class TelegramServiceTests(unittest.TestCase):
    def test_disabled_without_credentials(self) -> None:
        service = TelegramService(None, None)
        self.assertFalse(service.enabled)
        self.assertFalse(service.send_signal({}))

    @patch("urllib.request.urlopen", return_value=FakeResponse())
    def test_sends_signal_summary(self, mocked_urlopen) -> None:
        service = TelegramService("token", "123")
        signal = {
            "symbol": "ABC",
            "strategy_name": "opening_breakout",
            "entry_price": 101.0,
            "stop_loss": 99.0,
            "target_price": 105.0,
            "quantity": 10,
            "score": 2.5,
            "created_at": "2026-07-20T09:20:00+05:30",
        }

        delivered = service.send_signal(signal)
        request = mocked_urlopen.call_args.args[0]
        payload = json.loads(request.data)

        self.assertTrue(delivered)
        self.assertEqual(payload["chat_id"], "123")
        self.assertIn("ABC", payload["text"])
        self.assertIn("Stop Loss: 99.00", payload["text"])


if __name__ == "__main__":
    unittest.main()
