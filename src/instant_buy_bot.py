import logging
from datetime import datetime
from binance.exceptions import BinanceAPIException
from decimal import Decimal, ROUND_DOWN
from symbol_manager import SymbolManager

logger = logging.getLogger(__name__)

class InstantBuyBot:
    def __init__(self, client, config):
        """Initialize instant buy bot with Binance client and configuration."""
        self.client = client
        self.config = config
        self.symbol = config['symbol']
        self.investment_amount = config['investment_amount']
        self.profit_target = config.get('profit_target', 1.02)
        self.stop_loss = config.get('stop_loss', 0.98)
        self.symbol_manager = SymbolManager(client)
        self.position = None
        self.trade_history = []
        
    def execute_buy(self):
        """Execute an immediate market buy order."""
        try:
            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            current_price = float(ticker['price'])
            
            # Calculate quantity based on investment amount
            quantity = self.symbol_manager.calculate_quantity(self.symbol, self.investment_amount)
            
            if not quantity:
                logger.error(f"Failed to calculate valid quantity for {self.symbol}")
                return False
            
            # Place market buy order
            order = self.client.create_test_order(
                symbol=self.symbol,
                side='BUY',
                type='MARKET',
                quantity=quantity
            )
            
            # Record the position
            self.position = {
                'symbol': self.symbol,
                'quantity': quantity,
                'price': current_price,
                'time': datetime.now()
            }
            
            # Record in trade history
            self.trade_history.append({
                'type': 'BUY',
                'symbol': self.symbol,
                'price': current_price,
                'quantity': quantity,
                'time': datetime.now()
            })
            
            logger.info(f"Successfully placed instant buy order for {self.symbol}: {quantity} @ {current_price}")
            return True
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error during instant buy: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error during instant buy: {str(e)}")
            return False
    
    def check_position(self):
        """Check current position and execute sell if conditions are met."""
        if not self.position:
            return
        
        try:
            current_price = float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])
            buy_price = self.position['price']
            
            # Check for profit target or stop loss
            if current_price >= buy_price * self.profit_target:
                self._execute_sell("Take profit")
            elif current_price <= buy_price * self.stop_loss:
                self._execute_sell("Stop loss")
                
        except Exception as e:
            logger.error(f"Error checking position: {str(e)}")
    
    def _execute_sell(self, reason):
        """Execute a sell order for the current position."""
        try:
            order = self.client.create_test_order(
                symbol=self.symbol,
                side='SELL',
                type='MARKET',
                quantity=self.position['quantity']
            )
            
            current_price = float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])
            
            # Record in trade history
            self.trade_history.append({
                'type': 'SELL',
                'symbol': self.symbol,
                'price': current_price,
                'quantity': self.position['quantity'],
                'time': datetime.now(),
                'reason': reason
            })
            
            logger.info(f"Sold position for {self.symbol} ({reason})")
            self.position = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error selling position: {str(e)}")
            return False
    
    def get_position_value(self):
        """Get current position value and profit/loss."""
        if not self.position:
            return {
                'symbol': self.symbol,
                'position': None,
                'current_value': 0,
                'profit_loss': 0
            }
        
        try:
            current_price = float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])
            current_value = self.position['quantity'] * current_price
            profit_loss = current_value - (self.position['quantity'] * self.position['price'])
            
            return {
                'symbol': self.symbol,
                'position': self.position,
                'current_value': current_value,
                'profit_loss': profit_loss
            }
            
        except Exception as e:
            logger.error(f"Error calculating position value: {str(e)}")
            return None
    
    def get_trade_history(self):
        """Get the complete trade history."""
        return self.trade_history 