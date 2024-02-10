import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s][%(asctime)s]: %(message)s")

from collections import OrderedDict

from typing import OrderedDict

from .enums import OrderType, OrderStatus
from .order import Order
from .orderbook import OrderBook


class SecuritiesExchange:
    
    def __init__(self, allow_market_queue: bool = True):
        self.orders = OrderedDict()
        self.rejected_orders = OrderedDict()
        self.markets = {}
        self._allow_market_queue = allow_market_queue


    def _init_market(self, ticker: str):
        self.markets[ticker] = OrderBook(allow_market_queue=self._allow_market_queue)


    def _validate_order(self, order: Order):
        
        msg = f"Order {order.id} has been REJECTED."
        if (order.price is None or order.price <= 0) and (order.type == OrderType.LIMIT):
            order.error = True
            msg += "\n\t\t\t\t\t- LIMIT orders require a non-null positive PRICE."

        if (order.size <= 0):
            order.error = True
            msg += "\n\t\t\t\t\t- Orders require a non-null positive SIZE."
        
        if order.error:
            logging.error(msg)


    def submit_order(self, order: Order) -> bool:

        self._validate_order(order)

        if order.error:
            self.rejected_orders[order.id] = order
            return False

        if order.ticker not in self.markets:
            self._init_market(order.ticker)

        self.orders[order.id] = order

        logging.info(f"Order {order.id} submitted for {order.ticker}")
        
        self.markets[order.ticker].process_order(order, self.orders)

        if self._allow_market_queue:
            if (order.type == OrderType.MARKET) and (order.status == OrderStatus.UNFILLED):             
                logging.info(f"Order {order.id} has been added to the Market Orders queue for the full amount.")
            elif (order.type == OrderType.MARKET) and (order.status == OrderStatus.PARTIALLY_FILLED):
                logging.info(f"Order {order.id} has been added to the Market Orders queue for the residual amount of {order.residual_size} units.")
        else:
            if (order.type == OrderType.MARKET) and (order.status == OrderStatus.UNFILLED):             
                logging.info(f"Order {order.id} couldn't be matched.")
        
        return True


    def get_order(self, order_id: str) -> Order:

        if order_id in self.orders:
            return self.orders.get(order_id)

        return self.rejected_orders.get(order_id)