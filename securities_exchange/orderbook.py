import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s][%(asctime)s]: %(message)s")

from typing import OrderedDict

from .enums import OrderType, OrderStatus, MarketSide
from .order import Order
from .bookside import BookSide


class OrderBook:

    def __init__(self, allow_market_queue: bool = True):
        self.Bid = BookSide(allow_market_queue = allow_market_queue)
        self.Ask = BookSide(side = MarketSide.SELL, allow_market_queue = allow_market_queue)

    def process_order(self, order: Order, orders: OrderedDict[str, Order]) -> bool:

        if (order.side == MarketSide.BUY):
            side_for_match = self.Ask
            side_to_add = self.Bid
        else:
            side_for_match = self.Bid
            side_to_add = self.Ask
            
        while ((order.status != OrderStatus.FILLED) and (side_for_match.liquid() or (order.type == OrderType.LIMIT and side_for_match.has_market()))):
            side_for_match.match(order, orders)
        
        if (order.status != OrderStatus.FILLED):
            side_to_add.add(order)