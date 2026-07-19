from __future__ import annotations

import unittest
from datetime import datetime

from ai_intraday_trading.config import AppConfig
from ai_intraday_trading.domain.models import Candle
from ai_intraday_trading.services.backtest_service import run_intraday_backtest


class BacktestServiceTests(unittest.TestCase):
    def test_backtest_service_generates_trade_for_valid_breakout(self) -> None:
        candles = [
            Candle(
                symbol="ABC",
                timestamp=datetime(2026, 7, 18, 9, 15),
                open=100.0,
                high=100.8,
                low=100.1,
                close=100.7,
                volume=200000,
                ema_9=100.5,
                ema_15=100.3,
                vwap=100.6,
            ),
            Candle(
                symbol="ABC",
                timestamp=datetime(2026, 7, 18, 9, 20),
                open=100.7,
                high=101.2,
                low=100.6,
                close=101.0,
                volume=400000,
                ema_9=100.8,
                ema_15=100.4,
                vwap=100.8,
            ),
            Candle(
                symbol="ABC",
                timestamp=datetime(2026, 7, 18, 9, 25),
                open=101.0,
                high=102.5,
                low=100.9,
                close=102.1,
                volume=350000,
                ema_9=101.0,
                ema_15=100.6,
                vwap=101.2,
            ),
        ]

        trades, scan_results = run_intraday_backtest(
            symbol="ABC",
            candles=candles,
            previous_close=99.5,
            average_volume=200000,
            config=AppConfig(),
        )

        self.assertEqual(len(scan_results), 1)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].outcome, "flat")
        self.assertGreater(trades[0].quantity, 0)


if __name__ == "__main__":
    unittest.main()
