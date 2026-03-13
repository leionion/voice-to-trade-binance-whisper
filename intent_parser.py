"""
Intent parser — natural language → trading intent (symbol, side, type, qty, price).
Handles: "buy 0.5 btc at market", "limit sell 0.5 btc at 69500", "short 200 USDT ETH limit 3200"
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedIntent:
    symbol: str
    side: str
    order_type: str
    quantity: float
    quantity_in_usdt: bool  # True = quantity is USDT value, False = base asset
    price: Optional[float]
    raw_text: str
    parse_error: Optional[str] = None


# Common ticker aliases
SYMBOL_ALIASES = {
    "btc": "BTC",
    "bitcoin": "BTC",
    "eth": "ETH",
    "ethereum": "ETH",
    "sol": "SOL",
    "solana": "SOL",
    "bnb": "BNB",
    "xrp": "XRP",
    "ripple": "XRP",
    "ada": "ADA",
    "cardano": "ADA",
    "doge": "DOGE",
    "avax": "AVAX",
    "avalanche": "AVAX",
    "link": "LINK",
    "chainlink": "LINK",
    "dot": "DOT",
    "polkadot": "DOT",
    "matic": "MATIC",
    "polygon": "MATIC",
}

# Words to reject as symbols (Whisper hallucinations from silence/noise)
SYMBOL_BLOCKLIST = {"you", "the", "a", "i", "me", "oh", "um", "uh", "so", "and", "or"}

# Word forms for numbers
WORD_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "hundred": 100, "half": 0.5, "quarter": 0.25,
    "point": None,  # "point five" = 0.5
}


def _parse_quantity(text: str) -> tuple[Optional[float], bool]:
    """Extract quantity and whether it's in USDT. Returns (qty, is_usdt)."""
    text_lower = text.lower().strip()

    # Check for USDT amount: "200 USDT", "200 usdt", "100 dollars"
    usdt_match = re.search(
        r"(?:^|\s)(\d+(?:\.\d+)?)\s*(?:usdt|usd|dollars?)\b",
        text_lower,
        re.IGNORECASE,
    )
    if usdt_match:
        return float(usdt_match.group(1)), True

    # "point five" / "point 5" / "0.5"
    point_match = re.search(r"point\s+(\d+(?:\.\d+)?)", text_lower)
    if point_match:
        return float("0." + point_match.group(1).replace(".", "")), False
    # "point five" / "point one" (word form)
    if re.search(r"point\s+five\b", text_lower):
        return 0.5, False
    if re.search(r"point\s+one\b", text_lower):
        return 0.1, False
    if re.search(r"point\s+two\b", text_lower):
        return 0.2, False
    if re.search(r"point\s+two\s+five\b", text_lower):
        return 0.25, False

    # "half" / "quarter"
    if "half" in text_lower and "a " in text_lower:
        return 0.5, False
    if re.search(r"\bhalf\b", text_lower):
        return 0.5, False
    if re.search(r"\bquarter\b", text_lower):
        return 0.25, False

    # Numeric: "0.5", "1.5", "200"
    num_match = re.search(r"\b(\d+(?:\.\d+)?)\b", text_lower)
    if num_match:
        return float(num_match.group(1)), False

    return None, False


def _parse_symbol(text: str, default_quote: str = "USDT") -> Optional[str]:
    """Extract symbol and normalize to SYMBOLUSDT."""
    text_lower = text.lower()
    for alias, base in SYMBOL_ALIASES.items():
        if alias in text_lower:
            return f"{base}{default_quote}"
    # Try uppercase symbol pattern: BTC, ETH
    sym_match = re.search(
        r"\b([A-Z]{2,10})(?:USDT|USD)?\b", text, re.IGNORECASE
    )
    if sym_match:
        base = sym_match.group(1).upper()
        if base in ["USDT", "USD", "BUSD"]:
            return None
        if base.lower() in SYMBOL_BLOCKLIST:
            return None
        return f"{base}{default_quote}"
    return None


def _parse_side(text: str) -> Optional[str]:
    """Extract side: BUY or SELL."""
    t = text.lower()
    if any(w in t for w in ["buy", "long", "bid"]):
        return "BUY"
    if any(w in t for w in ["sell", "short", "ask"]):
        return "SELL"
    return None


def _parse_order_type(text: str) -> str:
    """Extract order type: MARKET or LIMIT."""
    t = text.lower()
    if any(w in t for w in ["limit", "at ", "price"]):
        return "LIMIT"
    if any(w in t for w in ["market", "at market"]):
        return "MARKET"
    return "MARKET"


def _parse_price(text: str) -> Optional[float]:
    """Extract limit price."""
    # "at 69500", "at 3200", "limit 3200"
    match = re.search(r"(?:at|@|limit\s+)(?:price\s+)?(\d+(?:[.,]\d+)?)", text, re.I)
    if match:
        s = match.group(1).replace(",", "")
        return float(s)
    # Trailing number often is price: "limit sell 0.5 btc 69500"
    nums = re.findall(r"\b(\d+(?:\.\d+)?)\b", text)
    if len(nums) >= 2:
        # Last large number is often price
        for n in reversed(nums):
            v = float(n)
            if v > 100:
                return v
    return None


def parse_intent(transcript: str, default_quote: str = "USDT") -> ParsedIntent:
    """
    Parse natural language transcript into trading intent.
    Returns ParsedIntent with parse_error set if parsing fails.
    """
    text = transcript.strip()
    if not text:
        return ParsedIntent(
            symbol="",
            side="",
            order_type="MARKET",
            quantity=0.0,
            quantity_in_usdt=False,
            price=None,
            raw_text=text,
            parse_error="Empty transcript",
        )

    symbol = _parse_symbol(text, default_quote)
    side = _parse_side(text)
    price = _parse_price(text)
    order_type = "LIMIT" if price is not None else "MARKET"
    qty, qty_in_usdt = _parse_quantity(text)

    errors = []
    if not symbol:
        errors.append("Could not identify symbol (e.g. BTC, ETH)")
    if not side:
        errors.append("Could not identify side (buy/sell)")
    if qty is None or qty <= 0:
        errors.append("Could not identify valid quantity")

    if errors:
        return ParsedIntent(
            symbol=symbol or "",
            side=side or "",
            order_type=order_type,
            quantity=qty or 0.0,
            quantity_in_usdt=qty_in_usdt,
            price=price,
            raw_text=text,
            parse_error="; ".join(errors),
        )

    return ParsedIntent(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=qty,
        quantity_in_usdt=qty_in_usdt,
        price=price,
        raw_text=text,
    )
