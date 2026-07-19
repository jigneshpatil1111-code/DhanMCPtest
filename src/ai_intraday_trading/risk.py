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
) -> PositionPlan:
    if entry_price <= 0:
        raise ValueError("Entry price must be positive.")
    if stop_loss <= 0:
        raise ValueError("Stop loss must be positive.")
    if stop_loss >= entry_price:
        raise ValueError("Stop loss must be below entry price for a long trade.")

    adjusted_entry = entry_price * (1 + config.assumed_slippage_pct)
    risk_per_share = adjusted_entry - stop_loss
    allowed_risk = config.capital * config.risk_per_trade_pct
    quantity = math.floor(allowed_risk / risk_per_share)

    if quantity < 1:
        raise ValueError("Capital or risk settings do not allow even one share.")

    capital_committed = quantity * adjusted_entry
    if capital_committed > config.capital:
        quantity = math.floor(config.capital / adjusted_entry)
        if quantity < 1:
            raise ValueError("Capital is insufficient for the trade.")
        capital_committed = quantity * adjusted_entry

    risk_amount = quantity * risk_per_share
    return PositionPlan(
        symbol=symbol,
        entry_price=adjusted_entry,
        stop_loss=stop_loss,
        quantity=quantity,
        risk_amount=risk_amount,
        capital_committed=capital_committed,
    )
