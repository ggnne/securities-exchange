import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s][%(asctime)s]: %(message)s")

from collections import deque
from datetime import datetime

from pydantic import validate_call

from .enums import OrderType, OrderStatus, MarketSide


class Order:
    
    @validate_call
    def __init__(self, ticker: str, type: OrderType, side: MarketSide, size: int, price: float = None):
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

        if self.price is not None and self.type == OrderType.MARKET:
            logging.warning("Market orders will ignore 'price'. Price attribute set to None")
            self.price = None        

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

        filled_quantity = min(filled_quantity, self.residual_size)

        self.avg_fill_price *= (self.size - self.residual_size)
        self.avg_fill_price += filled_quantity * at_price
        self.avg_fill_price /= (self.size - self.residual_size + filled_quantity)

        self.residual_size -= filled_quantity

        if self.residual_size  == 0:
            self.status = OrderStatus.FILLED
            logging.info(f"Order {self.id} filled {filled_quantity} units at price {at_price} with order {matched_order_id}")
        elif self.residual_size > 0:
            self.status = OrderStatus.PARTIALLY_FILLED
            logging.info(f"Order {self.id} partially filled {filled_quantity} units at price {at_price} with order {matched_order_id}")
        self.matches.append((filled_quantity, at_price, matched_order_id))
