# Dhan Cloud deployment

This deployment emits signal alerts to the dashboard and Telegram. It never
calls the Dhan order API.

## Variables

- `CLIENT_ID`: Dhan client ID
- `ACCESS_TOKEN`: active Dhan access token
- `DASHBOARD_SIGNAL_URL`: Railway `/api/signals` endpoint
- `SIGNAL_WEBHOOK_SECRET`: same random secret configured on Railway

## Dependencies

Add the package names from `dependencies.txt` in the Dhan Cloud Dependencies tab.

## Strategy policy

- Universe: official Nifty 500 equity constituents only
- Strategies: opening breakout and EMA 9/15 pullback only
- Product design: long intraday proposals
- Position limits: 1% risk, three concurrent candidates, 3% daily loss guardrail,
  5x maximum exposure and 95% maximum margin utilization
- Output: dashboard and Telegram signal alerts only; no order API is called
