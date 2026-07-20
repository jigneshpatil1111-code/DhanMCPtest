from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import hmac
import os
from pathlib import Path

try:
    from fastapi import FastAPI, Header
    from fastapi import HTTPException
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel
except ImportError:  # pragma: no cover - optional dependency
    FastAPI = None  # type: ignore[assignment]
    HTTPException = Exception  # type: ignore[assignment]
    FileResponse = None  # type: ignore[assignment]
    StaticFiles = None  # type: ignore[assignment]
    BaseModel = object  # type: ignore[assignment]
    Header = None  # type: ignore[assignment]

from ai_intraday_trading.backtest.engine import summarize_backtest
from ai_intraday_trading.config import AppConfig, load_angel_market_data_config, load_config
from ai_intraday_trading.domain.models import Candle
from ai_intraday_trading.paths import get_project_paths
from ai_intraday_trading.persistence.sqlite_store import SQLiteStore
from ai_intraday_trading.services.backtest_service import run_intraday_backtest
from ai_intraday_trading.services.angel_market_data import AngelLiveWorker
from ai_intraday_trading.services.dashboard_service import build_dashboard_snapshot
from ai_intraday_trading.services.execution_policy import validate_execution_candidate
from ai_intraday_trading.services.journal_service import JournalService
from ai_intraday_trading.services.market_data_service import MarketDataService
from ai_intraday_trading.services.telegram_service import TelegramService
from ai_intraday_trading.universe import search_nifty500


class BacktestRequest(BaseModel):
    symbol: str
    previous_close: float
    average_volume: float
    candles: list[dict]


class CsvImportRequest(BaseModel):
    csv_path: str
    symbol: str | None = None


class PolicyValidationRequest(BaseModel):
    symbol: str
    strategy_name: str
    transaction_type: str = "BUY"
    product_type: str = "INTRADAY"


class SignalIngestRequest(BaseModel):
    signal_id: str
    symbol: str
    strategy_name: str
    entry_price: float
    stop_loss: float
    target_price: float
    quantity: int
    score: float
    created_at: str


def create_app():
    if FastAPI is None:
        raise RuntimeError(
            "FastAPI is not installed. Install the project with the 'api' extras to run the web app."
        )

    app = FastAPI(title="AI Intraday Trading System", version="0.1.0")
    package_root = Path(__file__).resolve().parent
    web_dir = package_root / "web"
    app.mount("/assets", StaticFiles(directory=web_dir), name="assets")
    paths = get_project_paths()
    config = load_config(paths.config_path) if paths.config_path.exists() else AppConfig()
    store = SQLiteStore(paths.db_path)
    market_data_service = MarketDataService(store)
    journal_service = JournalService(store)
    market_data_service.initialize()
    signal_secret = os.getenv("SIGNAL_WEBHOOK_SECRET")
    telegram = TelegramService(
        os.getenv("TELEGRAM_BOT_TOKEN"),
        os.getenv("TELEGRAM_CHAT_ID"),
    )

    def publish_live_signal(signal: dict[str, object]) -> None:
        if not store.insert_signal(signal):
            return
        if telegram.enabled:
            telegram.send_signal(signal)

    live_worker = AngelLiveWorker(
        load_angel_market_data_config(),
        config,
        publish_live_signal,
    )
    app.add_event_handler("startup", live_worker.start)
    app.add_event_handler("shutdown", live_worker.stop)

    @app.get("/", include_in_schema=False)
    def dashboard():
        return FileResponse(web_dir / "dashboard.html")

    @app.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/live/status")
    def live_status() -> dict[str, object]:
        return live_worker.status()

    @app.get("/api/dashboard")
    def dashboard_snapshot() -> dict[str, object]:
        return build_dashboard_snapshot(
            candidates=store.fetch_signals(),
            telegram_enabled=telegram.enabled,
        )

    @app.post("/api/signals")
    def ingest_signal(
        payload: SignalIngestRequest,
        x_signal_secret: str | None = Header(default=None),
    ) -> dict[str, object]:
        if not signal_secret:
            raise HTTPException(status_code=503, detail="Signal ingestion is not configured.")
        if not x_signal_secret or not hmac.compare_digest(x_signal_secret, signal_secret):
            raise HTTPException(status_code=401, detail="Invalid signal secret.")
        signal = payload.model_dump()
        inserted = store.insert_signal(signal)
        telegram_delivered = False
        telegram_error = None
        if inserted and telegram.enabled:
            try:
                telegram_delivered = telegram.send_signal(signal)
            except Exception as exc:
                telegram_error = type(exc).__name__
        return {
            "accepted": True,
            "duplicate": not inserted,
            "telegram_delivered": telegram_delivered,
            "telegram_error": telegram_error,
        }

    @app.get("/api/universe")
    def search_universe(query: str = "", limit: int = 25) -> list[dict[str, str]]:
        return [asdict(member) for member in search_nifty500(query, limit)]

    @app.post("/api/policy/validate")
    def validate_policy(payload: PolicyValidationRequest) -> dict[str, object]:
        return asdict(
            validate_execution_candidate(
                symbol=payload.symbol,
                strategy_name=payload.strategy_name,
                transaction_type=payload.transaction_type,
                product_type=payload.product_type,
            )
        )

    @app.get("/config")
    def get_config() -> dict[str, object]:
        return asdict(config)

    @app.get("/symbols")
    def list_symbols() -> list[dict[str, object]]:
        return [asdict(symbol) for symbol in store.list_symbols()]

    @app.post("/symbols/import")
    def import_symbols(payload: CsvImportRequest) -> dict[str, int]:
        csv_path = Path(payload.csv_path)
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="CSV file not found.")
        imported = market_data_service.import_symbol_universe(csv_path)
        return {"imported": imported}

    @app.post("/candles/import")
    def import_candles(payload: CsvImportRequest) -> dict[str, int]:
        if not payload.symbol:
            raise HTTPException(status_code=400, detail="symbol is required for candle imports.")
        csv_path = Path(payload.csv_path)
        if not csv_path.exists():
            raise HTTPException(status_code=404, detail="CSV file not found.")
        imported = market_data_service.import_candles(csv_path, symbol=payload.symbol)
        return {"imported": imported}

    @app.post("/backtest/preview")
    def preview_backtest(payload: BacktestRequest) -> dict[str, object]:
        candles = [_deserialize_candle(item) for item in payload.candles]
        trades, scan_results = run_intraday_backtest(
            symbol=payload.symbol,
            candles=candles,
            previous_close=payload.previous_close,
            average_volume=payload.average_volume,
            config=config,
        )
        summary = summarize_backtest(trades)
        return {
            "summary": asdict(summary),
            "trade_count": len(trades),
            "scan_count": len(scan_results),
        }

    @app.get("/journal/trades")
    def list_trades(symbol: str | None = None) -> list[dict[str, object]]:
        return journal_service.list_trades(symbol=symbol)

    @app.get("/journal/summary")
    def journal_summary(symbol: str | None = None) -> dict[str, object]:
        return journal_service.summary(symbol=symbol)

    return app


app = create_app() if FastAPI is not None else None


def _deserialize_candle(item: dict) -> Candle:
    payload = dict(item)
    if isinstance(payload.get("timestamp"), str):
        payload["timestamp"] = datetime.fromisoformat(payload["timestamp"])
    return Candle(**payload)
