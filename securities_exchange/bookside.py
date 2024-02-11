from collections import defaultdict, deque, Counter, OrderedDict
from heapq import heapify, heappop, heappush
from typing import OrderedDict

from .enums import OrderType, OrderStatus, MarketSide
from .order import Order


class BookSide:

    """
    Class representing a side (Buy or Sell) of the order book.

    Attributes:
        side (MarketSide): The side of the market (Buy or Sell).
        _allow_market_queue (bool): Flag indicating whether market orders are allowed to be queued.
        _sign (int): Sign used for heap comparisons based on market side.
        market_orders (deque): Queue to store market orders.
        limit_orders (defaultdict): Dictionary to store limit orders as dequeues.
        _bestHeap (list): Heap structure to efficiently find the best price.
        bestP (float): Best price on the order book.
        bestV (int): Best volume at the best price.
        volumes (Counter): Counter to track volumes at different prices.

    Methods:
        fill: Match and fill two orders.
        match: Match and fill an order with the best available order.
        add: Add an order to the order book.
        liquid: Check if the order book is liquid.
        has_market: Check if there are market orders in the queue.
    """

    def __init__(self, side: MarketSide = MarketSide.BUY, allow_market_queue: bool = False):

        """
        Initialize a BookSide instance with the given parameters.

        Args:
            side (MarketSide): The side of the market (Buy or Sell).
            allow_market_queue (bool): Flag indicating whether market orders are allowed to be queued.
        """
        
        self.side = side
        self._allow_market_queue = allow_market_queue
        self._sign = -1 if self.side == MarketSide.BUY else 1
        self.market_orders = deque()
        self.limit_orders = defaultdict(deque)
        self._bestHeap = []
        heapify(self._bestHeap)
        self.bestP = None
        self.bestV = 0  
        self.volumes = Counter()


    def fill(self, orderA: Order, orderB: Order):
        
        """
        FIll two orders with each other.

        Args:
            orderA (Order): First order to match.
            orderB (Order): Second order to match.
        """

        if orderA.type == OrderType.MARKET:
            at_price = orderB.price
        elif orderB.type == OrderType.MARKET:
            at_price = orderA.price
        else:
            # Determine price based on market side and order sides
            if self.side == MarketSide.BUY:
                if orderA.side == MarketSide.BUY:
                    at_price = orderA.price
                else:
                    at_price = orderB.price
            else:
                if orderA.side == MarketSide.SELL:
                    at_price = orderA.price
                else:
                    at_price = orderB.price
                    
        resA = orderA.residual_size
        resB = orderB.residual_size
        orderA.update(resB, at_price, orderB.id)
        orderB.update(resA, at_price, orderA.id)


    def match(self, order: Order, orders: OrderedDict[str, Order]):

        """
        Match an order with the best available order and update book.

        Args:
            order (Order): The order to match.
            orders (OrderedDict): Dictionary containing all existing orders.
        """
        
        if (order.type == OrderType.LIMIT and self.has_market()) and self._allow_market_queue:

            # If order is LIMIT and there are market orders in the queue, match with the first market order in the queue
            queued_mo = orders[self.market_orders[0]]
            self.fill(order, queued_mo)
            if queued_mo.status == OrderStatus.FILLED:
                self.market_orders.popleft()

        else:

            # Match with the best limit order
            queued_lo = orders[self.limit_orders[self.bestP][0]]
            self.fill(order, queued_lo)

            self.volumes[self.bestP] -= queued_lo.matches[-1][0]
            self.bestV -= queued_lo.matches[-1][0]
            if queued_lo.status == OrderStatus.FILLED:
                # If the matched limit order is fully filled remove it from the queue and update order book
                self.limit_orders[self.bestP].popleft()
                if len(self.limit_orders[self.bestP]) == 0:
                    del self.limit_orders[self.bestP]
                    del self.volumes[self.bestP]
                    if len(self._bestHeap):
                        self.bestP = self._sign * heappop(self._bestHeap)
                        self.bestV = self.volumes[self.bestP]
                    else:
                        self.bestP = None
                        self.bestV = 0                


    def add(self, order: Order):

        """
        Add an order to the side of the order book.

        Args:
            order (Order): The order to be added.
        """

        if (order.type == OrderType.MARKET) and self._allow_market_queue:
            # If the order is MARKET and market queue is allowed, add to market queue
            self.market_orders.append(order.id)

        elif order.type == OrderType.LIMIT:
            # If the order is LIMIT, add to limit orders and update order book
            if self.bestP is None:
                self.bestP = order.price
                self.bestV = order.residual_size                
            elif (self.bestP < order.price and self.side == MarketSide.BUY) or \
                 (self.bestP > order.price and self.side == MarketSide.SELL):
                heappush(self._bestHeap, self._sign * self.bestP)
                self.bestP = order.price
                self.bestV = order.residual_size
            elif self.bestP == order.price:
                self.bestV += order.residual_size
            elif order.price not in self.limit_orders:
                heappush(self._bestHeap, self._sign * order.price)
            
            self.limit_orders[order.price].append(order.id)
            self.volumes[order.price] += order.residual_size


    def liquid(self) -> bool:
        """
        Check if the side of the order book has liquidity.

        Returns:
            bool: True if the side of the order book has liquidity, False otherwise.
        """
        return self.bestV > 0
        

    def is_be(self, price) -> bool:
        """
        Compare price with the current bestP, Better or Equal.

        Args:
            price (float): price to compare to bestP

        Returns:
            bool: True if the price is better or equal to bestP, False otherwise.
        """
        if self.side == MarketSide.BUY:
            return self.bestP >= price 
        else:
            return self.bestP <= price 


    def has_market(self) -> bool:
        """
        Check if there are market orders in the queue.

        Returns:
            bool: True if there are market orders, False otherwise.
        """
        return len(self.market_orders) and self._allow_market_queue