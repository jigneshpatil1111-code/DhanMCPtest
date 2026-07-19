from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

from ai_intraday_trading.brokers.dhan_api import DhanApiClient, DhanApiError
from ai_intraday_trading.config import RiskConfig
from ai_intraday_trading.domain.models import StrategyDecision, TradeProposal
from ai_intraday_trading.risk import build_position_plan
from ai_intraday_trading.services.execution_policy import validate_execution_candidate


def prepare_trade_proposal(
    *,
    symbol: str,
    security_id: str,
    decision: StrategyDecision,
    available_balance: float,
    risk_config: RiskConfig,
    broker_leverage: float | None = None,
) -> TradeProposal:
    if not decision.is_valid:
        raise ValueError("Only a validated strategy decision can become a proposal.")
    if decision.entry_price is None or decision.stop_loss is None or decision.target_price is None:
        raise ValueError("Entry, stop loss, and target are required.")
    if not security_id.strip().isdigit():
        raise ValueError("A numeric Dhan security ID is required.")

    policy = validate_execution_candidate(
        symbol=symbol,
        strategy_name=decision.strategy_name,
        transaction_type="BUY",
        product_type="INTRADAY",
    )
    if not policy.allowed:
        raise ValueError(" ".join(policy.reasons))

    position = build_position_plan(
        symbol=policy.symbol,
        entry_price=decision.entry_price,
        stop_loss=decision.stop_loss,
        config=risk_config,
        available_balance=available_balance,
        leverage=broker_leverage,
    )
    correlation_id = f"algo-{uuid4().hex[:12]}"
    return TradeProposal(
        correlation_id=correlation_id,
        approval_code=correlation_id,
        symbol=policy.symbol,
        security_id=security_id.strip(),
        strategy_name=decision.strategy_name,
        entry_price=round(decision.entry_price, 2),
        stop_loss=round(decision.stop_loss, 2),
        target_price=round(decision.target_price, 2),
        quantity=position.quantity,
        risk_amount=round(position.risk_amount, 2),
        notional_value=round(position.notional_value, 2),
        estimated_margin=round(position.estimated_margin, 2),
        leverage_cap=position.leverage,
    )


def build_margin_request(proposal: TradeProposal, dhan_client_id: str) -> dict[str, object]:
    return {
        "dhanClientId": dhan_client_id,
        "exchangeSegment": proposal.exchange_segment,
        "transactionType": proposal.transaction_type,
        "quantity": proposal.quantity,
        "productType": proposal.product_type,
        "securityId": proposal.security_id,
        "price": proposal.entry_price,
        "triggerPrice": 0,
    }


def build_super_order_payload(
    proposal: TradeProposal,
    dhan_client_id: str,
) -> dict[str, object]:
    return {
        "dhanClientId": dhan_client_id,
        "correlationId": proposal.correlation_id,
        "transactionType": proposal.transaction_type,
        "exchangeSegment": proposal.exchange_segment,
        "productType": proposal.product_type,
        "orderType": proposal.order_type,
        "securityId": proposal.security_id,
        "quantity": proposal.quantity,
        "price": proposal.entry_price,
        "targetPrice": proposal.target_price,
        "stopLossPrice": proposal.stop_loss,
        "trailingJump": 0,
    }


def validate_broker_margin(
    proposal: TradeProposal,
    margin_response: dict[str, object],
    available_balance: float,
) -> None:
    required = float(margin_response.get("totalMargin", 0) or 0)
    insufficient = float(margin_response.get("insufficientBalance", 0) or 0)
    broker_leverage = float(margin_response.get("leverage", 1) or 1)
    if required <= 0:
        raise ValueError("Broker did not return a valid margin requirement.")
    if insufficient > 0 or required > available_balance:
        raise ValueError("Dhan reports insufficient balance for this order.")
    if broker_leverage > proposal.leverage_cap:
        raise ValueError("Broker leverage exceeds the configured safety cap.")


def execute_approved_super_order(
    client: DhanApiClient,
    proposal: TradeProposal,
    confirmation_phrase: str,
) -> dict[str, object]:
    if not client.config.client_id:
        raise DhanApiError("DHAN_CLIENT_ID is missing.")
    if confirmation_phrase != proposal.confirmation_phrase:
        raise DhanApiError("Exact action-time confirmation phrase is required.")
    payload = build_super_order_payload(proposal, client.config.client_id)
    return client.place_super_order(
        payload,
        confirmation_phrase=f"PLACE {proposal.correlation_id}",
    )


def proposal_summary(proposal: TradeProposal) -> dict[str, object]:
    summary = asdict(proposal)
    summary["confirmation_phrase"] = proposal.confirmation_phrase
    summary["live_order_submitted"] = False
    return summary
