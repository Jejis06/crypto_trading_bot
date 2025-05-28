import logging
from binance.exceptions import BinanceAPIException

logger = logging.getLogger(__name__)

class SymbolManager:
    def __init__(self, client):
        self.client = client
        self.symbols = {}  # Cache for symbol information
        self.quote_assets = set()  # Available quote assets (USDT, BTC, etc.)
        self.refresh_symbols()
    
    def refresh_symbols(self):
        """Fetch and cache all available trading symbols."""
        try:
            exchange_info = self.client.get_exchange_info()
            
            # Reset caches
            self.symbols.clear()
            self.quote_assets.clear()
            
            # Process all symbols
            for symbol_info in exchange_info['symbols']:
                if symbol_info['status'] == 'TRADING':  # Only include active pairs
                    symbol = symbol_info['symbol']
                    quote_asset = symbol_info['quoteAsset']
                    
                    # Get filters with safe defaults
                    filters = {f['filterType']: f for f in symbol_info['filters']}
                    
                    try:
                        min_qty = float(filters.get('LOT_SIZE', {}).get('minQty', '0.00000001'))
                    except (ValueError, TypeError):
                        min_qty = 0.00000001
                        
                    try:
                        min_notional = float(filters.get('MIN_NOTIONAL', {}).get('minNotional', '10'))
                    except (ValueError, TypeError):
                        min_notional = 10
                    
                    self.symbols[symbol] = {
                        'baseAsset': symbol_info['baseAsset'],
                        'quoteAsset': quote_asset,
                        'filters': filters,
                        'minQty': min_qty,
                        'minNotional': min_notional
                    }
                    self.quote_assets.add(quote_asset)
            
            logger.info(f"Loaded {len(self.symbols)} trading pairs with {len(self.quote_assets)} quote assets")
            return True
            
        except BinanceAPIException as e:
            logger.error(f"Failed to fetch exchange information: {str(e)}")
            return False
    
    def get_symbols_for_quote_asset(self, quote_asset='USDT'):
        """Get all trading pairs for a specific quote asset."""
        return {symbol: info for symbol, info in self.symbols.items() 
                if info['quoteAsset'] == quote_asset}
    
    def get_top_volume_symbols(self, quote_asset='USDT', limit=20):
        """Get top trading pairs by 24h volume."""
        try:
            # Get 24h ticker for all symbols
            tickers = self.client.get_ticker()
            
            # Filter and sort by volume
            quote_pairs = [t for t in tickers if t['symbol'] in self.symbols 
                         and self.symbols[t['symbol']]['quoteAsset'] == quote_asset]
            sorted_pairs = sorted(quote_pairs, key=lambda x: float(x['volume']), reverse=True)
            
            return [{'symbol': t['symbol'], 
                    'volume': float(t['volume']), 
                    'price': float(t['lastPrice'])} 
                   for t in sorted_pairs[:limit]]
            
        except BinanceAPIException as e:
            logger.error(f"Failed to fetch top volume symbols: {str(e)}")
            return []
    
    def get_symbol_info(self, symbol):
        """Get detailed information for a specific symbol."""
        return self.symbols.get(symbol)
    
    def validate_symbol(self, symbol):
        """Check if a symbol is valid and currently trading."""
        return symbol in self.symbols
    
    def get_quantity_precision(self, symbol):
        """Get the quantity precision for a symbol."""
        try:
            symbol_info = self.symbols.get(symbol)
            if not symbol_info:
                return 8  # Default precision
                
            lot_size = symbol_info['filters'].get('LOT_SIZE', {})
            step_size = float(lot_size.get('stepSize', '0.00000001'))
            
            # Calculate precision from step size
            precision = str(step_size)[::-1].find('.')
            return precision if precision != -1 else 0
            
        except Exception as e:
            logger.error(f"Error getting precision for {symbol}: {str(e)}")
            return 8  # Default precision
    
    def calculate_quantity(self, symbol, quote_amount):
        """Calculate the quantity to buy based on quote amount and current price."""
        try:
            symbol_info = self.symbols.get(symbol)
            if not symbol_info:
                raise ValueError(f"Symbol {symbol} not found")
            
            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            
            # Calculate raw quantity
            quantity = quote_amount / price
            
            # Get step size with safe default
            lot_size = symbol_info['filters'].get('LOT_SIZE', {})
            step_size = float(lot_size.get('stepSize', '0.00000001'))
            precision = self.get_quantity_precision(symbol)
            
            # Round down to valid step size
            quantity = (quantity // step_size) * step_size
            quantity = round(quantity, precision)
            
            # Check MIN_NOTIONAL
            min_notional = symbol_info['minNotional']
            if quantity * price < min_notional:
                raise ValueError(f"Order value ({quantity * price}) is less than minimum ({min_notional})")
            
            return quantity
            
        except Exception as e:
            logger.error(f"Error calculating quantity for {symbol}: {str(e)}")
            return None 