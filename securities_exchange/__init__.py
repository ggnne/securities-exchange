"""Top-level package for securities-exchange."""

__author__ = """Giulio Guerri"""
__email__ = "giulio.guerri93@gmail.com"
__version__ = "0.0.5"

import logging

# Set up a global logger for the package
logging.basicConfig(level=logging.WARNING, format="[%(levelname)s][%(asctime)s]: %(message)s")
logger = logging.getLogger(__name__)


def set_logging_level(level):
    """
    Set the logging level for the entire package.

    Args:
        level (int): The logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING, etc.).
    """
    logging.getLogger(__name__).setLevel(level)


from .securities_exchange import SecuritiesExchange
from .enums import OrderType, OrderStatus, MarketSide
from .order import Order
from .orderbook import OrderBook
from .bookside import BookSide

