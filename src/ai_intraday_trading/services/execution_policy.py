from __future__ import annotations

from dataclasses import dataclass

from ai_intraday_trading.universe import nifty500_symbols


ALLOWED_STRATEGIES = frozenset({"opening_breakout", "ema_pullback"})


@dataclass(frozen=True, slots=True)
class ExecutionPolicyDecision:
    allowed: bool
    symbol: str
    strategy_name: str
    reasons: tuple[str, ...]


def validate_execution_candidate(
    *,
    symbol: str,
    strategy_name: str,
    transaction_type: str = "BUY",
    product_type: str = "INTRADAY",
) -> ExecutionPolicyDecision:
    normalized_symbol = symbol.strip().upper()
    normalized_strategy = strategy_name.strip().lower()
    reasons: list[str] = []

    if normalized_symbol not in nifty500_symbols():
        reasons.append("Symbol is not in the locked Nifty 500 universe.")
    if normalized_strategy not in ALLOWED_STRATEGIES:
        reasons.append("Strategy is not one of the two approved strategies.")
    if transaction_type.strip().upper() != "BUY":
        reasons.append("The approved strategies currently support BUY signals only.")
    if product_type.strip().upper() != "INTRADAY":
        reasons.append("Only INTRADAY product type is permitted.")

    return ExecutionPolicyDecision(
        allowed=not reasons,
        symbol=normalized_symbol,
        strategy_name=normalized_strategy,
        reasons=tuple(reasons) if reasons else ("All hard policy gates passed.",),
    )
