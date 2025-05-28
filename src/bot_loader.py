import os
import json
import logging
from typing import Dict, List, Tuple, Optional
from trading_bot import TradingBot
from portfolio_bot import PortfolioBot
from instant_buy_bot import InstantBuyBot
from bot_validator import BotValidator
from symbol_manager import SymbolManager

logger = logging.getLogger(__name__)

class BotLoader:
    def __init__(self, client):
        logger.info("Initializing BotLoader...")
        self.client = client
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bots')
        logger.info(f"Bot configuration directory: {self.config_dir}")
        
        self.symbol_manager = SymbolManager(client)
        self.validator = BotValidator()
        
        if not os.path.exists(self.config_dir):
            logger.warning(f"Config directory does not exist, creating: {self.config_dir}")
            os.makedirs(self.config_dir)
    
    def load_all_bots(self):
        """Load all bot configurations and create bot instances."""
        trading_bots = []
        portfolio_bot = None
        
        logger.info("Starting to load bot configurations...")
        try:
            config_files = [f for f in os.listdir(self.config_dir) if f.endswith('.json')]
            logger.info(f"Found {len(config_files)} configuration files: {', '.join(config_files)}")
            
            if not config_files:
                logger.warning("No bot configuration files found in directory")
                return [], None
            
            for filename in config_files:
                logger.info(f"Processing configuration file: {filename}")
                try:
                    file_path = os.path.join(self.config_dir, filename)
                    if not os.path.exists(file_path):
                        logger.error(f"Configuration file does not exist: {file_path}")
                        continue
                        
                    with open(file_path, 'r') as f:
                        try:
                            config = json.load(f)
                        except json.JSONDecodeError as je:
                            logger.error(f"Invalid JSON in configuration file {filename}: {str(je)}")
                            continue
                            
                    logger.info(f"Loaded configuration from {filename}: {config.get('name', 'Unnamed')} - Strategy: {config.get('strategy', 'unknown')}")
                    
                    # Validate configuration using BotValidator
                    try:
                        is_valid, errors = BotValidator.validate_bot_config(config, self.symbol_manager)
                        if not is_valid:
                            logger.error(f"Configuration validation failed for {filename}: {', '.join(errors)}")
                            continue
                        logger.info(f"Configuration validation successful for {filename}")
                    except Exception as e:
                        logger.error(f"Error during configuration validation for {filename}: {str(e)}", exc_info=True)
                        continue
                    
                    if filename == 'portfolio_bot.json':
                        try:
                            portfolio_bot = PortfolioBot(self.client, config)
                            logger.info("Successfully created portfolio bot instance")
                        except Exception as e:
                            logger.error(f"Failed to create portfolio bot: {str(e)}", exc_info=True)
                            portfolio_bot = None
                    elif 'symbol' in config:
                        try:
                            bot = self._create_bot_instance(config)
                            if bot:
                                trading_bots.append(bot)
                                logger.info(f"Successfully loaded trading bot for {config['symbol']}")
                            else:
                                logger.error(f"Failed to create bot instance for {config['symbol']}")
                        except Exception as e:
                            logger.error(f"Error creating bot instance for {config['symbol']}: {str(e)}", exc_info=True)
                except Exception as e:
                    logger.error(f"Unexpected error processing {filename}: {str(e)}", exc_info=True)
            
            if not trading_bots and not portfolio_bot:
                raise ValueError("No valid bot configurations were loaded")
                
            logger.info(f"Completed loading bots. Created {len(trading_bots)} trading bots and {'a' if portfolio_bot else 'no'} portfolio bot")
            return trading_bots, portfolio_bot
            
        except Exception as e:
            logger.error(f"Critical error in load_all_bots: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to load bots: {str(e)}")
    
    def _create_bot_instance(self, config: Dict) -> Optional[TradingBot]:
        """Create appropriate bot instance based on configuration."""
        try:
            strategy = config['strategy']
            logger.info(f"Creating bot instance for strategy: {strategy}")
            
            # Validate symbol if required
            if strategy != 'portfolio' and 'symbol' in config:
                symbol = config['symbol']
                logger.info(f"Validating symbol: {symbol}")
                if not self.symbol_manager.validate_symbol(symbol):
                    logger.error(f"Invalid symbol {symbol} for {strategy} bot")
                    return None
                logger.info(f"Symbol {symbol} validation successful")
            
            # Create bot instance
            if strategy == 'instant_buy':
                logger.info(f"Creating InstantBuyBot for {config['symbol']}")
                return InstantBuyBot(self.client, config)
            elif strategy in ['simple', 'grid', 'dca']:
                logger.info(f"Creating TradingBot for {config['symbol']}")
                return TradingBot(self.client, config)
            else:
                logger.error(f"Unknown strategy type: {strategy}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating bot instance: {str(e)}", exc_info=True)
            return None 