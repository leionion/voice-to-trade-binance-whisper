"""
Binance executor — place orders (paper or live) via python-binance.
"""

from dataclasses import dataclass
from typing import Any, Optional

from intent_parser import ParsedIntent


@dataclass
class OrderResult:
    success: bool
    order_id: Optional[str] = None
    status: Optional[str] = None
    avg_price: Optional[float] = None
    executed_qty: Optional[float] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    raw_response: Optional[dict] = None


def _get_client(config: dict, paper: bool):
    """Create Binance client."""
    from binance.client import Client
    api_key = config.get("api_key") or "dummy"
    api_secret = config.get("api_secret") or "dummy"
    testnet = config.get("testnet", False)

    if paper:
        # Paper mode: we never send real orders; use dummy or testnet
        if testnet and api_key != "dummy":
            return Client(api_key=api_key, api_secret=api_secret, testnet=True)
        return None

    return Client(api_key=api_key, api_secret=api_secret, testnet=testnet)


def _get_client_public():
    """Public client for price/orderbook (no keys needed)."""
    from binance.client import Client
    return Client("", "")


def _get_current_price(client, symbol: str) -> Optional[float]:
    """Fetch current market price."""
    c = client if client else _get_client_public()
    try:
        ticker = c.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
    except Exception:
        return None


def _get_symbol_info(client, symbol: str) -> Optional[dict]:
    """Get lot size / step info."""
    try:
        c = client if client else _get_client_public()
        info = c.get_exchange_info()
        for s in info.get("symbols", []):
            if s["symbol"] == symbol:
                return s
    except Exception:
        pass
    return None


def _round_quantity(symbol_info: Optional[dict], qty: float, symbol: str) -> float:
    """Round quantity to exchange lot size."""
    if not symbol_info:
        if qty >= 1:
            return round(qty, 2)
        return round(qty, 5)
    for f in symbol_info.get("filters", []):
        if f.get("filterType") == "LOT_SIZE":
            step = float(f.get("stepSize", "0.001"))
            # Safely derive precision from step (handles 1.0, 0.001, 1e-5)
            step_str = f"{step:.10f}".rstrip("0")
            if "." in step_str:
                prec = len(step_str.split(".")[-1])
            else:
                prec = 5
            prec = max(1, min(prec, 8))
            return round(qty - (qty % step), prec)
    return round(qty, 5)


def execute_order(
    intent: ParsedIntent,
    config: dict,
    paper: bool,
) -> OrderResult:
    """
    Execute or simulate order.
    Paper: validate, fetch price, log, do not place.
    Live: place real order.
    """
    import time
    start = time.perf_counter()

    if intent.parse_error:
        return OrderResult(success=False, error=f"Parse error: {intent.parse_error}")

    symbol = intent.symbol
    side = intent.side
    order_type = intent.order_type
    qty = intent.quantity
    qty_in_usdt = intent.quantity_in_usdt
    price = intent.price

    client = _get_client(config, paper)
    price_fetch = _get_current_price(client, symbol)
    if price_fetch is None:
        return OrderResult(success=False, error=f"Could not fetch price for {symbol}")

    # Convert USDT quantity to base quantity if needed
    if qty_in_usdt:
        qty = qty / price_fetch

    # Apply max_order_usdt cap
    max_usdt = config.get("max_order_usdt", 500)
    usdt_value = qty * (price or price_fetch)
    if usdt_value > max_usdt:
        return OrderResult(
            success=False,
            error=f"Order ${usdt_value:.0f} exceeds max_order_usdt ${max_usdt}",
        )

    symbol_info = _get_symbol_info(client, symbol) if not paper else None
    qty = _round_quantity(symbol_info, qty, symbol)

    if paper:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        if order_type == "MARKET":
            return OrderResult(
                success=True,
                order_id="PAPER",
                status="FILLED",
                avg_price=price_fetch,
                executed_qty=qty,
                latency_ms=elapsed_ms,
                raw_response={"paper": True, "would_fill_at": price_fetch},
            )
        return OrderResult(
            success=True,
            order_id="PAPER",
            status="OPEN (GTC)",
            avg_price=price,
            executed_qty=0,
            latency_ms=elapsed_ms,
            raw_response={"paper": True, "limit_price": price},
        )

    if not client:
        return OrderResult(success=False, error="No API credentials for live mode")

    try:
        if order_type == "MARKET":
            if side == "BUY":
                order = client.order_market_buy(symbol=symbol, quantity=qty)
            else:
                order = client.order_market_sell(symbol=symbol, quantity=qty)
        else:
            from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_LIMIT, TIME_IN_FORCE_GTC
            order = client.create_order(
                symbol=symbol,
                side=SIDE_BUY if side == "BUY" else SIDE_SELL,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,
                quantity=qty,
                price=f"{price:.2f}",
            )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return OrderResult(
            success=True,
            order_id=str(order.get("orderId", "")),
            status=order.get("status", ""),
            avg_price=float(order.get("avgPrice") or order.get("price") or 0),
            executed_qty=float(order.get("executedQty") or 0),
            latency_ms=elapsed_ms,
            raw_response=order,
        )
    except Exception as e:
        return OrderResult(success=False, error=str(e))
