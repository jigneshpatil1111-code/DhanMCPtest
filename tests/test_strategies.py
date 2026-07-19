from __future__ import annotations

import unittest
from datetime import datetime

from ai_intraday_trading.config import EmaPullbackConfig, OpeningBreakoutConfig
from ai_intraday_trading.domain.models import Candle
from ai_intraday_trading.strategies.ema_pullback import evaluate_ema_pullback
from ai_intraday_trading.strategies.opening_breakout import evaluate_opening_breakout


class StrategyTests(unittest.TestCase):
    def test_opening_breakout_valid_signal(self) -> None:
        first_candle = Candle(
            symbol="ABC",
            timestamp=datetime(2026, 7, 19, 9, 15),
            open=100,
            high=100.8,
            low=100.1,
            close=100.7,
            volume=200000,
            ema_9=100.5,
        )
        current_candle = Candle(
            symbol="ABC",
            timestamp=datetime(2026, 7, 19, 9, 20),
            open=100.7,
            high=101.2,
            low=100.6,
            close=101.1,
            volume=400000,
            ema_9=100.9,
        )

        decision = evaluate_opening_breakout(
            first_candle=first_candle,
            confirmation_candle=current_candle,
            average_volume=200000,
            previous_close=99.5,
            config=OpeningBreakoutConfig(),
        )

        self.assertTrue(decision.is_valid)
        self.assertEqual(decision.strategy_name, "opening_breakout")
        self.assertIsNotNone(decision.target_price)

    def test_ema_pullback_rejects_when_vwap_fails(self) -> None:
        candle = Candle(
            symbol="XYZ",
            timestamp=datetime(2026, 7, 19, 10, 0),
            open=200,
            high=201,
            low=199.8,
            close=200.1,
            volume=150000,
            vwap=200.5,
            ema_9=200.0,
            ema_15=199.5,
        )

        decision = evaluate_ema_pullback(
            candle=candle,
            average_volume=100000,
            config=EmaPullbackConfig(),
        )

        self.assertFalse(decision.is_valid)
        self.assertIn("Price is below VWAP.", decision.reasons)


if __name__ == "__main__":
    unittest.main()
