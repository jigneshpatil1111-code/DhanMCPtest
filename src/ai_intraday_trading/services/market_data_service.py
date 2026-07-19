from __future__ import annotations

from pathlib import Path

from ai_intraday_trading.ingestion.csv_loader import load_candles_from_csv, load_symbols_from_csv
from ai_intraday_trading.persistence.sqlite_store import SQLiteStore


class MarketDataService:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def initialize(self) -> None:
        self.store.initialize()

    def import_symbol_universe(self, csv_path: str | Path) -> int:
        records = load_symbols_from_csv(csv_path)
        self.store.upsert_symbols(records)
        return len(records)

    def import_candles(self, csv_path: str | Path, *, symbol: str) -> int:
        candles = load_candles_from_csv(csv_path, symbol=symbol)
        self.store.insert_candles(candles)
        return len(candles)
