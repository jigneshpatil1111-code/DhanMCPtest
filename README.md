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
- Strategy engines for:
  - Opening Breakout
  - EMA Pullback
- Scanner orchestration
- Risk sizing logic
- Backtesting engine
- Simple trade simulation service
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
```

## Notes

- This scaffold intentionally keeps strategy logic deterministic and testable.
- SQLite and CSV support are included as local-first building blocks.
- Broker integration and dashboard UI are planned next layers.
- Dhan MCP authentication is managed by Codex, not by files in this repository.
- Never commit access tokens. Live orders require a fresh pre-trade funds check and explicit action-time approval.
