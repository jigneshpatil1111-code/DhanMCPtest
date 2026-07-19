from __future__ import annotations

from ai_intraday_trading.domain.models import BacktestSummary, BacktestTrade


def summarize_backtest(trades: list[BacktestTrade]) -> BacktestSummary:
    total_trades = len(trades)
    wins = sum(1 for trade in trades if trade.outcome == "win")
    losses = sum(1 for trade in trades if trade.outcome == "loss")
    gross_profit = sum(trade.pnl for trade in trades if trade.pnl > 0)
    gross_loss = abs(sum(trade.pnl for trade in trades if trade.pnl < 0))
    net_profit = sum(trade.pnl for trade in trades)
    win_rate = wins / total_trades if total_trades else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss else float("inf")
    expectancy = net_profit / total_trades if total_trades else 0.0

    equity = 0.0
    peak = 0.0
    max_drawdown = 0.0
    for trade in trades:
        equity += trade.pnl
        peak = max(peak, equity)
        drawdown = peak - equity
        max_drawdown = max(max_drawdown, drawdown)

    return BacktestSummary(
        total_trades=total_trades,
        wins=wins,
        losses=losses,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        net_profit=net_profit,
        win_rate=win_rate,
        profit_factor=profit_factor,
        expectancy=expectancy,
        max_drawdown=max_drawdown,
    )
