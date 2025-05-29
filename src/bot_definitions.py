from simple_bot import SimpleBot
from typing import List
from binance.client import Client

def get_available_bots(client: Client) -> List[SimpleBot]:
    """
    Define and return all available trading bots.
    This replaces the JSON configuration with direct Python definitions.
    """
    bots = [
        # Major cryptocurrencies
        SimpleBot(client, "BTCUSDT", investment_amount=100.0),
        SimpleBot(client, "ETHUSDT", investment_amount=100.0),
        SimpleBot(client, "BNBUSDT", investment_amount=100.0),
        
        # Popular altcoins
        SimpleBot(client, "ADAUSDT", investment_amount=50.0),
        SimpleBot(client, "DOTUSDT", investment_amount=50.0),
        SimpleBot(client, "SOLUSDT", investment_amount=50.0),
        
        # DeFi tokens
        SimpleBot(client, "UNIUSDT", investment_amount=30.0),
        SimpleBot(client, "AAVEUSDT", investment_amount=30.0),
        SimpleBot(client, "LINKUSDT", investment_amount=30.0),
        
        # Meme coins (smaller investment due to higher risk)
        SimpleBot(client, "DOGEUSDT", investment_amount=20.0),
        SimpleBot(client, "SHIBUSDT", investment_amount=20.0)
    ]
    
    # Filter out any bots whose symbols aren't available
    valid_bots = []
    for bot in bots:
        try:
            # Verify the symbol exists
            client.get_symbol_info(bot.symbol)
            valid_bots.append(bot)
        except Exception as e:
            print(f"Skipping {bot.symbol} - not available: {str(e)}")
    
    return valid_bots 