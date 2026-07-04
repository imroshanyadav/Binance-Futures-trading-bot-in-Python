"""
Input validation for the trading bot CLI.

Every function raises ValueError with a clear, user-facing message on
invalid input, and returns a normalized value on success.
"""

import re

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP"}  # STOP = bonus stop-limit order
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


def validate_symbol(symbol: str) -> str:
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol is required, e.g. BTCUSDT")
    symbol = symbol.strip().upper()
    if not SYMBOL_PATTERN.match(symbol):
        raise ValueError(
            f"Invalid symbol format: '{symbol}'. Expected something like 'BTCUSDT'."
        )
    return symbol


def validate_side(side: str) -> str:
    if not side or not isinstance(side, str):
        raise ValueError("Side is required: BUY or SELL")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Invalid side '{side}'. Must be one of {sorted(VALID_SIDES)}")
    return side


def validate_order_type(order_type: str) -> str:
    if not order_type or not isinstance(order_type, str):
        raise ValueError("Order type is required: MARKET, LIMIT, or STOP")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be one of {sorted(VALID_ORDER_TYPES)}"
        )
    return order_type


def validate_quantity(quantity) -> float:
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity must be a number, got '{quantity}'")
    if quantity <= 0:
        raise ValueError(f"Quantity must be greater than 0, got {quantity}")
    return quantity


def validate_price(price, order_type: str, field_name: str = "price"):
    """
    Price is required for LIMIT and STOP orders, forbidden/ignored for MARKET.
    Returns a validated float, or None if not applicable.
    """
    if order_type == "MARKET":
        return None

    if price is None:
        raise ValueError(f"'{field_name}' is required for {order_type} orders")
    try:
        price = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"'{field_name}' must be a number, got '{price}'")
    if price <= 0:
        raise ValueError(f"'{field_name}' must be greater than 0, got {price}")
    return price


def validate_stop_price(stop_price, order_type: str):
    """Stop price is required only for STOP orders (bonus feature)."""
    if order_type != "STOP":
        return None
    return validate_price(stop_price, "STOP", field_name="stop_price")
