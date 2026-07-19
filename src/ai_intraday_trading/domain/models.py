from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass(slots=True)
class Candle:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float | None = None
    ema_9: float | None = None
    ema_15: float | None = None
    sector: str | None = None

    @property
    def range_pct(self) -> float:
        if self.open == 0:
            return 0.0
        return (self.high - self.low) / self.open


@dataclass(slots=True)
class StrategyDecision:
    is_valid: bool
    strategy_name: str
    reasons: list[str] = field(default_factory=list)
    entry_price: float | None = None
    stop_loss: float | None = None
    target_price: float | None = None
    metadata: dict[str, float | str | bool] = field(default_factory=dict)


@dataclass(slots=True)
class PositionPlan:
    symbol: str
    entry_price: float
    stop_loss: float
    quantity: int
    risk_amount: float
    capital_committed: float


@dataclass(slots=True)
class BacktestTrade:
    symbol: str
    strategy_name: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    stop_loss: float
    target_price: float
    quantity: int
    pnl: float
    outcome: Literal["win", "loss", "flat"]
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BacktestSummary:
    total_trades: int
    wins: int
    losses: int
    gross_profit: float
    gross_loss: float
    net_profit: float
    win_rate: float
    profit_factor: float
    expectancy: float
    max_drawdown: float


@dataclass(slots=True)
class ScanResult:
    symbol: str
    decisions: list[StrategyDecision]


@dataclass(slots=True)
class SymbolRecord:
    symbol: str
    name: str | None = None
    sector: str | None = None
    is_active: bool = True
