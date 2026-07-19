from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from ai_intraday_trading.domain.models import Candle
from ai_intraday_trading.domain.models import SymbolRecord


def load_candles_from_csv(csv_path: str | Path, *, symbol: str) -> list[Candle]:
    rows: list[Candle] = []
    with Path(csv_path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            timestamp = _parse_timestamp(raw_row)
            rows.append(
                Candle(
                    symbol=symbol,
                    timestamp=timestamp,
                    open=float(raw_row["open"]),
                    high=float(raw_row["high"]),
                    low=float(raw_row["low"]),
                    close=float(raw_row["close"]),
                    volume=float(raw_row["volume"]),
                    vwap=_optional_float(raw_row.get("vwap")),
                    ema_9=_optional_float(raw_row.get("ema_9")),
                    ema_15=_optional_float(raw_row.get("ema_15")),
                    sector=raw_row.get("sector") or None,
                )
            )
    return rows


def load_symbols_from_csv(csv_path: str | Path) -> list[SymbolRecord]:
    records: list[SymbolRecord] = []
    with Path(csv_path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            records.append(
                SymbolRecord(
                    symbol=raw_row["symbol"],
                    name=raw_row.get("name") or None,
                    sector=raw_row.get("sector") or None,
                    is_active=_parse_bool(raw_row.get("is_active", "true")),
                )
            )
    return records


def _parse_timestamp(row: dict[str, str]) -> datetime:
    if row.get("timestamp"):
        return datetime.fromisoformat(row["timestamp"])
    if row.get("date") and row.get("time"):
        return datetime.fromisoformat(f"{row['date']}T{row['time']}")
    raise ValueError("CSV row must contain either 'timestamp' or both 'date' and 'time'.")


def _optional_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _parse_bool(value: str) -> bool:
    return value.strip().lower() not in {"0", "false", "no", "n"}
