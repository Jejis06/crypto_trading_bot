import os
import json
import logging
from dotenv import load_dotenv
from bot_manager import BotManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_bot_configs():
    """Load all bot configurations from the config/bots directory."""
    configs = []
    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'bots')
    
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        logger.info(f"Created config directory at {config_dir}")
        return configs

    for filename in os.listdir(config_dir):
        if filename.endswith('.json'):
            with open(os.path.join(config_dir, filename), 'r') as f:
                try:
                    config = json.load(f)
                    configs.append(config)
                    logger.info(f"Loaded bot configuration from {filename}")
                except json.JSONDecodeError:
                    logger.error(f"Error parsing {filename}. Skipping...")
    
    return configs

def main():
    # Load environment variables
    load_dotenv()
    
    # Verify API credentials
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("API credentials not found. Please set BINANCE_API_KEY and BINANCE_API_SECRET in .env file")
        return

    # Load bot configurations
    bot_configs = load_bot_configs()
    
    if not bot_configs:
        logger.warning("No bot configurations found. Please add configuration files in config/bots/")
        return

    # Initialize and start bot manager
    bot_manager = BotManager(api_key, api_secret)
    
    try:
        for config in bot_configs:
            bot_manager.add_bot(config)
        
        bot_manager.start()
    except KeyboardInterrupt:
        logger.info("Shutting down bots...")
        bot_manager.stop()
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        bot_manager.stop()

if __name__ == "__main__":
    main() 