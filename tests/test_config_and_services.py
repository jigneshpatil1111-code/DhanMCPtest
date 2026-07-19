from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from ai_intraday_trading.config import load_config
from ai_intraday_trading.domain.models import BacktestTrade
from ai_intraday_trading.paths import get_project_paths
from ai_intraday_trading.persistence.sqlite_store import SQLiteStore
from ai_intraday_trading.services.journal_service import JournalService
from ai_intraday_trading.services.market_data_service import MarketDataService


class ConfigAndServicesTests(unittest.TestCase):
    def test_load_config_overrides_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text(
                "[risk]\ncapital = 250000.0\nrisk_per_trade_pct = 0.02\n",
                encoding="utf-8",
            )

            config = load_config(config_path)

        self.assertEqual(config.risk.capital, 250000.0)
        self.assertEqual(config.risk.risk_per_trade_pct, 0.02)

    def test_get_project_paths_uses_work_data_layout(self) -> None:
        paths = get_project_paths(Path("C:/tmp/project-root"))
        self.assertEqual(paths.data_dir.as_posix(), "C:/tmp/project-root/work/data")
        self.assertEqual(paths.db_path.as_posix(), "C:/tmp/project-root/work/data/market.db")

    def test_market_data_service_imports_symbol_universe(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = SQLiteStore(root / "market.db")
            service = MarketDataService(store)
            service.initialize()
            csv_path = root / "symbols.csv"
            csv_path.write_text(
                "symbol,name,sector,is_active\nABC,Alpha Corp,Banking,true\nXYZ,Xylo Tech,IT,false\n",
                encoding="utf-8",
            )

            imported = service.import_symbol_universe(csv_path)
            symbols = store.list_symbols()

        self.assertEqual(imported, 2)
        self.assertEqual(len(symbols), 2)
        self.assertFalse(symbols[1].is_active)

    def test_journal_service_returns_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SQLiteStore(Path(temp_dir) / "market.db")
            store.initialize()
            store.insert_backtest_trades(
                [
                    BacktestTrade(
                        symbol="ABC",
                        strategy_name="opening_breakout",
                        entry_time=datetime(2026, 7, 19, 9, 20),
                        exit_time=datetime(2026, 7, 19, 9, 25),
                        entry_price=100.0,
                        exit_price=102.0,
                        stop_loss=99.0,
                        target_price=102.0,
                        quantity=100,
                        pnl=200.0,
                        outcome="win",
                        reasons=["Signal validated."],
                    )
                ]
            )
            service = JournalService(store)

            trades = service.list_trades()
            summary = service.summary()

        self.assertEqual(len(trades), 1)
        self.assertEqual(summary["wins"], 1)


if __name__ == "__main__":
    unittest.main()
