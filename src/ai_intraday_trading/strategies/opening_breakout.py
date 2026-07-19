from __future__ import annotations

from ai_intraday_trading.config import OpeningBreakoutConfig
from ai_intraday_trading.domain.models import Candle, StrategyDecision


def evaluate_opening_breakout(
    first_candle: Candle,
    confirmation_candle: Candle,
    average_volume: float,
    previous_close: float,
    config: OpeningBreakoutConfig,
) -> StrategyDecision:
    reasons: list[str] = []

    if previous_close <= 0:
        reasons.append("Previous close is invalid.")
        return StrategyDecision(False, "opening_breakout", reasons)

    if first_candle.range_pct >= config.first_candle_max_range_pct:
        reasons.append("First candle range exceeds threshold.")

    gap_pct = (first_candle.open - previous_close) / previous_close
    if gap_pct < config.minimum_gap_pct:
        reasons.append("Gap up condition failed.")

    if confirmation_candle.ema_9 is None:
        reasons.append("EMA 9 is unavailable.")
    elif confirmation_candle.close <= confirmation_candle.ema_9:
        reasons.append("Price is not above EMA 9.")

    if average_volume <= 0:
        reasons.append("Average volume is invalid.")
    else:
        volume_multiple = confirmation_candle.volume / average_volume
        if volume_multiple < config.minimum_volume_multiple:
            reasons.append("Volume confirmation failed.")

    if reasons:
        return StrategyDecision(
            is_valid=False,
            strategy_name="opening_breakout",
            reasons=reasons,
            metadata={
                "gap_pct": gap_pct,
                "range_pct": first_candle.range_pct,
            },
        )

    entry_price = confirmation_candle.high
    stop_loss = first_candle.low
    risk_per_share = entry_price - stop_loss
    if risk_per_share <= 0:
        return StrategyDecision(
            False,
            "opening_breakout",
            ["Risk per share is invalid."],
        )

    target_price = entry_price + (risk_per_share * config.risk_reward_ratio)
    return StrategyDecision(
        is_valid=True,
        strategy_name="opening_breakout",
        reasons=["Signal validated."],
        entry_price=entry_price,
        stop_loss=stop_loss,
        target_price=target_price,
        metadata={
            "gap_pct": gap_pct,
            "range_pct": first_candle.range_pct,
        },
    )
