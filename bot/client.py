"""
Thin REST client for Binance Futures (USDT-M) Testnet.

Implemented with direct HTTP calls (requests) + HMAC-SHA256 signing so the
signing/request flow is fully visible and auditable, rather than hidden
inside a third-party library. Every outgoing request and incoming response
(or error) is logged.
"""

import hashlib
import hmac
import logging
import time
import urllib.parse
from typing import Any, Dict, Optional

import requests

DEFAULT_BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW_MS = 5000
REQUEST_TIMEOUT_SECONDS = 10


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-2xx / error-coded response."""

    def __init__(self, message: str, status_code: Optional[int] = None, payload: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


class BinanceNetworkError(Exception):
    """Raised for connection/timeout failures talking to Binance."""


class BinanceFuturesClient:
    """
    Minimal client wrapper around the Binance Futures Testnet REST API.

    dry_run=True skips the actual HTTP call and returns a simulated response,
    which is useful for testing the CLI/logging pipeline without live keys.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        logger: Optional[logging.Logger] = None,
        dry_run: bool = False,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.logger = logger or logging.getLogger("trading_bot")
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        self._time_offset_ms = 0  # server_time - local_time, corrects for clock drift

    def sync_time(self) -> None:
        """
        Fetch Binance server time and compute the offset from local time.
        Call this once before placing orders to avoid error -1021
        ("Timestamp for this request was ... ahead of the server's time"),
        which happens whenever the local clock drifts from Binance's clock.
        """
        if self.dry_run:
            return
        try:
            server_time = self._request("GET", "/fapi/v1/time", signed=False)
            server_ms = server_time.get("serverTime")
            if server_ms is not None:
                local_ms = int(time.time() * 1000)
                self._time_offset_ms = server_ms - local_ms
                self.logger.debug(f"Time sync: offset={self._time_offset_ms}ms")
        except (BinanceAPIError, BinanceNetworkError) as exc:
            # Non-fatal: fall back to local time (offset stays 0) and let the
            # order request surface any resulting timestamp error normally.
            self.logger.warning(f"Could not sync server time, using local clock: {exc}")

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _sign(self, params: Dict[str, Any]) -> str:
        query_string = urllib.parse.urlencode(params, doseq=True)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = True,
    ) -> Dict[str, Any]:
        params = dict(params or {})

        if signed:
            params["timestamp"] = int(time.time() * 1000) + self._time_offset_ms
            params["recvWindow"] = RECV_WINDOW_MS
            params["signature"] = self._sign(params)

        url = f"{self.base_url}{path}"
        # Never log the API secret or the computed signature in full.
        safe_params = {k: v for k, v in params.items() if k != "signature"}
        self.logger.debug(f"REQUEST {method} {url} | params={safe_params}")

        if self.dry_run:
            simulated = self._simulate_response(params)
            self.logger.debug(f"RESPONSE (dry-run simulated) | {simulated}")
            return simulated

        try:
            response = self.session.request(
                method, url, params=params, timeout=REQUEST_TIMEOUT_SECONDS
            )
        except requests.exceptions.Timeout as exc:
            self.logger.error(f"NETWORK TIMEOUT calling {url}: {exc}")
            raise BinanceNetworkError(f"Request to Binance timed out: {exc}") from exc
        except requests.exceptions.ConnectionError as exc:
            self.logger.error(f"NETWORK ERROR calling {url}: {exc}")
            raise BinanceNetworkError(f"Could not connect to Binance: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            self.logger.error(f"REQUEST ERROR calling {url}: {exc}")
            raise BinanceNetworkError(f"Request to Binance failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {"raw_text": response.text}

        if response.status_code != 200:
            self.logger.error(
                f"RESPONSE ERROR {response.status_code} | {payload}"
            )
            raise BinanceAPIError(
                message=payload.get("msg", f"HTTP {response.status_code}"),
                status_code=response.status_code,
                payload=payload,
            )

        self.logger.debug(f"RESPONSE {response.status_code} | {payload}")
        return payload

    def _simulate_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Used only when dry_run=True (no live API keys / no network)."""
        now_ms = int(time.time() * 1000)
        order_type = params.get("type", "MARKET")
        price = params.get("price")
        return {
            "orderId": now_ms,
            "symbol": params.get("symbol"),
            "status": "FILLED" if order_type == "MARKET" else "NEW",
            "side": params.get("side"),
            "type": order_type,
            "origQty": params.get("quantity"),
            "executedQty": params.get("quantity") if order_type == "MARKET" else "0",
            "avgPrice": price if order_type == "MARKET" and price else "0.0",
            "price": price or "0.0",
            "updateTime": now_ms,
            "_simulated": True,
        }

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def ping(self) -> Dict[str, Any]:
        return self._request("GET", "/fapi/v1/ping", signed=False)

    def place_order(self, **order_params) -> Dict[str, Any]:
        """
        Places a new order via POST /fapi/v1/order.
        order_params should already be validated/normalized by the caller.
        """
        return self._request("POST", "/fapi/v1/order", params=order_params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )