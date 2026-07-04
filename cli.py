#!/usr/bin/env python3
"""
CLI entry point for the Simplified Trading Bot (Binance Futures Testnet).

Examples:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
    python cli.py --symbol BTCUSDT --side BUY --type STOP --quantity 0.01 --price 61000 --stop-price 60800

Credentials can be supplied via --api-key/--api-secret, or (preferred) via
environment variables BINANCE_API_KEY / BINANCE_API_SECRET.
"""

import argparse
import logging
import os
import sys

from bot.client import BinanceAPIError, BinanceFuturesClient, BinanceNetworkError, DEFAULT_BASE_URL
from bot.logging_config import setup_logger
from bot.orders import OrderManager
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place MARKET / LIMIT / STOP orders on Binance Futures Testnet (USDT-M)."
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, help="BUY or SELL")
    parser.add_argument(
        "--type", required=True, dest="order_type", help="MARKET, LIMIT, or STOP (bonus)"
    )
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", help="Required for LIMIT and STOP orders")
    parser.add_argument("--stop-price", dest="stop_price", help="Required for STOP orders")
    parser.add_argument(
        "--time-in-force",
        dest="time_in_force",
        default="GTC",
        help="GTC / IOC / FOK (default: GTC). Ignored for MARKET orders.",
    )
    parser.add_argument(
        "--api-key", dest="api_key", default=os.environ.get("BINANCE_API_KEY"),
        help="Binance Testnet API key (or set BINANCE_API_KEY env var)",
    )
    parser.add_argument(
        "--api-secret", dest="api_secret", default=os.environ.get("BINANCE_API_SECRET"),
        help="Binance Testnet API secret (or set BINANCE_API_SECRET env var)",
    )
    parser.add_argument(
        "--base-url", dest="base_url", default=DEFAULT_BASE_URL,
        help=f"API base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulate the order locally without calling the real API (for testing).",
    )
    return parser


def main(argv=None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    logger = setup_logger()

    # ---- Validate input -------------------------------------------------
    try:
        symbol = validate_symbol(args.symbol)
        side = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity = validate_quantity(args.quantity)
        price = validate_price(args.price, order_type)
        stop_price = validate_stop_price(args.stop_price, order_type)
    except ValueError as exc:
        logger.error(f"Input validation failed: {exc}")
        print(f"\nINVALID INPUT: {exc}")
        return 1

    if not args.dry_run and (not args.api_key or not args.api_secret):
        logger.error("Missing API credentials.")
        print(
            "\nERROR: API key/secret not provided. Pass --api-key/--api-secret, "
            "set BINANCE_API_KEY/BINANCE_API_SECRET env vars, or use --dry-run to test "
            "without credentials."
        )
        return 1

    # ---- Build client + order manager -----------------------------------
    client = BinanceFuturesClient(
        api_key=args.api_key or "DRY-RUN-KEY",
        api_secret=args.api_secret or "DRY-RUN-SECRET",
        base_url=args.base_url,
        logger=logger,
        dry_run=args.dry_run,
    )
    if not args.dry_run:
        client.sync_time()

    order_manager = OrderManager(client, logger=logger)

    # ---- Dispatch by order type ------------------------------------------
    try:
        if order_type == "MARKET":
            order_manager.market_order(symbol, side, quantity)
        elif order_type == "LIMIT":
            order_manager.limit_order(symbol, side, quantity, price, args.time_in_force)
        elif order_type == "STOP":
            order_manager.stop_limit_order(
                symbol, side, quantity, price, stop_price, args.time_in_force
            )
    except (BinanceAPIError, BinanceNetworkError):
        # Details already logged/printed inside OrderManager._submit
        return 1
    except Exception as exc:  # noqa: BLE001 - final safety net, log unexpected errors
        logger.exception(f"Unexpected error while placing order: {exc}")
        print(f"\nUNEXPECTED ERROR: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())