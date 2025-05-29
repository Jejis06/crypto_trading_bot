import logging
import time
import threading
from datetime import datetime
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

class TradingBot:
    def __init__(self, client, config):
        """Initialize trading bot with Binance client and configuration."""
        self.client = client
        self.config = config
        self.symbol = config['symbol']
        self.strategy = config.get('strategy', 'simple')
        self.running = False
        self.thread = None
        
        # Trading parameters
        self.investment_amount = config.get('investment_amount', 100.0)
        self.profit_target = config.get('profit_target', 1.02)
        self.stop_loss = config.get('stop_loss', 0.98)
        self.trailing_stop = config.get('trailing_stop', 0.005)
        self.min_volume_24h = config.get('min_volume_24h', 10000)
        self.min_spread = config.get('min_spread', 0.001)
        
        # State tracking
        self.current_position = None
        self.trade_history = []
        
        # Validate symbol
        try:
            self.client.get_symbol_info(self.symbol)
        except BinanceAPIException as e:
            logger.error(f"Invalid symbol {self.symbol}: {str(e)}")
            raise

    def __getitem__(self, key):
        """Make the bot subscriptable to access config items."""
        if hasattr(self, key):
            return getattr(self, key)
        return self.config.get(key)
        
    def __contains__(self, key):
        """Support 'in' operator for config checking."""
        return hasattr(self, key) or key in self.config

    def start(self):
        """Start the trading bot in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.start()
            logger.info(f"Started trading bot for {self.symbol}")

    def stop(self):
        """Stop the trading bot."""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info(f"Stopped trading bot for {self.symbol}")

    def _run(self):
        """Main trading loop."""
        while self.running:
            try:
                if self.strategy == 'simple':
                    self._simple_strategy()
                else:
                    logger.warning(f"Unknown strategy: {self.strategy}")
                
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in trading loop: {str(e)}")
                time.sleep(60)  # Wait before retrying

    def _simple_strategy(self):
        """Implement a simple trading strategy."""
        try:
            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            current_price = float(ticker['price'])
            
            # Get recent trades
            trades = self.client.get_my_trades(symbol=self.symbol, limit=1)
            
            if trades:
                last_trade = trades[0]
                last_price = float(last_trade['price'])
                
                if last_trade['isBuyer']:
                    # We have a buy position, check for sell conditions
                    if current_price >= last_price * self.profit_target:
                        self._place_sell_order("Take profit")
                    elif current_price <= last_price * self.stop_loss:
                        self._place_sell_order("Stop loss")
            else:
                # No recent trades, look for buying opportunity
                klines = self.client.get_klines(symbol=self.symbol, interval='1h', limit=24)
                if self._should_buy(klines):
                    self._place_buy_order()
                    
        except BinanceAPIException as e:
            logger.error(f"Binance API error: {str(e)}")

    def _should_buy(self, klines):
        """Analyze if we should buy based on klines data."""
        # Simple strategy: buy if price is lower than 24h average
        total = 0
        for kline in klines:
            total += float(kline[4])  # Closing price
        average = total / len(klines)
        
        current_price = float(klines[-1][4])
        return current_price < average

    def _place_buy_order(self):
        """Place a buy order."""
        try:
            # Calculate quantity based on investment amount
            quantity = self.symbol_manager.calculate_quantity(self.symbol, self.investment_amount)
            if not quantity:
                logger.error(f"Failed to calculate valid quantity for {self.symbol}")
                return
                
            order = self.client.create_test_order(
                symbol=self.symbol,
                side='BUY',
                type='MARKET',
                quantity=quantity
            )
            
            current_price = float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])
            order_value = quantity * current_price
            
            logger.info(f"Placed buy order for {self.symbol}: {quantity} @ {current_price:.8f} (Value: ${order_value:.2f})")
            
            # Record the position
            self.current_position = {
                'symbol': self.symbol,
                'quantity': quantity,
                'entry_price': current_price,
                'time': datetime.now(),
                'value': order_value
            }
            
            # Add to trade history
            self.trade_history.append({
                'type': 'BUY',
                'symbol': self.symbol,
                'quantity': quantity,
                'price': current_price,
                'value': order_value,
                'time': datetime.now()
            })
            
            return True
            
        except BinanceAPIException as e:
            logger.error(f"Failed to place buy order for {self.symbol}: {str(e)}")
            return False

    def _place_sell_order(self, reason):
        """Place a sell order."""
        if not self.current_position:
            logger.warning(f"No position to sell for {self.symbol}")
            return False
            
        try:
            quantity = self.current_position['quantity']
            order = self.client.create_test_order(
                symbol=self.symbol,
                side='SELL',
                type='MARKET',
                quantity=quantity
            )
            
            current_price = float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])
            order_value = quantity * current_price
            profit_loss = order_value - self.current_position['value']
            
            logger.info(f"Placed sell order for {self.symbol}: {quantity} @ {current_price:.8f} " +
                       f"(Value: ${order_value:.2f}, P/L: ${profit_loss:.2f}) - {reason}")
            
            # Add to trade history
            self.trade_history.append({
                'type': 'SELL',
                'symbol': self.symbol,
                'quantity': quantity,
                'price': current_price,
                'value': order_value,
                'profit_loss': profit_loss,
                'reason': reason,
                'time': datetime.now()
            })
            
            self.current_position = None
            return True
            
        except BinanceAPIException as e:
            logger.error(f"Failed to place sell order for {self.symbol}: {str(e)}")
            return False

    def get_status(self):
        """Get current bot status and position information."""
        try:
            current_price = float(self.client.get_symbol_ticker(symbol=self.symbol)['price'])
            
            status = {
                'symbol': self.symbol,
                'strategy': self.strategy,
                'current_price': current_price,
                'investment_amount': self.investment_amount,
                'is_running': self.running,
                'position': None,
                'unrealized_pl': 0.0
            }
            
            if self.current_position:
                position_value = self.current_position['quantity'] * current_price
                unrealized_pl = position_value - self.current_position['value']
                
                status['position'] = {
                    'quantity': self.current_position['quantity'],
                    'entry_price': self.current_position['entry_price'],
                    'current_value': position_value,
                    'unrealized_pl': unrealized_pl,
                    'unrealized_pl_percent': (unrealized_pl / self.current_position['value']) * 100,
                    'time': self.current_position['time']
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting status for {self.symbol}: {str(e)}")
            return None 