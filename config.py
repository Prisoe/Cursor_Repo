"""
Configuration settings for the Signals Bot
"""
from dataclasses import dataclass
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class TradingConfig:
    """Trading configuration parameters"""
    
    # Risk Management
    max_risk_per_trade: float = 0.02  # 2% max risk per trade
    min_risk_reward_ratio: float = 2.0  # Minimum 2:1 R:R
    max_position_size: float = 0.10  # 10% max position size
    
    # Strategy Parameters
    volume_threshold_multiplier: float = 2.0  # Volume must be 2x average
    gap_threshold_percent: float = 3.0  # Minimum 3% gap
    momentum_lookback_days: int = 5
    
    # Premarket Settings
    premarket_start_time: str = "04:00"
    premarket_end_time: str = "09:30"
    min_price: float = 1.0  # Minimum stock price
    max_price: float = 500.0  # Maximum stock price
    
    # Data Sources
    max_stocks_to_analyze: int = 50
    data_refresh_interval: int = 300  # 5 minutes
    
    # Strategy Weights
    strategy_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.strategy_weights is None:
            self.strategy_weights = {
                'gap_momentum': 0.4,
                'volume_breakout': 0.3,
                'premarket_momentum': 0.3
            }

@dataclass
class APIConfig:
    """API configuration for data sources"""
    
    # Yahoo Finance (free)
    use_yfinance: bool = True
    
    # Add other API keys here as needed
    alpha_vantage_key: str = os.getenv('ALPHA_VANTAGE_KEY', '')
    finnhub_key: str = os.getenv('FINNHUB_KEY', '')
    
    # Rate limiting
    requests_per_second: float = 10.0
    max_concurrent_requests: int = 5

# Global configuration instances
trading_config = TradingConfig()
api_config = APIConfig()

# Most active premarket stocks list (can be updated)
WATCHLIST_SYMBOLS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'BRK.B',
    'LLY', 'AVGO', 'WMT', 'JPM', 'XOM', 'UNH', 'V', 'PG', 'MA', 'JNJ',
    'HD', 'CVX', 'ABBV', 'PEP', 'KO', 'BAC', 'TMO', 'COST', 'MRK', 'NFLX',
    'CRM', 'ACN', 'LIN', 'ABT', 'ADBE', 'CSCO', 'DHR', 'VZ', 'TXN', 'NKE',
    'WFC', 'PM', 'RTX', 'INTC', 'UPS', 'CMCSA', 'NEE', 'T', 'COP', 'ORCL'
]