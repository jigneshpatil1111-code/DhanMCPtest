from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from ai_intraday_trading.domain.models import Candle, SymbolRecord
from ai_intraday_trading.ingestion.csv_loader import load_candles_from_csv
from ai_intraday_trading.persistence.sqlite_store import SQLiteStore


class IngestionAndStorageTests(unittest.TestCase):
    def test_csv_loader_reads_candles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "candles.csv"
            csv_path.write_text(
                "timestamp,open,high,low,close,volume,vwap,ema_9,ema_15,sector\n"
                "2026-07-18T09:15:00,100,101,99.8,100.9,150000,100.5,100.4,100.2,Banking\n",
                encoding="utf-8",
            )

            candles = load_candles_from_csv(csv_path, symbol="ABC")

        self.assertEqual(len(candles), 1)
        self.assertEqual(candles[0].symbol, "ABC")
        self.assertEqual(candles[0].sector, "Banking")

    def test_sqlite_store_initializes_and_fetches_candles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "market.db"
            store = SQLiteStore(db_path)
            store.initialize()
            store.upsert_symbols([SymbolRecord(symbol="ABC", sector="Banking")])
            store.insert_candles(
                [
                    Candle(
                        symbol="ABC",
                        timestamp=datetime(2026, 7, 18, 9, 15),
                        open=100,
                        high=101,
                        low=99.8,
                        close=100.9,
                        volume=150000,
                        vwap=100.5,
                        ema_9=100.4,
                        ema_15=100.2,
                        sector="Banking",
                    )
                ]
            )

            candles = store.fetch_candles("ABC")

        self.assertEqual(len(candles), 1)
        self.assertEqual(candles[0].close, 100.9)

    def test_signal_storage_rejects_duplicate_signal_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SQLiteStore(Path(temp_dir) / "market.db")
            store.initialize()
            signal = {
                "signal_id": "ABC-opening-2026-07-20T09:20:00+05:30",
                "symbol": "ABC",
                "strategy_name": "opening_breakout",
                "entry_price": 101.0,
                "stop_loss": 99.0,
                "target_price": 105.0,
                "quantity": 10,
                "score": 2.5,
                "created_at": "2026-07-20T09:20:00+05:30",
            }

            first_insert = store.insert_signal(signal)
            second_insert = store.insert_signal(signal)
            signals = store.fetch_signals()

        self.assertTrue(first_insert)
        self.assertFalse(second_insert)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0]["symbol"], "ABC")


if __name__ == "__main__":
    unittest.main()
