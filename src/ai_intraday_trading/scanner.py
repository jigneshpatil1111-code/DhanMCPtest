from __future__ import annotations

from dataclasses import dataclass

from ai_intraday_trading.config import AppConfig
from ai_intraday_trading.domain.models import Candle, StrategyDecision
from ai_intraday_trading.strategies.ema_pullback import evaluate_ema_pullback
from ai_intraday_trading.strategies.opening_breakout import evaluate_opening_breakout


@dataclass(slots=True)
class ScanInput:
    symbol: str
    first_candle: Candle
    current_candle: Candle
    previous_close: float
    average_volume: float


def scan_symbol(scan_input: ScanInput, config: AppConfig) -> list[StrategyDecision]:
    return [
        evaluate_opening_breakout(
            first_candle=scan_input.first_candle,
            confirmation_candle=scan_input.current_candle,
            average_volume=scan_input.average_volume,
            previous_close=scan_input.previous_close,
            config=config.opening_breakout,
        ),
        evaluate_ema_pullback(
            candle=scan_input.current_candle,
            average_volume=scan_input.average_volume,
            config=config.ema_pullback,
        ),
    ]
