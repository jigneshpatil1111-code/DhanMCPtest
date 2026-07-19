# Next Market Open Order Plan

## Current Status

Date: Sunday, July 19, 2026

Market status:

- Indian cash market closed
- No live setup can be validated right now
- Dhan MCP is connected
- Dhan read-only portfolio calls were attempted, but the MCP calls were canceled before returning data

Because of this, **no valid live stock selection or order placement can be completed today**.

## What Is Ready

The execution path is prepared:

- Dhan MCP connected through Codex
- Trading system scaffold created locally
- Strategy logic foundation available
- Order placement intent confirmed by you

## Order Placement Rules For Next Market Session

Before placing any order, all these must be true:

1. Market is open
2. Dhan MCP call completes successfully
3. A live stock matches your setup
4. Entry, stop loss, and target are calculable
5. Quantity is derived from risk rules
6. Final order action is confirmed at execution time

## Stock Selection Logic To Use

### Strategy 1: Opening Breakout

Required checks:

- First candle range less than 1%
- Gap up condition present
- Price above 9 EMA
- Volume confirmation present
- Risk-reward acceptable

### Strategy 2: EMA Pullback

Required checks:

- 9 EMA above 15 EMA
- Pullback near 9 EMA
- VWAP alignment present
- Volume confirmation present
- Risk-reward acceptable

## Order Ticket Format

For the selected stock, generate:

- Symbol
- Strategy name
- Entry price
- Stop loss
- Target price
- Quantity
- Total capital used
- Risk amount

## Immediate Next Action At Market Open

Run this sequence:

1. Fetch live eligible stocks
2. Apply your setup filters
3. Select the highest-quality valid setup
4. Calculate entry, SL, target, and quantity
5. Reconfirm order side and product type
6. Place the order through Dhan

## Exact Prompt To Use Next Time

Use this directly when market is open:

```text
Market open hai. Mere setup ke according live scan chalao, best valid stock select karo, entry stop loss target quantity calculate karo, aur order place karne se just pehle final action summary dikhao.
```

## Final Truth

Today no real stock can be responsibly selected or ordered because:

- market closed hai
- live signal unavailable hai
- Dhan MCP read verification complete nahi hui

The correct next step is to execute this plan in the next live market session.
