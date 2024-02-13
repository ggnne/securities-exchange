# Usage

## Overview

The securities-exchange package provides a simple framework for simulating a securities exchange. This package allows you to model and test different order types, market behaviors, and exchange rules.
Installation

## Getting Started

To use the package, you need to import the necessary classes and functions:

```python
from securities_exchange import SecuritiesExchange, Order, OrderType, MarketSide
```

The primary classes include:

- **SecuritiesExchange:** Represents the securities exchange.
- **Order:** Represents an order with specific details like ticker, order type, side, size, and price.
- **OrderType:** Enum defining order types (MARKET, LIMIT).
- **MarketSide:** Enum defining market sides (BUY, SELL).

## Exchange Modes

The `SecuritiesExchange` class has two modes of operation:

1. **Default Mode:**
	- The exchange takes Market Orders and tries to fill them given the available liquidity.
	- If Market Orders remain UNFILLED or PARTIALLY FILLED due to insufficient liquidity, they exit with the achieved status.
2. **Queue Mode (allow_market_queue=True):**
	- UNFILLED / PARTIALLY UNFILLED Market Orders don't exit from the exchange.
	- They get queued into a "priority" queue and will be filled at the next available opportunity, i.e., with the next Limit order that arrives on the opposite side.

### Usage Example - Default Mode

```python

secEx = SecuritiesExchange()

orders = [
    Order("MSFT", OrderType.MARKET, MarketSide.BUY, 10),
    Order("MSFT", OrderType.LIMIT, MarketSide.SELL, 10, 411.10),
    # ... other orders
]

for order in orders:
    secEx.submit_order(order)
```

### Usage Example - Market Queue Mode

```python
secEx_withMarketQueue = SecuritiesExchange(allow_market_queue=True)

orders = [
    Order("MSFT", OrderType.MARKET, MarketSide.BUY, 10),
    Order("MSFT", OrderType.LIMIT, MarketSide.SELL, 10, 411.10),
    # ... other orders
]

for order in orders:
    secEx_withMarketQueue.submit_order(order)
```
