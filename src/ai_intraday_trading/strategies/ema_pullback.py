from __future__ import annotations

from ai_intraday_trading.config import EmaPullbackConfig
from ai_intraday_trading.domain.models import Candle, StrategyDecision


def evaluate_ema_pullback(
    candle: Candle,
    average_volume: float,
    config: EmaPullbackConfig,
) -> StrategyDecision:
    reasons: list[str] = []

    if candle.ema_9 is None or candle.ema_15 is None:
        reasons.append("EMA values are unavailable.")
        return StrategyDecision(False, "ema_pullback", reasons)

    if candle.ema_9 <= candle.ema_15:
        reasons.append("Fast EMA is not above slow EMA.")

    if average_volume <= 0:
        reasons.append("Average volume is invalid.")
    else:
        volume_multiple = candle.volume / average_volume
        if volume_multiple < config.minimum_volume_multiple:
            reasons.append("Volume confirmation failed.")

    if config.require_vwap_alignment:
        if candle.vwap is None:
            reasons.append("VWAP is unavailable.")
        elif candle.close < candle.vwap:
            reasons.append("Price is below VWAP.")

    distance_from_ema = abs(candle.close - candle.ema_9) / candle.ema_9
    if distance_from_ema > config.pullback_tolerance_pct:
        reasons.append("Price is too far from EMA 9 for a pullback entry.")

    if candle.low > candle.ema_9:
        reasons.append("No pullback touch near EMA 9 was observed.")

    if reasons:
        return StrategyDecision(
            is_valid=False,
            strategy_name="ema_pullback",
            reasons=reasons,
            metadata={"distance_from_ema": distance_from_ema},
        )

    entry_price = candle.high
    stop_loss = min(candle.low, candle.ema_15)
    risk_per_share = entry_price - stop_loss
    if risk_per_share <= 0:
        return StrategyDecision(False, "ema_pullback", ["Risk per share is invalid."])

    target_price = entry_price + (risk_per_share * config.risk_reward_ratio)
    return StrategyDecision(
        is_valid=True,
        strategy_name="ema_pullback",
        reasons=["Signal validated."],
        entry_price=entry_price,
        stop_loss=stop_loss,
        target_price=target_price,
        metadata={"distance_from_ema": distance_from_ema},
    )
