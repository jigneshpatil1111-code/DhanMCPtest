from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from ai_intraday_trading.config import AppConfig
from ai_intraday_trading.services.angel_market_data import (
    AngelInstrument,
    AngelTick,
    LiveCandleScanner,
    parse_angel_tick,
)


IST = ZoneInfo("Asia/Kolkata")


class AngelMarketDataTests(unittest.TestCase):
    def test_parses_quote_prices_from_paise(self) -> None:
        tick = parse_angel_tick(
            {
                "token": "3045",
                "exchange_timestamp": 1784605500000,
                "last_traded_price": 12345,
                "average_traded_price": 12300,
                "volume_trade_for_the_day": 2500,
                "closed_price": 12000,
            }
        )

        self.assertIsNotNone(tick)
        assert tick is not None
        self.assertEqual(tick.price, 123.45)
        self.assertEqual(tick.vwap, 123.0)
        self.assertEqual(tick.previous_close, 120.0)

    def test_rollover_finalizes_previous_candle_before_new_tick(self) -> None:
        scanner = LiveCandleScanner(
            AppConfig(),
            {"3045": AngelInstrument(symbol="SBIN", token="3045")},
            lambda signal: None,
        )
        scanner.on_tick(
            AngelTick("3045", datetime(2026, 7, 21, 9, 15, tzinfo=IST), 100, 10, 100, 99)
        )
        scanner.on_tick(
            AngelTick("3045", datetime(2026, 7, 21, 9, 20, tzinfo=IST), 101, 15, 100.5, 99)
        )

        history = list(scanner.history["SBIN"])
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].timestamp.minute, 15)
        self.assertEqual(scanner.active["SBIN"].timestamp.minute, 20)
        self.assertEqual(scanner.active["SBIN"].open, 101)


if __name__ == "__main__":
    unittest.main()
