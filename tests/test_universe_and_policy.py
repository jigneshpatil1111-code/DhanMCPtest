from __future__ import annotations

import unittest

from ai_intraday_trading.services.execution_policy import validate_execution_candidate
from ai_intraday_trading.universe import load_nifty500_members, nifty500_symbols


class UniverseAndPolicyTests(unittest.TestCase):
    def test_official_universe_contains_exactly_500_symbols(self) -> None:
        self.assertEqual(len(load_nifty500_members()), 500)
        self.assertEqual(len(nifty500_symbols()), 500)

    def test_policy_accepts_approved_strategy_for_member(self) -> None:
        symbol = next(iter(nifty500_symbols()))
        decision = validate_execution_candidate(
            symbol=symbol,
            strategy_name="opening_breakout",
        )
        self.assertTrue(decision.allowed)

    def test_policy_rejects_symbol_outside_nifty500(self) -> None:
        decision = validate_execution_candidate(
            symbol="NOT-A-REAL-SYMBOL",
            strategy_name="opening_breakout",
        )
        self.assertFalse(decision.allowed)
        self.assertIn("Nifty 500", decision.reasons[0])

    def test_policy_rejects_unapproved_strategy(self) -> None:
        symbol = next(iter(nifty500_symbols()))
        decision = validate_execution_candidate(
            symbol=symbol,
            strategy_name="random_momentum",
        )
        self.assertFalse(decision.allowed)


if __name__ == "__main__":
    unittest.main()
