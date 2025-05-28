import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class BotValidator:
    """Validates trading bot configurations and ensures they meet requirements."""
    
    # Define valid strategies and their required fields
    STRATEGY_REQUIREMENTS = {
        'instant_buy': {
            'required_fields': [
                'name', 'symbol', 'strategy', 'investment_amount'
            ],
            'optional_fields': [
                'description', 'profit_target', 'stop_loss'
            ],
            'value_ranges': {
                'investment_amount': (10, 1000),
                'profit_target': (1.001, 1.5),
                'stop_loss': (0.5, 0.999)
            }
        },
        'simple': {
            'required_fields': [
                'name', 'symbol', 'strategy', 'investment_amount',
                'profit_target', 'stop_loss'
            ],
            'optional_fields': [
                'description', 'max_trades_per_day', 'min_volume_24h',
                'max_spread_percent', 'enable_trailing_stop'
            ],
            'value_ranges': {
                'investment_amount': (10, 1000),
                'profit_target': (1.001, 1.5),
                'stop_loss': (0.5, 0.999),
                'max_trades_per_day': (1, 100),
                'max_spread_percent': (0.01, 5.0)
            }
        },
        'portfolio': {
            'required_fields': [
                'name', 'strategy', 'quote_asset', 'max_symbols',
                'investment_per_coin', 'profit_target', 'stop_loss',
                'max_holdings', 'symbol_selection'
            ],
            'optional_fields': [
                'description', 'rebalance_interval', 'min_volume_24h',
                'max_allocation_percent', 'enable_trailing_stop'
            ],
            'value_ranges': {
                'max_symbols': (1, 50),
                'investment_per_coin': (10, 1000),
                'profit_target': (1.001, 1.5),
                'stop_loss': (0.5, 0.999),
                'max_holdings': (1, 50),
                'max_allocation_percent': (1, 100)
            }
        },
        'grid': {
            'required_fields': [
                'name', 'symbol', 'strategy', 'investment_amount',
                'grid_levels', 'grid_spread_percent'
            ],
            'optional_fields': [
                'description', 'min_volume_24h', 'max_spread_percent',
                'auto_adjust_levels'
            ],
            'value_ranges': {
                'investment_amount': (10, 1000),
                'grid_levels': (3, 100),
                'grid_spread_percent': (0.1, 5.0),
                'max_spread_percent': (0.01, 5.0)
            }
        },
        'dca': {  # Dollar Cost Averaging
            'required_fields': [
                'name', 'symbol', 'strategy', 'investment_amount',
                'interval_hours', 'total_periods'
            ],
            'optional_fields': [
                'description', 'min_volume_24h', 'max_spread_percent',
                'profit_target', 'stop_loss'
            ],
            'value_ranges': {
                'investment_amount': (10, 1000),
                'interval_hours': (1, 168),
                'total_periods': (2, 52),
                'profit_target': (1.001, 1.5),
                'stop_loss': (0.5, 0.999)
            }
        }
    }

    @classmethod
    def validate_bot_config(cls, config: Dict[str, Any], symbol_manager=None) -> Tuple[bool, List[str]]:
        """
        Validate a bot configuration.
        
        Args:
            config: Bot configuration dictionary
            symbol_manager: Optional SymbolManager instance for symbol validation
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if strategy is valid
        strategy = config.get('strategy')
        if not strategy:
            return False, ["No strategy specified"]
        if strategy not in cls.STRATEGY_REQUIREMENTS:
            return False, [f"Invalid strategy: {strategy}"]
        
        requirements = cls.STRATEGY_REQUIREMENTS[strategy]
        
        # Check required fields
        for field in requirements['required_fields']:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Validate value ranges
        for field, (min_val, max_val) in requirements['value_ranges'].items():
            if field in config:
                value = config[field]
                if not isinstance(value, (int, float)) or value < min_val or value > max_val:
                    errors.append(f"{field} must be between {min_val} and {max_val}")
        
        # Strategy-specific validations
        if strategy != 'portfolio' and 'symbol' in config:
            if symbol_manager and not symbol_manager.validate_symbol(config['symbol']):
                errors.append(f"Invalid symbol: {config['symbol']}")
        
        # Validate symbol selection for portfolio strategy
        if strategy == 'portfolio':
            if 'symbol_selection' in config:
                sel = config['symbol_selection']
                if not isinstance(sel, dict) or 'method' not in sel:
                    errors.append("Invalid symbol_selection configuration")
                elif sel['method'] not in ['top_volume', 'manual']:
                    errors.append(f"Invalid symbol selection method: {sel['method']}")
        
        # Additional strategy-specific validations
        if strategy == 'grid':
            if 'grid_levels' in config and 'grid_spread_percent' in config:
                total_spread = config['grid_levels'] * config['grid_spread_percent']
                if total_spread > 100:
                    errors.append("Total grid spread exceeds 100%")
        
        return len(errors) == 0, errors

    @classmethod
    def get_strategy_template(cls, strategy: str) -> Dict[str, Any]:
        """Get a template configuration for a specific strategy."""
        if strategy not in cls.STRATEGY_REQUIREMENTS:
            raise ValueError(f"Invalid strategy: {strategy}")
        
        template = {
            'name': f"{strategy.capitalize()} Trading Bot",
            'strategy': strategy,
            'description': f"A {strategy} trading bot"
        }
        
        # Add required fields with default values
        requirements = cls.STRATEGY_REQUIREMENTS[strategy]
        for field in requirements['required_fields']:
            if field not in template:
                if field in requirements['value_ranges']:
                    min_val, max_val = requirements['value_ranges'][field]
                    if isinstance(min_val, int):
                        template[field] = min_val
                    else:
                        template[field] = round(min_val + (max_val - min_val) * 0.1, 3)
        
        return template 