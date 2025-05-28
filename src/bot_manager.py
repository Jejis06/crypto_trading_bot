import logging
from binance.client import Client
from binance.exceptions import BinanceAPIException
from trading_bot import TradingBot

logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self, api_key, api_secret):
        """Initialize the bot manager with Binance API credentials."""
        logger.info("Initializing BotManager...")
        try:
            self.client = Client(api_key, api_secret, testnet=True)
            logger.info("Created Binance client instance")
        except Exception as e:
            logger.error(f"Failed to create Binance client: {str(e)}")
            raise
            
        self.bots = []
        self.running = False
        
        # Verify connection to Binance
        try:
            logger.info("Testing connection to Binance testnet...")
            self.client.ping()
            
            # Additional verification
            server_time = self.client.get_server_time()
            logger.info(f"Successfully connected to Binance testnet. Server time: {server_time['serverTime']}")
            
            # Test market data access
            exchange_info = self.client.get_exchange_info()
            logger.info(f"Successfully retrieved exchange info with {len(exchange_info['symbols'])} symbols")
            
        except BinanceAPIException as e:
            logger.error(f"Failed to connect to Binance: {str(e)}")
            logger.error(f"Error code: {e.code}, message: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during connection verification: {str(e)}")
            raise

    def add_bot(self, config):
        """Add a new trading bot with the specified configuration."""
        try:
            bot = TradingBot(self.client, config)
            self.bots.append(bot)
            logger.info(f"Added new bot for {config.get('symbol', 'Unknown')}")
        except Exception as e:
            logger.error(f"Failed to add bot: {str(e)}")

    def start(self):
        """Start all trading bots."""
        self.running = True
        logger.info("Starting all trading bots...")
        
        for bot in self.bots:
            bot.start()

    def stop(self):
        """Stop all trading bots."""
        self.running = False
        logger.info("Stopping all trading bots...")
        
        for bot in self.bots:
            bot.stop()

    def get_account_info(self):
        """Get account information from Binance."""
        try:
            return self.client.get_account()
        except BinanceAPIException as e:
            logger.error(f"Failed to get account info: {str(e)}")
            return None 