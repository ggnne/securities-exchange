from typing import OrderedDict

from .enums import OrderType, OrderStatus, MarketSide
from .order import Order
from .bookside import BookSide


class OrderBook:

    """
    Class representing an order book in a securities exchange.

    Attributes:
        Bid (BookSide): The buy side of the order book.
        Ask (BookSide): The sell side of the order book.

    Methods:
        process_order: Processes an incoming order, matching and filling as needed.

    """

    def __init__(self, allow_market_queue: bool = False):
        """
        Initialize an OrderBook instance.

        Args:
            allow_market_queue (bool): Flag indicating whether market orders can be queued.
        """
        # Create instances of BookSide for buy (Bid) and sell (Ask) sides
        self.Bid = BookSide(allow_market_queue = allow_market_queue)
        self.Ask = BookSide(side = MarketSide.SELL, allow_market_queue = allow_market_queue)

    def process_order(self, order: Order, orders: OrderedDict[str, Order]):

        """
        Process an incoming order, matching and filling as needed.

        Args:
            order (Order): The incoming order to be processed.
            orders (OrderedDict): Dictionary containing all existing orders.
        """

        # Determine the sides for matching and adding based on the order's side
        if (order.side == MarketSide.BUY):
            side_for_match = self.Ask
            side_to_add = self.Bid
        else:
            side_for_match = self.Bid
            side_to_add = self.Ask
        
        if order.type == OrderType.MARKET:
            
            # Continue processing the order until it is fully filled or cannot be matched
            while (order.status != OrderStatus.FILLED and side_for_match.liquid()):
                side_for_match.match(order, orders)
        
        else:

            # Continue processing the order until it is fully filled or cannot be matched
            while (order.status != OrderStatus.FILLED and \
                   ((side_for_match.liquid() and side_for_match.is_be(order.price)) or (side_for_match.has_market()))):
                side_for_match.match(order, orders)
        
       # If the order is still not fully filled, add it to the appropriate side of the order book
        if (order.status != OrderStatus.FILLED):
            side_to_add.add(order)