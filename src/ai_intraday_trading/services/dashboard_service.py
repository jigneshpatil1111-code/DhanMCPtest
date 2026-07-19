from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from ai_intraday_trading.services.execution_policy import ALLOWED_STRATEGIES
from ai_intraday_trading.universe import load_nifty500_members


IST = timezone(timedelta(hours=5, minutes=30), name="IST")


def build_dashboard_snapshot(
    now: datetime | None = None,
    candidates: list[dict[str, object]] | None = None,
    telegram_enabled: bool = False,
) -> dict[str, object]:
    current = now.astimezone(IST) if now else datetime.now(IST)
    market_open = current.weekday() < 5 and time(9, 15) <= current.time() <= time(15, 30)

    return {
        "system": {
            "status": "ready",
            "market_state": "open" if market_open else "closed",
            "as_of": current.isoformat(),
            "execution_route": "Dhan MCP via Codex",
            "execution_mode": "approval-gated live",
        },
        "universe": {
            "name": "Nifty 500",
            "count": len(load_nifty500_members()),
            "locked": True,
            "source": "NSE official constituent CSV",
        },
        "strategies": [
            {
                "id": "opening_breakout",
                "name": "Opening Breakout",
                "status": "active",
                "rules": ["Gap up", "First candle range < 1%", "Above EMA 9", "Volume confirmation"],
            },
            {
                "id": "ema_pullback",
                "name": "EMA Pullback",
                "status": "active",
                "rules": ["EMA 9 > EMA 15", "Pullback near EMA 9", "VWAP aligned", "Volume confirmation"],
            },
        ],
        "guardrails": {
            "allowed_strategy_count": len(ALLOWED_STRATEGIES),
            "nifty500_only": True,
            "intraday_only": True,
            "funds_check_required": True,
            "final_confirmation_required": True,
            "auto_order_without_confirmation": False,
        },
        "scan": {
            "state": "waiting_for_market" if not market_open else "ready_for_live_data",
            "candidates": candidates or [],
            "message": (
                f"{len(candidates)} verified signal(s)."
                if candidates
                else "No verified signal has arrived yet."
            ),
            "telegram_enabled": telegram_enabled,
        },
    }
