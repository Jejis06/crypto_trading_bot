import logging
from datetime import datetime, timedelta
from binance.exceptions import BinanceAPIException
from decimal import Decimal, ROUND_DOWN
from symbol_manager import SymbolManager
import json

logger = logging.getLogger(__name__)

class PortfolioBot:
    def __init__(self, client, total_funds=15000.0):
        self.client = client
        self.total_funds = total_funds
        self.allocated_funds = {}  # symbol -> amount
        self.portfolio_history = []  # List of (timestamp, total_value) tuples
        self.last_rebalance = datetime.now()
        
    def allocate_funds(self, bots):
        """Allocate funds across trading bots."""
        active_bots = [bot for bot in bots if bot.running]
        if not active_bots:
            return
            
        # Equal allocation strategy
        per_bot_allocation = self.total_funds / len(active_bots)
        logger.info(f"Allocating ${per_bot_allocation:.2f} to each of {len(active_bots)} bots")
        
        for bot in active_bots:
            self.allocated_funds[bot.symbol] = per_bot_allocation
            bot.investment_amount = per_bot_allocation
            
    def get_portfolio_value(self):
        """Calculate current portfolio value."""
        try:
            total_value = 0
            holdings = []
            
            # Get account information
            account = self.client.get_account()
            
            # Calculate total value of holdings
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    # Get asset price in USDT
                    if asset == 'USDT':
                        price = 1.0
                    else:
                        try:
                            ticker = self.client.get_symbol_ticker(symbol=f"{asset}USDT")
                            price = float(ticker['price'])
                        except:
                            logger.warning(f"Could not get price for {asset}, skipping")
                            continue
                    
                    value = total * price
                    total_value += value
                    
                    holdings.append({
                        'asset': asset,
                        'quantity': total,
                        'value': value
                    })
            
            # Add USDT balance
            usdt_balance = float(next(b['free'] for b in account['balances'] if b['asset'] == 'USDT'))
            total_value += usdt_balance
            
            # Calculate 24h change
            yesterday_value = self._get_value_24h_ago()
            if yesterday_value:
                daily_pl = total_value - yesterday_value
                daily_pl_percent = (daily_pl / yesterday_value) * 100
            else:
                daily_pl = 0
                daily_pl_percent = 0
            
            # Store current value in history
            self.portfolio_history.append((datetime.now(), total_value))
            
            # Keep only last 7 days of history
            week_ago = datetime.now() - timedelta(days=7)
            self.portfolio_history = [(t, v) for t, v in self.portfolio_history if t > week_ago]
            
            return {
                'total_value': total_value,
                'holdings': holdings,
                'usdt_balance': usdt_balance,
                'daily_pl': daily_pl,
                'daily_pl_percent': daily_pl_percent
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio value: {str(e)}")
            return {
                'total_value': self.total_funds,
                'holdings': [],
                'usdt_balance': self.total_funds,
                'daily_pl': 0,
                'daily_pl_percent': 0
            }
            
    def _get_value_24h_ago(self):
        """Get portfolio value from 24 hours ago."""
        target_time = datetime.now() - timedelta(hours=24)
        
        # Find closest historical value
        if self.portfolio_history:
            closest = min(self.portfolio_history, 
                         key=lambda x: abs(x[0] - target_time))
            
            # Only use if within 2 hours of target
            if abs(closest[0] - target_time) <= timedelta(hours=2):
                return closest[1]
        
        return None
        
    def analyze_and_trade(self):
        """Analyze portfolio and execute trades if needed."""
        try:
            # Get current portfolio state
            portfolio = self.get_portfolio_value()
            
            # Check if rebalancing is needed (every 4 hours)
            if datetime.now() - self.last_rebalance > timedelta(hours=4):
                self._rebalance_portfolio(portfolio)
                self.last_rebalance = datetime.now()
                
        except Exception as e:
            logger.error(f"Error in portfolio analysis: {str(e)}")
            
    def _rebalance_portfolio(self, portfolio):
        """Rebalance portfolio to maintain target allocations."""
        try:
            # Calculate total value excluding USDT
            crypto_value = sum(h['value'] for h in portfolio['holdings'] if h['asset'] != 'USDT')
            
            # If crypto exposure is too high, reduce positions
            if crypto_value > self.total_funds * 0.8:  # 80% max crypto exposure
                logger.info("Crypto exposure too high, reducing positions")
                # Implement position reduction logic here
                
            # If crypto exposure is too low, look for opportunities
            elif crypto_value < self.total_funds * 0.2:  # 20% min crypto exposure
                logger.info("Crypto exposure too low, looking for opportunities")
                # Implement opportunity seeking logic here
                
        except Exception as e:
            logger.error(f"Error in portfolio rebalancing: {str(e)}")

    def refresh_symbols(self):
        """Refresh the list of trading symbols based on configuration."""
        selection = self.config.get('symbol_selection', {})
        method = selection.get('method', 'top_volume')
        
        if method == 'top_volume':
            symbols = self.symbol_manager.get_top_volume_symbols(
                quote_asset=self.quote_asset,
                limit=selection.get('limit', 20)
            )
            self.available_symbols = [s['symbol'] for s in symbols]
        else:
            # Fallback to all symbols for the quote asset
            symbols = self.symbol_manager.get_symbols_for_quote_asset(self.quote_asset)
            self.available_symbols = list(symbols.keys())[:self.max_symbols]
        
        # Initialize trade history for new symbols
        for symbol in self.available_symbols:
            if symbol not in self.trade_history:
                self.trade_history[symbol] = []
        
        logger.info(f"Updated available symbols: {', '.join(self.available_symbols)}")
    
    def calculate_quantity(self, symbol, current_price):
        """Calculate the quantity to buy based on investment amount and current price."""
        return self.symbol_manager.calculate_quantity(symbol, self.investment_per_coin)
    
    def _should_buy(self, symbol):
        """Determine if we should buy the symbol based on market conditions."""
        try:
            # Get recent price data
            klines = self.client.get_klines(symbol=symbol, interval='1h', limit=24)
            
            # Calculate 24h average price
            total = sum(float(k[4]) for k in klines)  # Using closing prices
            average = total / len(klines)
            
            # Get current price
            current_price = float(self.client.get_symbol_ticker(symbol=symbol)['price'])
            
            # Buy if price is below average (potential upward movement)
            return current_price < average
        
        except Exception as e:
            logger.error(f"Error in should_buy for {symbol}: {str(e)}")
            return False
    
    def _place_buy_order(self, symbol, quantity):
        """Place a buy order."""
        try:
            order = self.client.create_test_order(
                symbol=symbol,
                side='BUY',
                type='MARKET',
                quantity=quantity
            )
            logger.info(f"Placed buy order for {symbol}: {order}")
            
            # Record trade in history
            self.trade_history[symbol].append({
                'type': 'BUY',
                'price': float(self.client.get_symbol_ticker(symbol=symbol)['price']),
                'quantity': quantity,
                'time': datetime.now()
            })
            
            return True
        except BinanceAPIException as e:
            logger.error(f"Failed to place buy order for {symbol}: {str(e)}")
            return False
    
    def _place_sell_order(self, symbol, quantity, reason):
        """Place a sell order."""
        try:
            order = self.client.create_test_order(
                symbol=symbol,
                side='SELL',
                type='MARKET',
                quantity=quantity
            )
            logger.info(f"Placed sell order for {symbol} ({reason}): {order}")
            
            # Record trade in history
            self.trade_history[symbol].append({
                'type': 'SELL',
                'price': float(self.client.get_symbol_ticker(symbol=symbol)['price']),
                'quantity': quantity,
                'time': datetime.now(),
                'reason': reason
            })
            
            return True
        except BinanceAPIException as e:
            logger.error(f"Failed to place sell order for {symbol}: {str(e)}")
            return False
    
    def get_trade_history(self):
        """Get the complete trade history."""
        return self.trade_history 