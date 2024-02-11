import logging
from collections import OrderedDict

from typing import OrderedDict

from .enums import OrderType, OrderStatus
from .order import Order
from .orderbook import OrderBook


class SecuritiesExchange:
    
    """
    Class representing a securities exchange.

    Attributes:
        orders (OrderedDict): Dictionary to store all submitted orders.
        rejected_orders (OrderedDict): Dictionary to store rejected orders.
        markets (dict): Dictionary to store order books for different tickers.
        _allow_market_queue (bool): Flag indicating whether market orders can be queued.

    Methods:
        _init_market: Initializes an order book for a new ticker.
        _validate_order: Validates the properties of an order and logs errors if any.
        submit_order: Submits an order to the exchange for processing.
        get_order: Retrieves an order based on its ID.
    """

    def __init__(self, allow_market_queue: bool = False, verbose = False):

        """
        Initialize a SecuritiesExchange instance.

        Args:
            allow_market_queue (bool): Flag indicating whether market orders can be queued.
        """

        self.orders = OrderedDict()
        self.rejected_orders = OrderedDict()
        self.markets = {}
        self._allow_market_queue = allow_market_queue
        
        # Configure logging settings
        if verbose:
            logging.basicConfig(level=logging.INFO, format="[%(levelname)s][%(asctime)s]: %(message)s")


    def _init_market(self, ticker: str):

        """
        Initialize an order book for a new ticker.

        Args:
            ticker (str): Ticker symbol for the market.
        """

        self.markets[ticker] = OrderBook(allow_market_queue=self._allow_market_queue)


    def _validate_order(self, order: Order):
        
        """
        Validate the properties of an order and log errors if any.

        Args:
            order (Order): The order to be validated.
        """
        
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

        """
        Submits an order to the exchange for processing.

        Args:
            order (Order): The order to be submitted.

        Returns:
            bool: True if the order is successfully submitted, False otherwise.
        """

        # Validate the order before processing
        self._validate_order(order)

        if order.error:
            # If the order is invalid, store it in the rejected_orders dictionary and return False
            self.rejected_orders[order.id] = order
            return False

        if order.ticker not in self.markets:
            # If the ticker is not in markets, initialize a new market
            self._init_market(order.ticker)

        # Store the order in the orders dictionary
        self.orders[order.id] = order

        logging.info(f"Order {order.id} submitted for {order.ticker}")
        
        # Process the order in the corresponding market
        self.markets[order.ticker].process_order(order, self.orders)

        # Log information about the order based on the market queue settings
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
        
        """
        Retrieves an order based on its ID.

        Args:
            order_id (str): The ID of the order to retrieve.

        Returns:
            Order: The order corresponding to the given ID.
        """

        if order_id in self.orders:
            return self.orders.get(order_id)

        return self.rejected_orders.get(order_id)