from __future__ import annotations

import json
import threading
import urllib.request
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from zoneinfo import ZoneInfo

from ai_intraday_trading.config import AngelMarketDataConfig, AppConfig
from ai_intraday_trading.domain.models import Candle
from ai_intraday_trading.scanner import ScanInput, scan_symbol
from ai_intraday_trading.universe import nifty500_symbols


ANGEL_INSTRUMENTS_URL = (
    "https://margincalculator.angelone.in/OpenAPI_File/files/OpenAPIScripMaster.json"
)
IST = ZoneInfo("Asia/Kolkata")
PRICE_SCALE = 100.0


@dataclass(frozen=True, slots=True)
class AngelInstrument:
    symbol: str
    token: str


@dataclass(frozen=True, slots=True)
class AngelTick:
    token: str
    timestamp: datetime
    price: float
    cumulative_volume: float
    vwap: float | None
    previous_close: float


def load_angel_nifty500_instruments() -> dict[str, AngelInstrument]:
    with urllib.request.urlopen(ANGEL_INSTRUMENTS_URL, timeout=30) as response:
        records = json.loads(response.read().decode("utf-8"))

    universe = nifty500_symbols()
    mapped: dict[str, AngelInstrument] = {}
    for record in records:
        trading_symbol = str(record.get("symbol", "")).strip().upper()
        if str(record.get("exch_seg", "")).upper() != "NSE":
            continue
        if not trading_symbol.endswith("-EQ"):
            continue
        symbol = trading_symbol.removesuffix("-EQ")
        token = str(record.get("token", "")).strip()
        if symbol in universe and token.isdigit():
            mapped[token] = AngelInstrument(symbol=symbol, token=token)

    if len(mapped) < 490:
        raise RuntimeError(f"Only {len(mapped)} Nifty 500 symbols mapped to Angel tokens.")
    return mapped


def parse_angel_tick(message: dict[str, object]) -> AngelTick | None:
    token = str(message.get("token", "")).strip()
    timestamp_ms = int(message.get("exchange_timestamp", 0) or 0)
    price = float(message.get("last_traded_price", 0) or 0) / PRICE_SCALE
    if not token or timestamp_ms <= 0 or price <= 0:
        return None
    average_price = float(message.get("average_traded_price", 0) or 0) / PRICE_SCALE
    return AngelTick(
        token=token,
        timestamp=datetime.fromtimestamp(timestamp_ms / 1000, tz=IST),
        price=price,
        cumulative_volume=float(message.get("volume_trade_for_the_day", 0) or 0),
        vwap=average_price or None,
        previous_close=float(message.get("closed_price", 0) or 0) / PRICE_SCALE,
    )


def five_minute_bucket(timestamp: datetime) -> datetime:
    return timestamp.replace(
        minute=timestamp.minute - timestamp.minute % 5,
        second=0,
        microsecond=0,
    )


def ema(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    value = sum(values[:period]) / period
    alpha = 2.0 / (period + 1)
    for item in values[period:]:
        value = item * alpha + value * (1.0 - alpha)
    return value


class LiveCandleScanner:
    def __init__(
        self,
        config: AppConfig,
        token_map: dict[str, AngelInstrument],
        publish: Callable[[dict[str, object]], None],
    ) -> None:
        self.config = config
        self.token_map = token_map
        self.publish = publish
        self.active: dict[str, Candle] = {}
        self.history: dict[str, deque[Candle]] = defaultdict(lambda: deque(maxlen=80))
        self.previous_volume: dict[str, float] = defaultdict(float)
        self.previous_close: dict[str, float] = {}
        self.emitted: set[tuple[str, str, str]] = set()
        self.signals_today = 0
        self.lock = threading.Lock()

    def on_tick(self, tick: AngelTick) -> None:
        instrument = self.token_map.get(tick.token)
        if instrument is None:
            return
        with self.lock:
            self._consume(instrument.symbol, tick)

    def _consume(self, symbol: str, tick: AngelTick) -> None:
        bucket = five_minute_bucket(tick.timestamp)
        current = self.active.get(symbol)
        if current is not None and current.timestamp != bucket:
            self._finalize(symbol, current)
            current = None

        volume_delta = max(0.0, tick.cumulative_volume - self.previous_volume[symbol])
        if current is None:
            current = Candle(
                symbol=symbol,
                timestamp=bucket,
                open=tick.price,
                high=tick.price,
                low=tick.price,
                close=tick.price,
                volume=volume_delta,
                vwap=tick.vwap,
            )
            self.active[symbol] = current
        else:
            current.high = max(current.high, tick.price)
            current.low = min(current.low, tick.price)
            current.close = tick.price
            current.volume += volume_delta
            current.vwap = tick.vwap or current.vwap

        self.previous_volume[symbol] = tick.cumulative_volume
        if tick.previous_close > 0:
            self.previous_close[symbol] = tick.previous_close

    def _finalize(self, symbol: str, candle: Candle) -> None:
        history = self.history[symbol]
        closes = [item.close for item in history] + [candle.close]
        candle.ema_9 = ema(closes, self.config.ema_pullback.fast_ema_period)
        candle.ema_15 = ema(closes, self.config.ema_pullback.slow_ema_period)
        history.append(candle)
        if len(history) < 2 or self.signals_today >= self.config.risk.max_open_positions:
            return

        volumes = [item.volume for item in list(history)[-20:-1]]
        average_volume = sum(volumes) / len(volumes) if volumes else 0.0
        decisions = scan_symbol(
            ScanInput(
                symbol=symbol,
                first_candle=history[0],
                current_candle=candle,
                previous_close=self.previous_close.get(symbol, 0.0),
                average_volume=average_volume,
            ),
            self.config,
        )
        for decision in decisions:
            key = (symbol, decision.strategy_name, candle.timestamp.date().isoformat())
            if not decision.is_valid or key in self.emitted:
                continue
            self.emitted.add(key)
            self.signals_today += 1
            self.publish(
                {
                    "signal_id": f"{symbol}-{decision.strategy_name}-{candle.timestamp.isoformat()}",
                    "symbol": symbol,
                    "strategy_name": decision.strategy_name,
                    "entry_price": decision.entry_price,
                    "stop_loss": decision.stop_loss,
                    "target_price": decision.target_price,
                    "quantity": 0,
                    "score": float(decision.metadata.get("volume_multiple", 0.0)),
                    "created_at": candle.timestamp.isoformat(),
                }
            )
            if self.signals_today >= self.config.risk.max_open_positions:
                break


class AngelLiveWorker:
    def __init__(
        self,
        credentials: AngelMarketDataConfig,
        strategy_config: AppConfig,
        publish: Callable[[dict[str, object]], None],
    ) -> None:
        self.credentials = credentials
        self.strategy_config = strategy_config
        self.publish = publish
        self.thread: threading.Thread | None = None
        self.socket = None
        self.state = "disabled"
        self.last_tick_at: datetime | None = None
        self.error: str | None = None

    @property
    def configured(self) -> bool:
        return self.credentials.enabled and all(
            (
                self.credentials.api_key,
                self.credentials.client_code,
                self.credentials.jwt_token,
                self.credentials.feed_token,
            )
        )

    def start(self) -> None:
        if not self.configured or self.thread is not None:
            return
        self.thread = threading.Thread(target=self._run, name="angel-live-feed", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if self.socket is not None:
            self.socket.close_connection()
        self.state = "stopped"

    def status(self) -> dict[str, object]:
        return {
            "provider": "angel_one",
            "configured": self.configured,
            "state": self.state,
            "last_tick_at": self.last_tick_at.isoformat() if self.last_tick_at else None,
            "error": self.error,
        }

    def _run(self) -> None:
        try:
            from SmartApi.smartWebSocketV2 import SmartWebSocketV2

            token_map = load_angel_nifty500_instruments()
            scanner = LiveCandleScanner(self.strategy_config, token_map, self.publish)
            self.socket = SmartWebSocketV2(
                self.credentials.jwt_token,
                self.credentials.api_key,
                self.credentials.client_code,
                self.credentials.feed_token,
            )

            def on_open(_ws) -> None:
                self.state = "connected"
                self.socket.subscribe(
                    "nifty500-live",
                    SmartWebSocketV2.QUOTE,
                    [{"exchangeType": 1, "tokens": list(token_map)}],
                )

            def on_data(_ws, message) -> None:
                tick = parse_angel_tick(message)
                if tick is not None:
                    self.last_tick_at = datetime.now(IST)
                    scanner.on_tick(tick)

            def on_error(_ws, error) -> None:
                self.state = "error"
                self.error = type(error).__name__

            def on_close(_ws) -> None:
                if self.state != "stopped":
                    self.state = "disconnected"

            self.socket.on_open = on_open
            self.socket.on_data = on_data
            self.socket.on_error = on_error
            self.socket.on_close = on_close
            self.state = "connecting"
            self.socket.connect()
        except Exception as exc:
            self.state = "error"
            self.error = type(exc).__name__
