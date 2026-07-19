from __future__ import annotations

import unittest

from ai_intraday_trading.brokers.dhan_api import DhanApiClient, DhanApiError
from ai_intraday_trading.config import DhanApiConfig, RiskConfig
from ai_intraday_trading.domain.models import StrategyDecision
from ai_intraday_trading.risk import build_position_plan
from ai_intraday_trading.services.execution_service import (
    build_margin_request,
    build_super_order_payload,
    execute_approved_super_order,
    prepare_trade_proposal,
    validate_broker_margin,
)


class ExecutionServiceTests(unittest.TestCase):
    def _proposal(self):
        return prepare_trade_proposal(
            symbol="RELIANCE",
            security_id="2885",
            decision=StrategyDecision(
                is_valid=True,
                strategy_name="opening_breakout",
                entry_price=100.0,
                stop_loss=99.0,
                target_price=102.0,
            ),
            available_balance=500.0,
            risk_config=RiskConfig(),
            broker_leverage=5.0,
        )

    def test_position_plan_caps_gross_exposure_at_five_x(self) -> None:
        config = RiskConfig(risk_per_trade_pct=1.0, max_leverage=5.0)
        plan = build_position_plan(
            symbol="RELIANCE",
            entry_price=100.0,
            stop_loss=99.0,
            config=config,
            available_balance=500.0,
            leverage=20.0,
        )
        self.assertEqual(plan.leverage, 5.0)
        self.assertLessEqual(plan.notional_value, 500.0 * 0.95 * 5.0)
        self.assertLessEqual(plan.estimated_margin, 500.0 * 0.95)

    def test_proposal_contains_entry_stop_target_and_intraday_payload(self) -> None:
        proposal = self._proposal()
        payload = build_super_order_payload(proposal, "1101976114")
        margin_payload = build_margin_request(proposal, "1101976114")

        self.assertEqual(payload["productType"], "INTRADAY")
        self.assertEqual(payload["targetPrice"], 102.0)
        self.assertEqual(payload["stopLossPrice"], 99.0)
        self.assertEqual(margin_payload["securityId"], "2885")
        self.assertGreater(proposal.quantity, 0)

    def test_margin_validation_rejects_insufficient_balance(self) -> None:
        proposal = self._proposal()
        with self.assertRaisesRegex(ValueError, "insufficient"):
            validate_broker_margin(
                proposal,
                {
                    "totalMargin": 700,
                    "insufficientBalance": 200,
                    "leverage": "5.00",
                },
                500,
            )

    def test_live_order_is_disabled_by_default(self) -> None:
        proposal = self._proposal()
        client = DhanApiClient(
            DhanApiConfig(
                access_token="test-token",
                client_id="1101976114",
                live_orders_enabled=False,
            )
        )
        with self.assertRaisesRegex(DhanApiError, "disabled"):
            execute_approved_super_order(client, proposal, proposal.confirmation_phrase)

    def test_exact_confirmation_phrase_is_required(self) -> None:
        proposal = self._proposal()
        client = DhanApiClient(
            DhanApiConfig(
                access_token="test-token",
                client_id="1101976114",
                live_orders_enabled=True,
            )
        )
        with self.assertRaisesRegex(DhanApiError, "Exact"):
            execute_approved_super_order(client, proposal, "YES")


if __name__ == "__main__":
    unittest.main()
