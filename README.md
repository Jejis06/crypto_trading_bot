# Crypto Trading Bot with GUI

A Python-based cryptocurrency trading bot with a modern PyQt5 GUI interface, supporting both individual trading strategies and portfolio management. The bot operates on Binance's testnet for safe testing and development.

## Features

- **Modern GUI Interface**
  - Real-time portfolio visualization with charts
  - Live price updates and trade monitoring
  - Portfolio composition view
  - Trade history logging
  - Interactive controls for bot management

- **Portfolio Management**
  - Manages a diversified portfolio of up to 10 cryptocurrencies
  - Automatic position management with profit targets and stop losses
  - Real-time portfolio value tracking
  - Individual position monitoring
  - Profit/Loss visualization

- **Trading Features**
  - Configurable trading strategies via JSON
  - Support for multiple trading pairs
  - Real-time price monitoring
  - Automatic trade execution
  - Risk management with stop-loss
  - Position sizing and quantity calculations

## Prerequisites

- Python 3.8 or higher
- Binance API credentials (Testnet)
- macOS, Linux, or Windows

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/crypto_trading_bot.git
cd crypto_trading_bot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a Binance testnet account and get API credentials from [Binance Testnet](https://testnet.binance.vision/)

2. Configure your trading strategies in `config/bots/` directory:
   - Use `portfolio_bot.json` for portfolio management settings (manages multiple cryptocurrencies)
   - Use `simple_bot.json` for single-pair trading (included example for BTC/USDT)
   - Add custom strategy configurations as needed

### Bot Configuration Types

#### Simple Bot Configuration
For single-pair trading, use this format:
```json
{
    "name": "Simple Trading Bot",
    "symbol": "BTCUSDT",        // Trading pair
    "strategy": "simple",       // Strategy type
    "investment_amount": 100,   // Amount to invest per trade
    "profit_target": 1.02,     // 2% profit target
    "stop_loss": 0.98,         // 2% stop loss
    "description": "Simple trading bot that trades BTC/USDT pair"
}
```

#### Portfolio Bot Configuration
For managing multiple cryptocurrencies:
```json
{
    "name": "Diversified Portfolio Bot",
    "strategy": "portfolio",
    "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", ...],
    "investment_per_coin": 100,
    "profit_target": 1.05,
    "stop_loss": 0.95,
    "max_holdings": 10,
    "description": "Diversified portfolio bot that manages multiple cryptocurrencies"
}
```

## Usage

1. Start the bot:
```bash
python src/gui.py
```

2. In the GUI:
   - Enter your Binance API credentials
   - Click "Connect" to establish connection
   - Use the control buttons to start/stop trading
   - Monitor your portfolio and trades in real-time

## Project Structure

```
crypto_trading_bot/
├── src/
│   ├── gui.py              # Main GUI implementation
│   ├── portfolio_bot.py    # Portfolio management logic
│   └── bot_manager.py      # Bot management and coordination
├── config/
│   └── bots/
│       └── portfolio_bot.json  # Portfolio configuration
├── requirements.txt        # Project dependencies
├── README.md              # Project documentation
└── .gitignore            # Git ignore rules
```

## Trading Strategy

The default portfolio strategy:
- Monitors 10 popular cryptocurrencies
- Buys when price is below 24-hour average
- Takes profit at 5% gain
- Implements stop-loss at 2% loss
- Manages position sizes automatically
- Maintains diversified portfolio

## Security Notes

- Never share your API credentials
- Use testnet for development and testing
- Review all trading parameters before live trading
- Monitor bot activity regularly

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This bot is for educational purposes only. Cryptocurrency trading carries significant risks. Use this software at your own risk. The authors are not responsible for any financial losses incurred through the use of this software. 