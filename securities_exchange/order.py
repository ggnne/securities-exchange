import logging
from collections import deque
from datetime import datetime
from pydantic import validate_call
from .enums import OrderType, OrderStatus, MarketSide


class Order:

    """
    Class representing an order in the securities exchange.

    Attributes:
        ticker (str): Ticker symbol for the order.
        type (OrderType): Type of the order (Market or Limit).
        side (MarketSide): Side of the market (Buy or Sell).
        size (int): Size of the order.
        price (float): Price of the order (optional for Market orders).
        timestamp (int): Timestamp of order creation.
        status (OrderStatus): Status of the order (UNFILLED, PARTIALLY_FILLED, FILLED).
        matches (deque): Queue to store order matches.
        residual_size (int): Remaining size to be filled.
        avg_fill_price (float): Average fill price of the order.
        error (bool): Flag indicating if there's an error in the order.

    Methods:
        update: Updates the order status and properties after a fill.
    """    
    
    @validate_call
    def __init__(self, ticker: str, type: OrderType, side: MarketSide, size: int, price: float = None):

        """
        Initialize an order with the provided parameters.

        Args:
            ticker (str): Ticker symbol for the order.
            type (OrderType): Type of the order (Market or Limit).
            side (MarketSide): Side of the market (Buy or Sell).
            size (int): Size of the order.
            price (float): Price of the order (optional for Market orders).
        """

        # Set timestamp to current time in microseconds
        self.timestamp = int(datetime.now().timestamp() * 1e6)
        self.ticker = ticker
        self.type = type
        self.side = side
        self.size = size
        self.price = price
        self.status = OrderStatus.UNFILLED
        self.matches = deque()
        self.residual_size = size
        self.avg_fill_price = 0
        self.error = False

        # Handle special cases for market orders
        if self.price is not None and self.type == OrderType.MARKET:
            logging.warning("Market orders will ignore 'price'. Price attribute set to None")
            self.price = None        

        # Generate a unique order ID based on order attributes
        keys = [self.timestamp, self.ticker, self.type.name, self.side.name, self.size]
        if self.price is not None and self.type == OrderType.LIMIT:
            keys.append(f"@{self.price}")
        self.id = ''.join(map(str, keys))


    def __repr__(self) -> str:
        d = {k: v for k, v in self.__dict__.items()}
        d["type"] = d["type"].name
        d["side"] = d["side"].name
        d["status"] = d["status"].name
        d["matches"] = len(d["matches"])
        if d["price"] is None:
            del d["price"] 
        _repr = ",\n      ".join(map(lambda x: f"{x[0]} = {x[1]}", d.items()))
        return f"Order({_repr})"
    
    
    def update(self, filled_quantity: int, at_price: float, matched_order_id: str):

        """
        Update the order after a fill.

        Args:
            filled_quantity (int): Quantity filled in the latest match.
            at_price (float): Price at which the latest match occurred.
            matched_order_id (str): ID of the order that was matched.
        """

        # Ensure filled_quantity does not exceed the remaining size
        filled_quantity = min(filled_quantity, self.residual_size)

        # Update average fill price
        self.avg_fill_price *= (self.size - self.residual_size)
        self.avg_fill_price += filled_quantity * at_price
        self.avg_fill_price /= (self.size - self.residual_size + filled_quantity)

        # Update residual size
        self.residual_size -= filled_quantity

        # Update order status based on residual size
        if self.residual_size == 0:
            self.status = OrderStatus.FILLED
            logging.info(f"Order {self.id} filled {filled_quantity} units at price {at_price} with order {matched_order_id}")
        elif self.residual_size > 0:
            self.status = OrderStatus.PARTIALLY_FILLED
            logging.info(f"Order {self.id} partially filled {filled_quantity} units at price {at_price} with order {matched_order_id}")

        # Record the match in the matches queue
        self.matches.append((filled_quantity, at_price, matched_order_id))
