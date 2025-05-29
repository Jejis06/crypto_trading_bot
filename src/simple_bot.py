from base_bot import BaseBot
from typing import Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SimpleBot(BaseBot):
    def __init__(self, client, symbol: str, investment_amount: float = 100.0):
        """Initialize simple bot with moving average strategy."""
        super().__init__(client, symbol)
        self.investment_amount = investment_amount
        self.profit_target = 1.02  # 2% profit target
        self.stop_loss = 0.98  # 2% stop loss

    def analyze(self) -> Tuple[str, Optional[float]]:
        """
        Analyze market data and return trading action.
        Uses a simple moving average crossover strategy.
        """
        try:
            # Get current price and klines data
            current_price = self.get_current_price()
            if current_price == 0:
                return "waiting", None

            klines = self.get_klines(interval='1h', limit=24)
            if not klines:
                return "waiting", None

            # Calculate moving averages
            prices = [float(k[4]) for k in klines]  # Use closing prices
            ma_short = np.mean(prices[-6:])  # 6-hour MA
            ma_long = np.mean(prices)  # 24-hour MA

            # Calculate quantity based on investment amount
            quantity = self.investment_amount / current_price
            
            # Round quantity to appropriate decimal places
            info = self.client.get_symbol_info(self.symbol)
            if info and 'stepSize' in info['filters'][2]:
                step_size = float(info['filters'][2]['stepSize'])
                precision = len(str(step_size).split('.')[-1].rstrip('0'))
                quantity = round(quantity, precision)

            # If we have a position, check for exit conditions
            if self.current_position:
                entry_price = self.current_position['price']
                
                # Check profit target
                if current_price >= entry_price * self.profit_target:
                    return "sell", self.current_position['quantity']
                
                # Check stop loss
                if current_price <= entry_price * self.stop_loss:
                    return "sell", self.current_position['quantity']
                
                # Check MA crossover (sell signal)
                if ma_short < ma_long:
                    return "sell", self.current_position['quantity']
                
                return "waiting", None

            # If we don't have a position, check for entry conditions
            else:
                # Buy signal: short MA crosses above long MA
                if ma_short > ma_long and current_price < ma_long:
                    return "buy", quantity

            return "waiting", None

        except Exception as e:
            logger.error(f"Error in SimpleBot analysis: {str(e)}")
            return "waiting", None 