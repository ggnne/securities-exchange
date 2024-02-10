from enum import Enum, auto


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()


class MarketSide(Enum):
    BUY = auto()
    SELL = auto()


class OrderStatus(Enum):
    UNFILLED = auto()
    PARTIALLY_FILLED = auto()
    FILLED = auto()
