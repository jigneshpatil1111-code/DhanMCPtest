from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from ai_intraday_trading.domain.models import BacktestTrade, Candle, SymbolRecord


SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS symbols (
        symbol TEXT PRIMARY KEY,
        name TEXT,
        sector TEXT,
        is_active INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ohlcv_5m (
        symbol TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        open REAL NOT NULL,
        high REAL NOT NULL,
        low REAL NOT NULL,
        close REAL NOT NULL,
        volume REAL NOT NULL,
        vwap REAL,
        ema_9 REAL,
        ema_15 REAL,
        sector TEXT,
        PRIMARY KEY (symbol, timestamp)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS backtest_trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        strategy_name TEXT NOT NULL,
        entry_time TEXT NOT NULL,
        exit_time TEXT NOT NULL,
        entry_price REAL NOT NULL,
        exit_price REAL NOT NULL,
        stop_loss REAL NOT NULL,
        target_price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        pnl REAL NOT NULL,
        outcome TEXT NOT NULL,
        reasons TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS signal_alerts (
        signal_id TEXT PRIMARY KEY,
        symbol TEXT NOT NULL,
        strategy_name TEXT NOT NULL,
        entry_price REAL NOT NULL,
        stop_loss REAL NOT NULL,
        target_price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        score REAL NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
)


class SQLiteStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            for statement in SCHEMA_STATEMENTS:
                connection.execute(statement)

    def upsert_symbols(self, symbols: list[SymbolRecord]) -> None:
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT INTO symbols (symbol, name, sector, is_active)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    name=excluded.name,
                    sector=excluded.sector,
                    is_active=excluded.is_active
                """,
                [
                    (
                        record.symbol,
                        record.name,
                        record.sector,
                        1 if record.is_active else 0,
                    )
                    for record in symbols
                ],
            )

    def insert_candles(self, candles: list[Candle]) -> None:
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO ohlcv_5m
                (symbol, timestamp, open, high, low, close, volume, vwap, ema_9, ema_15, sector)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        candle.symbol,
                        candle.timestamp.isoformat(),
                        candle.open,
                        candle.high,
                        candle.low,
                        candle.close,
                        candle.volume,
                        candle.vwap,
                        candle.ema_9,
                        candle.ema_15,
                        candle.sector,
                    )
                    for candle in candles
                ],
            )

    def fetch_candles(self, symbol: str) -> list[Candle]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT symbol, timestamp, open, high, low, close, volume, vwap, ema_9, ema_15, sector
                FROM ohlcv_5m
                WHERE symbol = ?
                ORDER BY timestamp ASC
                """,
                (symbol,),
            ).fetchall()

        return [
            Candle(
                symbol=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                open=row[2],
                high=row[3],
                low=row[4],
                close=row[5],
                volume=row[6],
                vwap=row[7],
                ema_9=row[8],
                ema_15=row[9],
                sector=row[10],
            )
            for row in rows
        ]

    def list_symbols(self) -> list[SymbolRecord]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT symbol, name, sector, is_active
                FROM symbols
                ORDER BY symbol ASC
                """
            ).fetchall()

        return [
            SymbolRecord(
                symbol=row[0],
                name=row[1],
                sector=row[2],
                is_active=bool(row[3]),
            )
            for row in rows
        ]

    def insert_backtest_trades(self, trades: list[BacktestTrade]) -> None:
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT INTO backtest_trades
                (symbol, strategy_name, entry_time, exit_time, entry_price, exit_price, stop_loss, target_price, quantity, pnl, outcome, reasons)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        trade.symbol,
                        trade.strategy_name,
                        trade.entry_time.isoformat(),
                        trade.exit_time.isoformat(),
                        trade.entry_price,
                        trade.exit_price,
                        trade.stop_loss,
                        trade.target_price,
                        trade.quantity,
                        trade.pnl,
                        trade.outcome,
                        " | ".join(trade.reasons),
                    )
                    for trade in trades
                ],
            )

    def fetch_backtest_trades(self, symbol: str | None = None) -> list[BacktestTrade]:
        query = """
            SELECT symbol, strategy_name, entry_time, exit_time, entry_price, exit_price, stop_loss, target_price, quantity, pnl, outcome, reasons
            FROM backtest_trades
        """
        params: tuple[object, ...] = ()
        if symbol is not None:
            query += " WHERE symbol = ?"
            params = (symbol,)
        query += " ORDER BY entry_time ASC"

        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()

        return [
            BacktestTrade(
                symbol=row[0],
                strategy_name=row[1],
                entry_time=datetime.fromisoformat(row[2]),
                exit_time=datetime.fromisoformat(row[3]),
                entry_price=row[4],
                exit_price=row[5],
                stop_loss=row[6],
                target_price=row[7],
                quantity=row[8],
                pnl=row[9],
                outcome=row[10],
                reasons=row[11].split(" | ") if row[11] else [],
            )
            for row in rows
        ]

    def insert_signal(self, signal: dict[str, object]) -> bool:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO signal_alerts
                (signal_id, symbol, strategy_name, entry_price, stop_loss, target_price, quantity, score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal["signal_id"],
                    signal["symbol"],
                    signal["strategy_name"],
                    signal["entry_price"],
                    signal["stop_loss"],
                    signal["target_price"],
                    signal["quantity"],
                    signal["score"],
                    signal["created_at"],
                ),
            )
            return cursor.rowcount == 1

    def fetch_signals(self, limit: int = 20) -> list[dict[str, object]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT signal_id, symbol, strategy_name, entry_price, stop_loss,
                       target_price, quantity, score, created_at
                FROM signal_alerts
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "signal_id": row[0],
                "symbol": row[1],
                "strategy_name": row[2],
                "entry_price": row[3],
                "stop_loss": row[4],
                "target_price": row[5],
                "quantity": row[6],
                "score": row[7],
                "created_at": row[8],
            }
            for row in rows
        ]
