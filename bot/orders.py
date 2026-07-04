"""
Order placement logic — builds Binance-compliant order params from
validated CLI input, submits them via the client layer, and logs/prints
a clean summary of the request and response.
"""

import logging
from typing import Any, Dict, Optional

from bot.client import BinanceAPIError, BinanceFuturesClient, BinanceNetworkError


class OrderManager:
    def __init__(self, client: BinanceFuturesClient, logger: Optional[logging.Logger] = None):
        self.client = client
        self.logger = logger or logging.getLogger("trading_bot")

    # ------------------------------------------------------------------ #
    def _submit(self, request_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Shared submit/log/print flow for all order types."""
        self.logger.info(f"Placing order: {request_summary}")
        print("\n--- Order Request ---")
        for k, v in request_summary.items():
            print(f"{k}: {v}")

        try:
            response = self.client.place_order(**request_summary)
        except BinanceAPIError as exc:
            self.logger.error(f"Order REJECTED by API: {exc} | payload={exc.payload}")
            print("\n--- Order FAILED ---")
            print(f"Reason: {exc}")
            raise
        except BinanceNetworkError as exc:
            self.logger.error(f"Order failed due to network error: {exc}")
            print("\n--- Order FAILED (network error) ---")
            print(f"Reason: {exc}")
            raise

        self.logger.info(f"Order response: {response}")
        print("\n--- Order Response ---")
        print(f"orderId     : {response.get('orderId')}")
        print(f"status      : {response.get('status')}")
        print(f"executedQty : {response.get('executedQty', 'N/A')}")
        print(f"avgPrice    : {response.get('avgPrice', 'N/A')}")
        print("\nSUCCESS: order submitted to Binance Futures Testnet.")
        return response

    # ------------------------------------------------------------------ #
    def market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        request_summary = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity,
        }
        return self._submit(request_summary)

    def limit_order(
        self, symbol: str, side: str, quantity: float, price: float, time_in_force: str = "GTC"
    ) -> Dict[str, Any]:
        request_summary = {
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "quantity": quantity,
            "price": price,
            "timeInForce": time_in_force,
        }
        return self._submit(request_summary)

    def stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_price: float,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """Bonus feature: STOP order (stop-limit) — triggers a limit order at `price`
        once the market reaches `stop_price`."""
        request_summary = {
            "symbol": symbol,
            "side": side,
            "type": "STOP",
            "quantity": quantity,
            "price": price,
            "stopPrice": stop_price,
            "timeInForce": time_in_force,
        }
        return self._submit(request_summary)
