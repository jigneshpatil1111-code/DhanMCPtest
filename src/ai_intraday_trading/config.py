from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import tomllib


@dataclass(slots=True)
class OpeningBreakoutConfig:
    first_candle_max_range_pct: float = 0.01
    minimum_gap_pct: float = 0.002
    minimum_volume_multiple: float = 1.5
    ema_period: int = 9
    risk_reward_ratio: float = 2.0


@dataclass(slots=True)
class EmaPullbackConfig:
    fast_ema_period: int = 9
    slow_ema_period: int = 15
    minimum_volume_multiple: float = 1.25
    pullback_tolerance_pct: float = 0.0025
    risk_reward_ratio: float = 2.0
    require_vwap_alignment: bool = True


@dataclass(slots=True)
class RiskConfig:
    capital: float = 100000.0
    risk_per_trade_pct: float = 0.01
    max_open_positions: int = 3
    daily_loss_limit_pct: float = 0.03
    assumed_slippage_pct: float = 0.0005
    max_leverage: float = 5.0
    max_margin_utilization_pct: float = 0.95


@dataclass(slots=True)
class AppConfig:
    opening_breakout: OpeningBreakoutConfig = field(default_factory=OpeningBreakoutConfig)
    ema_pullback: EmaPullbackConfig = field(default_factory=EmaPullbackConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)


@dataclass(slots=True)
class DhanApiConfig:
    access_token: str | None = None
    client_id: str | None = None
    base_url: str = "https://api.dhan.co/v2"
    live_orders_enabled: bool = False


@dataclass(slots=True)
class AngelMarketDataConfig:
    api_key: str | None = None
    client_code: str | None = None
    jwt_token: str | None = None
    feed_token: str | None = None
    enabled: bool = False


def load_config(config_path: str | Path | None = None) -> AppConfig:
    if config_path is None:
        env_path = os.getenv("AI_INTRADAY_CONFIG")
        config_path = Path(env_path) if env_path else None

    config = AppConfig()
    if config_path is None:
        return config

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("rb") as handle:
        payload = tomllib.load(handle)

    _apply_section(config.opening_breakout, payload.get("opening_breakout", {}))
    _apply_section(config.ema_pullback, payload.get("ema_pullback", {}))
    _apply_section(config.risk, payload.get("risk", {}))
    return config


def load_dhan_api_config() -> DhanApiConfig:
    return DhanApiConfig(
        access_token=os.getenv("DHAN_ACCESS_TOKEN"),
        client_id=os.getenv("DHAN_CLIENT_ID"),
        base_url=os.getenv("DHAN_API_BASE_URL", "https://api.dhan.co/v2"),
        live_orders_enabled=os.getenv("DHAN_LIVE_ORDERS_ENABLED", "false").lower()
        in {"1", "true", "yes"},
    )


def load_angel_market_data_config() -> AngelMarketDataConfig:
    return AngelMarketDataConfig(
        api_key=os.getenv("ANGEL_API_KEY"),
        client_code=os.getenv("ANGEL_CLIENT_CODE"),
        jwt_token=os.getenv("ANGEL_JWT_TOKEN"),
        feed_token=os.getenv("ANGEL_FEED_TOKEN"),
        enabled=os.getenv("ANGEL_LIVE_DATA_ENABLED", "false").lower()
        in {"1", "true", "yes"},
    )


def _apply_section(target: object, values: dict[str, object]) -> None:
    for key, value in values.items():
        if hasattr(target, key):
            setattr(target, key, value)
