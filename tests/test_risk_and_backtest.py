from __future__ import annotations

import unittest
from datetime import datetime

from ai_intraday_trading.backtest.engine import summarize_backtest
from ai_intraday_trading.config import RiskConfig
from ai_intraday_trading.domain.models import BacktestTrade
from ai_intraday_trading.risk import build_position_plan


class RiskAndBacktestTests(unittest.TestCase):
    def test_position_plan_respects_capital_and_risk(self) -> None:
        plan = build_position_plan(
            symbol="ABC",
            entry_price=100.0,
            stop_loss=98.0,
            config=RiskConfig(capital=100000.0, risk_per_trade_pct=0.01),
        )

        self.assertGreater(plan.quantity, 0)
        self.assertLessEqual(plan.capital_committed, 100000.0)
        self.assertLessEqual(plan.risk_amount, 1000.0 + 1e-6)

    def test_backtest_summary_calculates_profit_factor(self) -> None:
        trades = [
            BacktestTrade(
                symbol="ABC",
                strategy_name="opening_breakout",
                entry_time=datetime(2026, 7, 19, 9, 20),
                exit_time=datetime(2026, 7, 19, 9, 45),
                entry_price=100,
                exit_price=104,
                stop_loss=98,
                target_price=104,
                quantity=100,
                pnl=400,
                outcome="win",
            ),
            BacktestTrade(
                symbol="XYZ",
                strategy_name="ema_pullback",
                entry_time=datetime(2026, 7, 19, 10, 0),
                exit_time=datetime(2026, 7, 19, 10, 15),
                entry_price=200,
                exit_price=198,
                stop_loss=198,
                target_price=204,
                quantity=100,
                pnl=-200,
                outcome="loss",
            ),
        ]

        summary = summarize_backtest(trades)

        self.assertEqual(summary.total_trades, 2)
        self.assertEqual(summary.wins, 1)
        self.assertEqual(summary.losses, 1)
        self.assertEqual(summary.net_profit, 200)
        self.assertAlmostEqual(summary.profit_factor, 2.0)


if __name__ == "__main__":
    unittest.main()
