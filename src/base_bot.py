from abc import ABC, abstractmethod
from typing import Tuple, Optional
from binance.client import Client
import logging

logger = logging.getLogger(__name__)

class BaseBot(ABC):
    def __init__(self, client: Client, symbol: str):
        """Initialize the base bot with a Binance client and trading symbol."""
        self.client = client
        self.symbol = symbol
        self.current_position = None

    @abstractmethod
    def analyze(self) -> Tuple[str, Optional[float]]:
        """
        Analyze the market and return a trading action.
        
        Returns:
            Tuple[str, Optional[float]]: A tuple containing:
                - Action string: One of "waiting", "buy", "sell"
                - Optional quantity to buy/sell (None for "waiting")
        """
        pass

    def get_current_price(self) -> float:
        """Get the current price of the symbol."""
        try:
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            return float(ticker['price'])
        except Exception as e:
            logger.error(f"Error getting price for {self.symbol}: {str(e)}")
            return 0.0

    def get_recent_trades(self, limit: int = 1000) -> list:
        """Get recent trades for analysis."""
        try:
            return self.client.get_historical_trades(symbol=self.symbol, limit=limit)
        except Exception as e:
            logger.error(f"Error getting trades for {self.symbol}: {str(e)}")
            return []

    def get_klines(self, interval: str = '1h', limit: int = 100) -> list:
        """Get klines/candlestick data for analysis."""
        try:
            return self.client.get_klines(symbol=self.symbol, interval=interval, limit=limit)
        except Exception as e:
            logger.error(f"Error getting klines for {self.symbol}: {str(e)}")
            return [] 