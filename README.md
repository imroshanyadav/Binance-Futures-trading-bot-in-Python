<<<<<<< HEAD
# Simplified Trading Bot — Binance Futures Testnet (USDT-M)

A small, structured Python CLI application for placing **MARKET**, **LIMIT**,
and (bonus) **STOP-LIMIT** orders on the Binance USDT-M Futures Testnet, with
input validation, structured logging, and clean error handling.

## Project Structure

```
trading_bot/
  bot/
    __init__.py
    client.py          # Binance REST client (HMAC signing, request/response, errors)
    orders.py           # Order placement logic (Market/Limit/Stop) + summary printing
    validators.py        # CLI input validation
    logging_config.py    # Console + rotating file logger setup
  cli.py                 # CLI entry point (argparse)
  requirements.txt
  logs/
    trading_bot.log       # Sample log output (MARKET, LIMIT, STOP orders)
  README.md
```

**Layering:** `cli.py` (command layer) never talks to the network directly —
it validates input, then delegates to `OrderManager` (`orders.py`), which
calls `BinanceFuturesClient` (`client.py`), the only place that knows about
HTTP, signing, and the Binance API surface. This keeps the code testable and
easy to extend (e.g. swapping REST for `python-binance` only touches
`client.py`).

## Setup

### 1. Create a Binance Futures Testnet account
1. Go to https://testnet.binancefuture.com
2. Log in with a GitHub account (the testnet uses GitHub OAuth).
3. Once logged in, go to **API Key** management on the testnet dashboard and
   generate an **API Key** and **API Secret**.
4. The testnet gives you a virtual USDT balance automatically — no real
   funds are involved.

### 2. Install dependencies
```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Provide your API credentials
Either export environment variables (recommended, keeps keys out of shell
history/process list):
```bash
export BINANCE_API_KEY="your_testnet_api_key"
export BINANCE_API_SECRET="your_testnet_api_secret"
```
or pass them directly as CLI flags (`--api-key` / `--api-secret`).

## How to Run

### Place a MARKET order
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Place a LIMIT order
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
```

### Place a STOP-LIMIT order (bonus feature)
Triggers a limit order at `--price` once the market touches `--stop-price`:
```bash
python cli.py --symbol BTCUSDT --side BUY --type STOP --quantity 0.01 --price 61000 --stop-price 60800
```

### Dry-run mode (no live API calls, no credentials needed)
Useful for verifying the CLI, validation, and logging pipeline without
touching the network:
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01 --dry-run
```

### Full argument list
| Flag | Required | Description |
|---|---|---|
| `--symbol` | yes | Trading pair, e.g. `BTCUSDT` |
| `--side` | yes | `BUY` or `SELL` |
| `--type` | yes | `MARKET`, `LIMIT`, or `STOP` |
| `--quantity` | yes | Order quantity (float, > 0) |
| `--price` | LIMIT/STOP only | Limit price |
| `--stop-price` | STOP only | Trigger price |
| `--time-in-force` | no | `GTC` (default), `IOC`, `FOK` |
| `--api-key` / `--api-secret` | yes (unless `--dry-run`) | Testnet credentials (or use env vars) |
| `--base-url` | no | Defaults to `https://testnet.binancefuture.com` |
| `--dry-run` | no | Simulate locally, skip the real API call |

## Output

Every run prints:
1. **Order request summary** — the exact parameters sent to Binance.
2. **Order response details** — `orderId`, `status`, `executedQty`, `avgPrice`.
3. A clear **SUCCESS** or **FAILED** message.

## Logging

- All requests, responses, and errors are logged to `logs/trading_bot.log`
  (rotating at 2MB, 5 backups kept) with full detail (`DEBUG` level).
- The console only shows `INFO`-level and above, keeping CLI output readable.
- API secrets/signatures are **never** written to the log file.
- `logs/trading_bot.log` in this repo already contains sample entries from
  one MARKET order, one LIMIT order, and one bonus STOP order (generated via
  `--dry-run` while preparing this submission — see Assumptions below).

## Error Handling

The app handles three categories of failure distinctly:
- **Invalid input** (e.g. negative quantity, missing price for LIMIT) →
  caught by `bot/validators.py`, reported before any network call is made.
- **API errors** (e.g. bad symbol, insufficient testnet balance, invalid
  signature) → raised as `BinanceAPIError`, with the full Binance error
  payload logged.
- **Network failures** (timeouts, connection errors) → raised as
  `BinanceNetworkError` and logged separately from API errors.

## Assumptions

- This environment used to prepare the submission does not have outbound
  network access to `testnet.binancefuture.com`, so the sample log entries
  in `logs/trading_bot.log` were generated using the built-in `--dry-run`
  mode (see `bot/client.py::_simulate_response`), which exercises the exact
  same validation → request-building → logging → response-parsing pipeline
  as a live call, minus the actual HTTP round trip. Running the same
  commands with real testnet API keys and `--dry-run` omitted will produce
  live orders and log entries in the identical format.
- `STOP` orders are implemented as Binance Futures `STOP` type orders
  (stop-limit): once `stopPrice` is touched, a limit order is placed at
  `price`.
- Default `timeInForce` is `GTC` (Good-Til-Cancelled) for LIMIT/STOP orders.
- Quantity/price precision (`stepSize`/`tickSize`) filtering per-symbol is
  not implemented — for the testnet grading flow, use standard increments
  (e.g. `0.001`+ for BTCUSDT quantity) to avoid `LOT_SIZE`/`PRICE_FILTER`
  rejections from Binance.

## Bonus Feature Implemented

**Third order type: STOP (Stop-Limit)** — see `OrderManager.stop_limit_order`
in `bot/orders.py` and the `--type STOP --stop-price` CLI flags above.
=======
# Binance-Futures-trading-bot-in-Python
Simplified trading bot for Binance Futures Testnet (USDT-M USDT-margined futures). Built in Python with a clean client/CLI separation, argparse-based input, HMAC-signed REST requests, structured logging to file, and support for MARKET, LIMIT, and bonus STOP-LIMIT order types.
>>>>>>> cefb0c7cf979792a9ba100a9e4e9d9ed62fd296a
