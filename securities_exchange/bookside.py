import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s][%(asctime)s]: %(message)s")

from collections import defaultdict, deque, Counter, OrderedDict
from heapq import heapify, heappop, heappush

from typing import OrderedDict

from .enums import OrderType, OrderStatus, MarketSide
from .order import Order


class BookSide:

    def __init__(self, side: MarketSide = MarketSide.BUY, allow_market_queue: bool = True):
        self.side = side
        self._allow_market_queue = allow_market_queue
        self._sign = -1 if self.side == MarketSide.BUY else 1
        self.market_orders = deque()
        self.limit_orders = defaultdict(deque)
        self._bestHeap = []
        heapify(self._bestHeap)
        self.bestP = None
        self.bestV = 0  
        self.volume = Counter()


    def fill(self, orderA: Order, orderB: Order):
        
        if orderA.type == OrderType.MARKET:
            at_price = orderB.price
        elif orderB.type == OrderType.MARKET:
            at_price = orderA.price
        else:
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

        
        if (order.type == OrderType.LIMIT and self.has_market()) and self._allow_market_queue:

            queued_mo = orders[self.market_orders[0]]
            self.fill(order, queued_mo)
            if queued_mo.status == OrderStatus.FILLED:
                self.market_orders.popleft()

        else:

            queued_lo = orders[self.limit_orders[self.bestP][0]]
            self.fill(order, queued_lo)

            if queued_lo.status == OrderStatus.FILLED :
                self.limit_orders[self.bestP].popleft()
                if len(self.limit_orders[self.bestP]):
                    self.volume[self.bestP] -= queued_lo.matches[-1][0]
                    self.bestV -= queued_lo.matches[-1][0]
                else:
                    del self.limit_orders[self.bestP]
                    del self.volume[self.bestP]
                    if len(self._bestHeap):
                        self.bestP = self._sign * heappop(self._bestHeap)
                        self.bestV = self.volume[self.bestP]
                    else:
                        self.bestP = None
                        self.bestV = 0
            elif queued_lo.status == OrderStatus.PARTIALLY_FILLED:
                self.volume[self.bestP] -= queued_lo.matches[-1][0]
                self.bestV -= queued_lo.matches[-1][0]


    def add(self, order: Order):

        if (order.type == OrderType.MARKET) and self._allow_market_queue:

            self.market_orders.append(order.id)

        else:

            if self.bestP is None:
                self.bestP = order.price
                self.bestV = order.size                
            elif (self.bestP > order.price and self.side == MarketSide.BUY) or (self.bestP < order.price and self.side == MarketSide.SELL):
                heappush(self._bestHeap, self._sign * self.bestP)
                self.bestP = order.price
                self.bestV = order.size
            elif order.price not in self.limit_orders:
                heappush(self._bestHeap, self._sign * order.price)
            
            self.limit_orders[order.price].append(order.id)
            self.volume[order.price] += order.residual_size


    def liquid(self):
        return self.bestP is not None
    

    def has_market(self):
        return len(self.market_orders) and self._allow_market_queue