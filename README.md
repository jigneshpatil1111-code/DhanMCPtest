# AI Intraday Trading System

Production-style scaffold for an intraday trading platform focused on Nifty 500 scanning, strategy evaluation, risk controls, and backtesting.

## Current Scope

This initial scaffold includes:

- Python package structure
- Config models
- Market data domain models
- Local SQLite persistence layer
- CSV-based candle ingestion utility
- Config loading from TOML
- Dhan API client scaffold with env-based auth
- Dhan margin calculator and Super Order payload support
- Entry, stop-loss, and 1:2 target proposals
- Maximum 5x exposure cap with 95% margin-utilization ceiling
- Exact action-time approval gate for live order submission
- Strategy engines for:
  - Opening Breakout
  - EMA Pullback
- Scanner orchestration
- Risk sizing logic
- Backtesting engine
- Simple trade simulation service
- Authenticated live-signal dashboard ingestion and Telegram notifications
- Angel One WebSocket 2.0 live-data worker for Nifty 500 scanning
- Market data import service
- Trade journal query service
- FastAPI application entrypoint scaffold
- Unit tests for core trading logic

## Project Layout

```text
src/ai_intraday_trading/
  api/
  backtest/
  domain/
  ingestion/
  persistence/
  services/
  strategies/
  config.py
  main.py
  risk.py
  scanner.py
tests/
```

## Quick Start

On Windows, run the one-time setup:

```powershell
.\setup-project.cmd
```

Check the complete local setup at any time:

```powershell
.\check-project.cmd
```

Start the local API:

```powershell
.\start-project.cmd
```

Then open `http://127.0.0.1:8000/docs`. The health endpoint is
`http://127.0.0.1:8000/health`.

Sample config template:

```text
work/config.example.toml
```

Optional environment variables for direct Dhan API access:

```text
DHAN_ACCESS_TOKEN=...
DHAN_CLIENT_ID=...
SIGNAL_WEBHOOK_SECRET=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
ANGEL_LIVE_DATA_ENABLED=false
ANGEL_API_KEY=...
ANGEL_CLIENT_CODE=...
ANGEL_JWT_TOKEN=...
ANGEL_FEED_TOKEN=...
```

## Notes

- This scaffold intentionally keeps strategy logic deterministic and testable.
- SQLite and CSV support are included as local-first building blocks.
- Broker integration and dashboard UI are planned next layers.
- Dhan MCP authentication is managed by Codex, not by files in this repository.
- Never commit access tokens. Live orders require a fresh pre-trade funds check and explicit action-time approval.
- Dhan order APIs require Static IP whitelisting. `DHAN_LIVE_ORDERS_ENABLED` defaults to `false`.
- Angel One provides market data only; Dhan is not used by the live scanner.
- The configured 5x value is a ceiling, not a guarantee; Dhan's live margin response is authoritative.
