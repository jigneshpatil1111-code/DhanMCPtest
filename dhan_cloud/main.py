from __future__ import annotations

import csv
import io
import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, time as clock_time
from zoneinfo import ZoneInfo

import requests
from dhanhq import DhanContext, dhanhq


CLIENT_ID = "{{CLIENT_ID}}"
ACCESS_TOKEN = "{{ACCESS_TOKEN}}"

NIFTY_500_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
DHAN_MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master-detailed.csv"
IST = ZoneInfo("Asia/Kolkata")

SCAN_INTERVAL_SECONDS = 2
CANDLE_MINUTES = 5
MAX_OPEN_POSITIONS = 3
RISK_PER_TRADE = 0.01
DAILY_LOSS_LIMIT = 0.03
MAX_LEVERAGE = 5.0
MAX_MARGIN_UTILIZATION = 0.95
RISK_REWARD = 2.0


@dataclass(slots=True)
class Candle:
    bucket: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float | None

    @property
    def range_pct(self) -> float:
        return (self.high - self.low) / self.open if self.open > 0 else 0.0


@dataclass(slots=True)
class Signal:
    symbol: str
    security_id: str
    strategy: str
    entry: float
    stop: float
    target: float
    score: float


def download_csv(url: str) -> list[dict[str, str]]:
    response = requests.get(url, timeout=30, headers={"User-Agent": "DhanCloudStrategy/1.0"})
    response.raise_for_status()
    return list(csv.DictReader(io.StringIO(response.text)))


def build_universe() -> dict[str, str]:
    constituents = download_csv(NIFTY_500_URL)
    by_isin = {
        row.get("ISIN Code", "").strip(): row.get("Symbol", "").strip().upper()
        for row in constituents
        if row.get("Series", "").strip().upper() == "EQ"
    }
    if len(by_isin) != 500:
        raise RuntimeError(f"Expected 500 Nifty constituents, found {len(by_isin)}")

    instruments = download_csv(DHAN_MASTER_URL)
    result: dict[str, str] = {}
    for row in instruments:
        if row.get("EXCH_ID", "").strip().upper() != "NSE":
            continue
        if row.get("SEGMENT", "").strip().upper() != "E":
            continue
        if row.get("SERIES", "").strip().upper() != "EQ":
            continue
        symbol = by_isin.get(row.get("ISIN", "").strip())
        security_id = row.get("SECURITY_ID", "").strip()
        if symbol and security_id.isdigit():
            result[symbol] = security_id

    if len(result) < 490:
        raise RuntimeError(f"Only {len(result)} Nifty 500 securities mapped to Dhan IDs")
    print(f"UNIVERSE_READY mapped={len(result)}")
    return result


def as_number(value: object, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    alpha = 2.0 / (period + 1)
    current = sum(values[:period]) / period
    for value in values[period:]:
        current = (value * alpha) + (current * (1.0 - alpha))
    return current


def five_minute_bucket(now: datetime) -> datetime:
    minute = now.minute - (now.minute % CANDLE_MINUTES)
    return now.replace(minute=minute, second=0, microsecond=0)


def extract_quotes(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    data = payload.get("data", payload)
    if not isinstance(data, dict):
        return {}
    segment = data.get("NSE_EQ", {})
    return segment if isinstance(segment, dict) else {}


def quote_value(quote: dict[str, object], *names: str) -> float:
    for name in names:
        if name in quote:
            return as_number(quote[name])
    return 0.0


def update_candle(
    candle: Candle | None,
    bucket: datetime,
    price: float,
    cumulative_volume: float,
    previous_volume: float,
    vwap: float,
) -> Candle:
    volume_delta = max(0.0, cumulative_volume - previous_volume)
    if candle is None or candle.bucket != bucket:
        return Candle(bucket, price, price, price, price, volume_delta, vwap or None)
    candle.high = max(candle.high, price)
    candle.low = min(candle.low, price)
    candle.close = price
    candle.volume += volume_delta
    candle.vwap = vwap or candle.vwap
    return candle


def opening_breakout(
    symbol: str,
    security_id: str,
    candles: list[Candle],
    previous_close: float,
) -> Signal | None:
    if len(candles) < 2 or previous_close <= 0:
        return None
    first, confirmation = candles[0], candles[1]
    average_volume = sum(c.volume for c in candles[-20:]) / min(20, len(candles))
    close_values = [c.close for c in candles]
    ema9 = ema(close_values, 9)
    if first.range_pct >= 0.01:
        return None
    if (first.open - previous_close) / previous_close < 0.002:
        return None
    if ema9 is None or confirmation.close <= ema9:
        return None
    if average_volume <= 0 or confirmation.volume / average_volume < 1.5:
        return None
    entry = confirmation.high
    stop = first.low
    risk = entry - stop
    if risk <= 0:
        return None
    return Signal(symbol, security_id, "opening_breakout", entry, stop, entry + risk * RISK_REWARD, confirmation.volume / average_volume)


def ema_pullback(symbol: str, security_id: str, candles: list[Candle]) -> Signal | None:
    if len(candles) < 20:
        return None
    candle = candles[-1]
    closes = [item.close for item in candles]
    ema9 = ema(closes, 9)
    ema15 = ema(closes, 15)
    if ema9 is None or ema15 is None or ema9 <= ema15:
        return None
    average_volume = sum(item.volume for item in candles[-20:-1]) / 19
    if average_volume <= 0 or candle.volume / average_volume < 1.25:
        return None
    if candle.vwap is None or candle.close < candle.vwap:
        return None
    if abs(candle.close - ema9) / ema9 > 0.0025:
        return None
    if candle.low > ema9:
        return None
    entry = candle.high
    stop = min(candle.low, ema15)
    risk = entry - stop
    if risk <= 0:
        return None
    return Signal(symbol, security_id, "ema_pullback", entry, stop, entry + risk * RISK_REWARD, candle.volume / average_volume)


def position_size(signal: Signal, available_balance: float) -> tuple[int, float]:
    risk_per_share = signal.entry - signal.stop
    if risk_per_share <= 0 or available_balance <= 0:
        return 0, 0.0
    risk_quantity = math.floor((available_balance * RISK_PER_TRADE) / risk_per_share)
    exposure_cap = available_balance * MAX_LEVERAGE * MAX_MARGIN_UTILIZATION
    exposure_quantity = math.floor(exposure_cap / signal.entry)
    quantity = max(0, min(risk_quantity, exposure_quantity))
    return quantity, quantity * risk_per_share


def available_balance(dhan: object) -> float:
    response = dhan.get_fund_limits()
    if not isinstance(response, dict):
        return 0.0
    data = response.get("data", response)
    if not isinstance(data, dict):
        return 0.0
    for key in ("availabelBalance", "availableBalance", "sodLimit", "withdrawableBalance"):
        value = as_number(data.get(key))
        if value > 0:
            return value
    return 0.0


def market_is_open(now: datetime) -> bool:
    if now.weekday() >= 5:
        return False
    return clock_time(9, 15) <= now.time() <= clock_time(15, 25)


def run() -> None:
    if "{{" in CLIENT_ID or "{{" in ACCESS_TOKEN:
        raise RuntimeError("CLIENT_ID and ACCESS_TOKEN variables are required")

    universe = build_universe()
    id_to_symbol = {security_id: symbol for symbol, security_id in universe.items()}
    context = DhanContext(CLIENT_ID, ACCESS_TOKEN)
    dhan = dhanhq(context)
    balance = available_balance(dhan)
    print(f"START mode=PAPER_ONLY universe={len(universe)} balance={balance:.2f}")

    candles: dict[str, deque[Candle]] = defaultdict(lambda: deque(maxlen=80))
    active: dict[str, Candle] = {}
    previous_volume: dict[str, float] = defaultdict(float)
    previous_close: dict[str, float] = {}
    last_bucket: datetime | None = None
    emitted: set[tuple[str, str, datetime]] = set()

    while True:
        now = datetime.now(IST)
        if not market_is_open(now):
            time.sleep(30)
            continue

        try:
            response = dhan.quote_data({"NSE_EQ": [int(item) for item in universe.values()]})
            quotes = extract_quotes(response)
            bucket = five_minute_bucket(now)

            for security_id, raw_quote in quotes.items():
                if not isinstance(raw_quote, dict):
                    continue
                security_id = str(security_id)
                symbol = id_to_symbol.get(security_id)
                if not symbol:
                    continue
                price = quote_value(raw_quote, "last_price", "LTP", "ltp")
                if price <= 0:
                    continue
                cumulative_volume = quote_value(raw_quote, "volume", "volume_traded", "Volume")
                vwap = quote_value(raw_quote, "average_price", "average_traded_price", "ATP")
                ohlc = raw_quote.get("ohlc", {})
                if isinstance(ohlc, dict):
                    previous_close[symbol] = quote_value(ohlc, "close") or previous_close.get(symbol, 0.0)
                active[symbol] = update_candle(
                    active.get(symbol), bucket, price, cumulative_volume, previous_volume[symbol], vwap
                )
                previous_volume[symbol] = cumulative_volume

            if last_bucket is not None and bucket != last_bucket:
                candidates: list[Signal] = []
                for symbol, current in list(active.items()):
                    if current.bucket == last_bucket:
                        candles[symbol].append(current)
                    history = list(candles[symbol])
                    security_id = universe[symbol]
                    for signal in (
                        opening_breakout(symbol, security_id, history, previous_close.get(symbol, 0.0)),
                        ema_pullback(symbol, security_id, history),
                    ):
                        if signal and (signal.symbol, signal.strategy, last_bucket) not in emitted:
                            candidates.append(signal)

                for signal in sorted(candidates, key=lambda item: item.score, reverse=True)[:MAX_OPEN_POSITIONS]:
                    quantity, risk_amount = position_size(signal, balance)
                    if quantity <= 0:
                        continue
                    emitted.add((signal.symbol, signal.strategy, last_bucket))
                    print(
                        "PAPER_SIGNAL "
                        f"symbol={signal.symbol} strategy={signal.strategy} entry={signal.entry:.2f} "
                        f"stop={signal.stop:.2f} target={signal.target:.2f} quantity={quantity} "
                        f"risk={risk_amount:.2f} score={signal.score:.2f}"
                    )

            last_bucket = bucket
            time.sleep(SCAN_INTERVAL_SECONDS)
        except Exception as exc:
            print(f"SCAN_ERROR type={type(exc).__name__} message={exc}")
            time.sleep(10)


if __name__ == "__main__":
    run()
