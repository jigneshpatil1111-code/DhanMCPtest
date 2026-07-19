# Market Open Execution Checklist

Date for execution: Monday, July 20, 2026

## Objective

Market open hone ke baad aapki strategy ke according:

- live stock scan karna
- best valid setup select karna
- entry, SL, target, quantity calculate karna
- final approval ke baad order place karna

## Pre-Market Checklist

- Dhan login active ho
- Dhan MCP connected ho
- Dhan MCP funds check successful ho
- Available balance planned order ke liye sufficient ho
- Strategy rules finalized ho
- Capital and risk-per-trade fixed ho

## Strategy Conditions

### Strategy 1: Opening Breakout

- first candle range `< 1%`
- gap up present
- price above 9 EMA
- volume confirmation
- acceptable risk-reward

### Strategy 2: EMA Pullback

- 9 EMA above 15 EMA
- pullback near 9 EMA
- VWAP aligned
- volume confirmation
- acceptable risk-reward

## Execution Flow

### 1. Market Scan

- Nifty universe ya selected watchlist scan karo
- invalid setups reject karo
- sirf top valid candidates rakho

### 2. Signal Validation

For selected stock:

- strategy name
- setup reason
- entry price
- stop loss
- target
- quantity
- total risk

### 3. Final Action Summary

Order place karne se pehle ye summary dikhani hai:

- selected stock
- strategy used
- buy or sell side
- entry
- SL
- target
- quantity
- estimated capital use

### 4. Final Confirmation Gate

Live order tabhi place hoga jab aap us moment par final approval doge.

Recommended exact confirmation phrase:

`Yes, place the order`

## Fallback Rules

If:

- Dhan MCP read fail kare
- available balance insufficient ho
- market data incomplete ho
- no valid setup mile

Then:

- no order place hoga
- sirf reason report hoga

## Opening Prompt For Tomorrow

Kal market open hone par seedha ye prompt use karo:

```text
Market open ho gaya hai. Meri strategy ke according live scan chalao, best valid stock select karo, entry stop loss target quantity calculate karo, aur order place karne se pehle final action summary dikhao.
```

## Final Note

Goal direct blind order placement nahi hai.

Goal hai:

- disciplined stock selection
- valid setup confirmation
- risk-controlled execution
- final approval ke baad order placement
