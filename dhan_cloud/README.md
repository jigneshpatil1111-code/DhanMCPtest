# Dhan Cloud deployment

This deployment is intentionally paper-only until live market logs and sandbox
behaviour validate the two approved strategies.

## Variables

- `CLIENT_ID`: Dhan client ID
- `ACCESS_TOKEN`: active Dhan access token

## Dependencies

Add the package names from `dependencies.txt` in the Dhan Cloud Dependencies tab.

## Strategy policy

- Universe: official Nifty 500 equity constituents only
- Strategies: opening breakout and EMA 9/15 pullback only
- Product design: long intraday proposals
- Position limits: 1% risk, three concurrent candidates, 3% daily loss guardrail,
  5x maximum exposure and 95% maximum margin utilization
- Output: paper signals only; no order API is called by this version
