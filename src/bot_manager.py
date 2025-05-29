import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
from typing import List, Dict
from datetime import datetime
from threading import Thread, Lock
import time

logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """Initialize bot manager with API credentials."""
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.bots = []
        self.running = False
        self.update_thread = None
        self.lock = Lock()
        
        # Test connection
        try:
            self.client.get_account()
            logger.info("Successfully connected to Binance API")
        except BinanceAPIException as e:
            logger.error(f"Failed to connect to Binance API: {str(e)}")
            raise

    def add_bot(self, bot) -> bool:
        """Add a trading bot to the manager."""
        try:
            if not hasattr(bot, 'symbol') or not hasattr(bot, 'analyze'):
                raise ValueError("Invalid bot object - missing required attributes")
            
            # Check for duplicate symbols
            if any(b.symbol == bot.symbol for b in self.bots):
                logger.warning(f"Bot for {bot.symbol} already exists, skipping")
                return False
            
            self.bots.append(bot)
            logger.info(f"Added bot for {bot.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add bot: {str(e)}")
            return False

    def start(self):
        """Start the bot manager."""
        if not self.running:
            logger.info("Starting bot manager...")
            self.running = True
            self.update_thread = Thread(target=self._run, daemon=True)
            self.update_thread.start()

    def stop(self):
        """Stop the bot manager."""
        if self.running:
            logger.info("Stopping bot manager...")
            self.running = False
            if self.update_thread:
                self.update_thread.join()

    def _run(self):
        """Main bot manager loop."""
        while self.running:
            try:
                with self.lock:
                    for bot in self.bots:
                        try:
                            # Get bot's analysis
                            action, quantity = bot.analyze()
                            
                            # Execute action if needed
                            if action == "buy":
                                self._execute_buy(bot, quantity)
                            elif action == "sell":
                                self._execute_sell(bot, quantity)
                            
                        except Exception as e:
                            logger.error(f"Error processing bot {bot.symbol}: {str(e)}")
                
                # Sleep for 1 minute before next update
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in bot manager loop: {str(e)}")
                time.sleep(60)

    def _execute_buy(self, bot, quantity: float):
        """Execute a buy order for a bot."""
        try:
            # Place market buy order
            order = self.client.create_test_order(
                symbol=bot.symbol,
                side='BUY',
                type='MARKET',
                quantity=quantity
            )
            
            # Update bot's position
            current_price = float(self.client.get_symbol_ticker(symbol=bot.symbol)['price'])
            bot.current_position = {
                'quantity': quantity,
                'price': current_price,
                'time': datetime.now()
            }
            
            logger.info(f"Executed buy order for {bot.symbol}: {quantity} @ {current_price}")
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error during buy: {str(e)}")
        except Exception as e:
            logger.error(f"Error executing buy order: {str(e)}")

    def _execute_sell(self, bot, quantity: float):
        """Execute a sell order for a bot."""
        try:
            # Place market sell order
            order = self.client.create_test_order(
                symbol=bot.symbol,
                side='SELL',
                type='MARKET',
                quantity=quantity
            )
            
            # Clear bot's position
            current_price = float(self.client.get_symbol_ticker(symbol=bot.symbol)['price'])
            if bot.current_position:
                entry_price = bot.current_position['price']
                pl_percent = ((current_price - entry_price) / entry_price) * 100
                logger.info(f"Closed position for {bot.symbol} with P/L: {pl_percent:.2f}%")
            
            bot.current_position = None
            
            logger.info(f"Executed sell order for {bot.symbol}: {quantity} @ {current_price}")
            
        except BinanceAPIException as e:
            logger.error(f"Binance API error during sell: {str(e)}")
        except Exception as e:
            logger.error(f"Error executing sell order: {str(e)}")

    def get_bot_statuses(self) -> List[Dict]:
        """Get current status of all bots."""
        statuses = []
        with self.lock:
            for bot in self.bots:
                try:
                    current_price = bot.get_current_price()
                    status = {
                        'symbol': bot.symbol,
                        'current_price': current_price,
                        'position': None,
                        'is_running': self.running
                    }
                    
                    if bot.current_position:
                        pos = bot.current_position
                        entry_price = pos['price']
                        quantity = pos['quantity']
                        current_value = quantity * current_price
                        entry_value = quantity * entry_price
                        unrealized_pl = current_value - entry_value
                        
                        status['position'] = {
                            'quantity': quantity,
                            'entry_price': entry_price,
                            'current_value': current_value,
                            'unrealized_pl': unrealized_pl,
                            'unrealized_pl_percent': (unrealized_pl / entry_value) * 100,
                            'time': pos['time']
                        }
                    
                    statuses.append(status)
                    
                except Exception as e:
                    logger.error(f"Error getting status for {bot.symbol}: {str(e)}")
                    
        return statuses

    def get_all_positions(self):
        """Get current positions for all bots."""
        positions = {}
        for bot in self.bots:
            try:
                status = bot.get_status()
                if status and status.get('position'):
                    positions[bot.symbol] = status['position']
            except Exception as e:
                logger.error(f"Failed to get position for {bot.symbol}: {str(e)}")
        return positions

    def get_account_info(self):
        """Get account information from Binance."""
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            logger.error(f"Failed to get account info: {str(e)}")
            return None 