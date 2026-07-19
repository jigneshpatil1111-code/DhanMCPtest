# AI Intraday Trading System Blueprint

## Project Goal

Ek production-style intraday trading system banana hai jo:

- Nifty 500 stocks scan kare
- User ki 2 strategies implement kare
- Entry, stop loss, target aur risk-based position sizing calculate kare
- Historical backtesting kare
- Daily live scan workflow support kare
- Dashboard aur trade journal maintain kare
- Automated tests run kare
- Bugs aur regressions detect karke fix workflow support kare

Important:

- `100% bug-free` guarantee realistic nahi hai
- Lekin system ko `production-ready`, `test-backed`, `well-logged`, aur `maintainable` banana target hai

## Strategy Scope

### Strategy 1: Opening Breakout

Core rules:

- First candle range `< 1%`
- Gap up condition required
- 9 EMA confirmation
- Volume confirmation
- Risk-reward rules apply

Notes:

- Final thresholds configurable hone chahiye
- Kisi bhi rule ko hardcode nahi karna
- Scanner aur backtester dono same strategy engine reuse karein

### Strategy 2: EMA Pullback

Core rules:

- 9 EMA
- 15 EMA
- VWAP
- Volume confirmation
- Risk-reward rules apply

Notes:

- Pullback definition config-driven honi chahiye
- Entry confirmation and invalidation rules explicit hone chahiye

## Product Requirements

System ke major modules:

1. Market Data Engine
2. Universe Scanner
3. Strategy Engine
4. Risk Management Engine
5. Backtesting Engine
6. Trade Journal
7. Analytics Dashboard
8. QA and Test Runner
9. Config and Logging Layer

## Recommended Architecture

### 1. Market Data Engine

Responsibilities:

- Historical OHLCV data ingest karna
- 5-minute candles store karna
- Symbol metadata maintain karna
- Corporate actions handling support karna where available
- Live/day-start refresh pipeline support karna

Recommended sources:

- Phase 1: Yahoo Finance available recent data for proof of concept
- Phase 2: Zerodha Kite Connect or Upstox or paid intraday provider for stronger system

Storage:

- PostgreSQL preferred
- Fast local cache ke liye parquet or sqlite optional

Suggested tables:

- `symbols`
- `ohlcv_5m`
- `daily_ohlcv`
- `corporate_actions`
- `data_ingestion_runs`

### 2. Universe Scanner

Responsibilities:

- Nifty 500 stock universe maintain karna
- Pre-market or early-session filters apply karna
- Eligible stocks shortlist karna
- Strategy-specific candidate list generate karna

Scanner outputs:

- Symbol
- Strategy eligibility
- Gap status
- First candle range
- Volume condition
- EMA/VWAP state
- Rejection reason if not selected

### 3. Strategy Engine

Responsibilities:

- Strategy 1 and Strategy 2 rules evaluate karna
- Entry price, stop loss, target calculate karna
- Signal quality score generate karna

Design requirement:

- Pure rule engine hona chahiye
- Backtest aur live mode dono same signal code use karein
- All parameters config file se aayein

### 4. Risk Management Engine

Responsibilities:

- Capital-based position sizing
- Per-trade max risk
- Daily loss limit
- Max open trades
- Slippage and brokerage assumptions

Outputs:

- Quantity
- Risk amount
- R multiple
- Breakeven and trail logic if enabled

### 5. Backtesting Engine

Responsibilities:

- Historical simulation
- Trade-by-trade replay
- Signal acceptance or rejection logging
- PnL calculation
- Equity curve generation

Mandatory metrics:

- Win rate
- Profit factor
- Expectancy
- Max drawdown
- Average holding time
- Best setup
- Worst setup
- Weekday-wise performance
- Sector-wise performance
- Market-condition analysis

### 6. Trade Journal

Responsibilities:

- All trades log karna
- Entry and exit reasons save karna
- Screenshot or chart link hooks optional
- Manual notes support karna

Suggested fields:

- Trade id
- Date
- Symbol
- Strategy
- Entry
- Stop loss
- Target
- Exit
- Quantity
- PnL
- Exit reason
- Filters passed
- Filters failed

### 7. Analytics Dashboard

Dashboard must show:

- Today candidates
- Active signals
- Historical performance
- Equity curve
- Strategy comparison
- Filter diagnostics
- Top rejection reasons
- Daily and weekly summaries

Suggested stack:

- Backend: Python FastAPI
- Frontend: Next.js or React dashboard
- Charts: lightweight interactive charts

### 8. QA and Test Runner

Responsibilities:

- Unit tests
- Integration tests
- Edge case tests
- Performance checks
- Regression suite

Coverage target:

- `95%+` on core business logic

Important:

- UI coverage se zyada strategy logic aur risk logic reliability important hai

### 9. Config and Logging Layer

All important values configurable hone chahiye:

- First candle threshold
- Gap threshold
- EMA periods
- VWAP usage
- Volume multiplier
- Risk-reward target
- Slippage
- Brokerage
- Max capital allocation

Logs must capture:

- Data fetch events
- Scanner decisions
- Signal generation reason
- Order simulation decisions
- Errors and retries

## Multi-Agent Build Plan

Ek single monolithic agent se better, project ko logical agents me break karna chahiye:

### Agent 1: Data Agent

- Historical data ingestion
- Symbol master maintenance
- Data quality validation

### Agent 2: Scanner Agent

- Nifty 500 filtering
- Eligibility logic
- Candidate ranking

### Agent 3: Strategy Agent

- Opening breakout implementation
- EMA pullback implementation
- Signal explanation output

### Agent 4: Backtesting Agent

- Backtest framework
- Performance analytics
- Result export

### Agent 5: Risk Agent

- Position sizing
- Loss limits
- Execution assumptions

### Agent 6: QA Agent

- Unit tests
- Integration tests
- Regression cycles
- Failure triage

## Definition of Done

Project tabhi complete maana jaye jab:

- Historical data pipeline stable ho
- Scanner deterministic results de
- Strategy engine expected signals generate kare
- Risk engine correct position sizing de
- Backtesting engine validated metrics de
- Trade journal correctly persist kare
- Dashboard crash-free ho on expected flows
- All critical tests pass
- Logs readable ho
- Config documentation complete ho

## Non-Negotiable Rules

- Hardcoded trade results allowed nahi
- Fake data allowed nahi
- Fake win rate allowed nahi
- Silent error ignore allowed nahi
- Manual patching without test evidence allowed nahi

Always required:

- Logging
- Error handling
- Retries where appropriate
- Unit tests
- Integration tests
- Regression checks
- Clear config files

## Suggested Tech Stack

### Backend

- Python 3.12+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Pandas
- Polars optional

### Backtesting

- Custom event-driven engine preferred
- Vectorized helpers where useful

### Frontend

- Next.js
- TypeScript
- Charting library

### Testing

- Pytest
- Coverage
- Playwright for dashboard smoke tests

### DevOps

- Docker
- `.env` based config
- Structured logging

## Delivery Phases

### Phase 1: Proof of Concept

- Yahoo Finance recent data
- Basic scanner
- Strategy 1 and Strategy 2 engine
- Simple backtest
- CSV or DB trade logs

### Phase 2: Structured Core

- Database schema
- Better data ingestion
- Modular backend
- Full analytics
- Risk engine

### Phase 3: Production Workflow

- Dashboard
- Schedules
- Alerting hooks
- Robust test suite
- Deployment packaging

## Master Build Prompt For Codex

Use the prompt below directly with Codex:

```text
Build a production-style AI Intraday Trading System for Nifty 500 stocks.

Primary goals:
- Implement two strategies:
  1. Opening Breakout Strategy
  2. EMA Pullback Strategy
- Use a shared strategy engine for both live scanning and backtesting
- Build a historical data ingestion layer
- Build a backtesting engine
- Build a risk management engine
- Build a trade journal
- Build a dashboard
- Add strong automated tests

Critical rules:
- Do not hardcode results
- Do not use fake performance metrics
- Do not silently ignore errors
- Keep all thresholds configurable
- Reuse the same core strategy logic in live and backtest modes
- Add structured logging and retry behavior where sensible
- Write unit, integration, regression, and edge-case tests
- Continue improving until all defined tests pass

Strategy constraints:
- Strategy 1 uses:
  - first candle range < 1%
  - gap up
  - 9 EMA
  - volume confirmation
  - configurable risk-reward
- Strategy 2 uses:
  - 9 EMA
  - 15 EMA
  - VWAP
  - volume confirmation
  - configurable risk-reward

Required modules:
- market data engine
- symbol universe manager
- scanner engine
- strategy engine
- risk management engine
- backtesting engine
- trade journal
- analytics dashboard
- config layer
- test suite

Required outputs:
- clean project structure
- database schema
- API layer
- documented configs
- test suite with high coverage on business logic
- dashboard for performance analytics
- logs and failure diagnostics

Backtesting metrics must include:
- win rate
- profit factor
- expectancy
- max drawdown
- average holding time
- weekday performance
- sector performance
- best setup
- worst setup

Definition of done:
- critical modules implemented
- tests passing
- no critical known bugs
- strategy engine validated on sample historical data
- dashboard working
- logs readable
- configs documented

Use an iterative workflow:
1. understand requirements
2. design architecture
3. implement modules
4. write tests
5. run tests
6. fix failures
7. rerun tests
8. repeat until stable

Prefer this stack unless the repository already dictates otherwise:
- Python backend with FastAPI
- PostgreSQL
- Pandas or Polars
- Next.js frontend
- Pytest
- Playwright for dashboard smoke tests
```

## Best Next Step

Agar aap chahein, next stage me main isi blueprint ke basis par:

1. Full folder structure bana sakta hoon
2. SRS document aur zyada detailed bana sakta hoon
3. Seedha project scaffold karke coding start kar sakta hoon

## Summary

Open chat ka actual intent ye tha:

- Strategy ko normal idea ki tarah nahi, full software system ki tarah build karna
- Data, scanner, strategy, backtest, risk, dashboard aur QA sab ek system me lana
- Codex ko vague instructions nahi, balki exact engineering brief dena

Ye document ussi intent ko practical build blueprint me convert karta hai.
