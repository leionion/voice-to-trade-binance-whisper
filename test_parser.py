"""Unit tests for intent parser."""

from intent_parser import parse_intent


def test_buy_market():
    i = parse_intent("buy point five btc at market", "USDT")
    assert i.symbol == "BTCUSDT"
    assert i.side == "BUY"
    assert i.order_type == "MARKET"
    assert i.quantity == 0.5
    assert i.price is None
    assert i.parse_error is None


def test_limit_sell():
    i = parse_intent("limit sell 0.5 btc at 69500", "USDT")
    assert i.symbol == "BTCUSDT"
    assert i.side == "SELL"
    assert i.order_type == "LIMIT"
    assert i.quantity == 0.5
    assert i.price == 69500
    assert i.parse_error is None


def test_buy_half():
    i = parse_intent("buy half a bitcoin market", "USDT")
    assert i.symbol == "BTCUSDT"
    assert i.side == "BUY"
    assert i.quantity == 0.5


def test_usdt_quantity():
    i = parse_intent("short 200 USDT ETH limit 3200", "USDT")
    assert i.symbol == "ETHUSDT"
    assert i.side == "SELL"
    assert i.quantity_in_usdt is True
    assert i.quantity == 200
    assert i.price == 3200


if __name__ == "__main__":
    test_buy_market()
    test_limit_sell()
    test_buy_half()
    test_usdt_quantity()
    print("All parser tests passed.")
