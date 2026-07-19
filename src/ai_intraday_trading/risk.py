from __future__ import annotations

import math

from ai_intraday_trading.config import RiskConfig
from ai_intraday_trading.domain.models import PositionPlan


def build_position_plan(
    *,
    symbol: str,
    entry_price: float,
    stop_loss: float,
    config: RiskConfig,
    available_balance: float | None = None,
    leverage: float | None = None,
) -> PositionPlan:
    if entry_price <= 0:
        raise ValueError("Entry price must be positive.")
    if stop_loss <= 0:
        raise ValueError("Stop loss must be positive.")
    if stop_loss >= entry_price:
        raise ValueError("Stop loss must be below entry price for a long trade.")

    cash_available = config.capital if available_balance is None else available_balance
    if cash_available <= 0:
        raise ValueError("Available balance must be positive.")

    requested_leverage = config.max_leverage if leverage is None else leverage
    effective_leverage = min(requested_leverage, config.max_leverage)
    if effective_leverage < 1:
        raise ValueError("Leverage must be at least 1x.")
    if not 0 < config.max_margin_utilization_pct <= 1:
        raise ValueError("Margin utilization must be between 0 and 1.")

    adjusted_entry = entry_price * (1 + config.assumed_slippage_pct)
    risk_per_share = adjusted_entry - stop_loss
    allowed_risk = cash_available * config.risk_per_trade_pct
    risk_quantity = math.floor(allowed_risk / risk_per_share)

    max_margin = cash_available * config.max_margin_utilization_pct
    max_notional = max_margin * effective_leverage
    exposure_quantity = math.floor(max_notional / adjusted_entry)
    quantity = min(risk_quantity, exposure_quantity)

    if quantity < 1:
        raise ValueError("Capital or risk settings do not allow even one share.")

    notional_value = quantity * adjusted_entry
    estimated_margin = notional_value / effective_leverage
    risk_amount = quantity * risk_per_share
    return PositionPlan(
        symbol=symbol,
        entry_price=adjusted_entry,
        stop_loss=stop_loss,
        quantity=quantity,
        risk_amount=risk_amount,
        capital_committed=estimated_margin,
        notional_value=notional_value,
        leverage=effective_leverage,
        estimated_margin=estimated_margin,
    )
