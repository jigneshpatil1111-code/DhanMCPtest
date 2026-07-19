from __future__ import annotations

from ai_intraday_trading.config import AppConfig
from ai_intraday_trading.domain.models import BacktestTrade, Candle, ScanResult
from ai_intraday_trading.risk import build_position_plan
from ai_intraday_trading.scanner import ScanInput, scan_symbol


def run_intraday_backtest(
    *,
    symbol: str,
    candles: list[Candle],
    previous_close: float,
    average_volume: float,
    config: AppConfig,
) -> tuple[list[BacktestTrade], list[ScanResult]]:
    if len(candles) < 3:
        return [], []

    trades: list[BacktestTrade] = []
    scan_results: list[ScanResult] = []
    first_candle = candles[0]

    for index in range(1, len(candles) - 1):
        current_candle = candles[index]
        next_candle = candles[index + 1]
        decisions = scan_symbol(
            ScanInput(
                symbol=symbol,
                first_candle=first_candle,
                current_candle=current_candle,
                previous_close=previous_close,
                average_volume=average_volume,
            ),
            config,
        )
        scan_results.append(ScanResult(symbol=symbol, decisions=decisions))

        valid_decision = next((decision for decision in decisions if decision.is_valid), None)
        if valid_decision is None:
            continue

        if valid_decision.entry_price is None or valid_decision.stop_loss is None or valid_decision.target_price is None:
            continue

        position = build_position_plan(
            symbol=symbol,
            entry_price=valid_decision.entry_price,
            stop_loss=valid_decision.stop_loss,
            config=config.risk,
        )

        exit_price, outcome = _simulate_exit(
            next_candle=next_candle,
            stop_loss=valid_decision.stop_loss,
            target_price=valid_decision.target_price,
        )
        pnl = (exit_price - position.entry_price) * position.quantity
        trades.append(
            BacktestTrade(
                symbol=symbol,
                strategy_name=valid_decision.strategy_name,
                entry_time=current_candle.timestamp,
                exit_time=next_candle.timestamp,
                entry_price=position.entry_price,
                exit_price=exit_price,
                stop_loss=valid_decision.stop_loss,
                target_price=valid_decision.target_price,
                quantity=position.quantity,
                pnl=pnl,
                outcome=outcome,
                reasons=valid_decision.reasons,
            )
        )

    return trades, scan_results


def _simulate_exit(
    *,
    next_candle: Candle,
    stop_loss: float,
    target_price: float,
) -> tuple[float, str]:
    if next_candle.low <= stop_loss:
        return stop_loss, "loss"
    if next_candle.high >= target_price:
        return target_price, "win"
    return next_candle.close, "flat"
