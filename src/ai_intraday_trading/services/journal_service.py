from __future__ import annotations

from dataclasses import asdict

from ai_intraday_trading.backtest.engine import summarize_backtest
from ai_intraday_trading.persistence.sqlite_store import SQLiteStore


class JournalService:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def list_trades(self, symbol: str | None = None) -> list[dict[str, object]]:
        trades = self.store.fetch_backtest_trades(symbol=symbol)
        return [asdict(trade) for trade in trades]

    def summary(self, symbol: str | None = None) -> dict[str, object]:
        trades = self.store.fetch_backtest_trades(symbol=symbol)
        summary = summarize_backtest(trades)
        return asdict(summary)
