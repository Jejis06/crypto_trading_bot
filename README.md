# Crypto Trading Bot

A Python-based cryptocurrency trading bot with a modern GUI interface that automates trading on Binance using customizable strategies.

## Features

- **Modern PyQt5-based GUI Interface**
  - Real-time price updates
  - Position tracking
  - Profit/Loss monitoring
  - Trading history visualization
  - Multi-bot management interface

- **Action-Based Trading System**
  - Simple, robust trading decisions ("buy", "sell", "waiting")
  - Built-in position tracking
  - Automatic quantity calculation
  - Risk management features

- **Pre-configured Trading Pairs**
  - Major cryptocurrencies (BTC, ETH, BNB)
  - Popular altcoins (ADA, DOT, SOL)
  - DeFi tokens (UNI, AAVE, LINK)
  - Meme coins (DOGE, SHIB)

- **Risk Management**
  - Tiered investment amounts based on cryptocurrency category
  - Built-in stop-loss and take-profit mechanisms
  - Position size management
  - Real-time profit/loss tracking

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto_trading_bot.git
cd crypto_trading_bot
```

2. Create and activate a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. **Binance API Setup**
   - Create a Binance account if you don't have one
   - Create API keys from your Binance account
   - Enable testnet for testing (recommended)

2. **Bot Configuration**
   - Trading pairs and investment amounts are defined in `src/bot_definitions.py`
   - Each bot category has pre-set investment amounts:
     * Major cryptocurrencies: $100 per trade
     * Popular altcoins: $50 per trade
     * DeFi tokens: $30 per trade
     * Meme coins: $20 per trade

## Usage

1. Start the GUI:
```bash
python src/gui.py
```

2. Enter your Binance API credentials in the GUI
3. The system will automatically:
   - Connect to Binance
   - Load and validate available trading pairs
   - Initialize the trading bots
   - Start monitoring the market

4. Use the GUI to:
   - Monitor bot status and positions
   - View real-time prices and P/L
   - Start/stop trading
   - View trading history

## Trading Strategy

The default SimpleBot implements a moving average crossover strategy:

- **Entry Conditions**:
  - Short-term MA (6-hour) crosses above long-term MA (24-hour)
  - Current price is below the long-term MA

- **Exit Conditions**:
  - 2% profit target reached
  - 2% stop loss triggered
  - Short-term MA crosses below long-term MA

## Project Structure

```
crypto_trading_bot/
├── src/
│   ├── gui.py              # Main GUI application
│   ├── base_bot.py         # Abstract base class for bots
│   ├── simple_bot.py       # Implementation of trading strategy
│   ├── bot_manager.py      # Manages multiple bots
│   ├── bot_loader.py       # Loads bot configurations
│   ├── bot_definitions.py  # Defines available trading bots
│   └── credentials_manager.py  # Handles API credentials
├── requirements.txt
└── README.md
```

## Dependencies

- Python 3.8+
- PyQt5
- python-binance
- numpy
- pyqtgraph
- pandas

## Security Notes

- Never share your API keys
- Use testnet for testing
- Start with small investment amounts
- Monitor your positions regularly
- The bot uses market orders by default

## Disclaimer

This software is for educational purposes only. Use at your own risk. The authors are not responsible for any financial losses incurred using this software. Cryptocurrency trading is highly risky and can result in significant losses.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - See LICENSE file for details 