"""
Stock data fetcher for premarket and regular market data
"""
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import asyncio
import aiohttp
import logging
from dataclasses import dataclass
from config import trading_config, api_config, WATCHLIST_SYMBOLS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StockData:
    """Stock data container"""
    symbol: str
    current_price: float
    previous_close: float
    premarket_price: float = None
    premarket_volume: int = 0
    regular_volume: int = 0
    avg_volume: float = 0
    gap_percent: float = 0
    market_cap: float = 0
    timestamp: datetime = None

class PremarketDataFetcher:
    """Fetches premarket and regular market stock data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    async def get_premarket_data(self, symbols: List[str]) -> Dict[str, StockData]:
        """
        Fetch premarket data for multiple symbols
        """
        results = {}
        
        # Use yfinance for basic data
        if api_config.use_yfinance:
            yf_data = await self._fetch_yfinance_data(symbols)
            results.update(yf_data)
        
        # Get additional premarket data from Yahoo Finance API
        premarket_data = await self._fetch_yahoo_premarket_data(symbols)
        
        # Merge premarket data
        for symbol, pm_data in premarket_data.items():
            if symbol in results:
                results[symbol].premarket_price = pm_data.get('premarket_price')
                results[symbol].premarket_volume = pm_data.get('premarket_volume', 0)
        
        return results
    
    async def _fetch_yfinance_data(self, symbols: List[str]) -> Dict[str, StockData]:
        """Fetch basic stock data using yfinance"""
        results = {}
        
        try:
            # Fetch data in chunks to avoid rate limits
            chunk_size = 10
            for i in range(0, len(symbols), chunk_size):
                chunk = symbols[i:i + chunk_size]
                tickers = yf.Tickers(' '.join(chunk))
                
                for symbol in chunk:
                    try:
                        ticker = tickers.tickers[symbol]
                        info = ticker.info
                        hist = ticker.history(period="5d", interval="1d")
                        
                        if not hist.empty and info:
                            current_price = info.get('currentPrice', hist['Close'].iloc[-1])
                            previous_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
                            
                            stock_data = StockData(
                                symbol=symbol,
                                current_price=float(current_price),
                                previous_close=float(previous_close),
                                regular_volume=int(info.get('volume', 0)),
                                avg_volume=float(info.get('averageVolume', 0)),
                                market_cap=float(info.get('marketCap', 0)),
                                timestamp=datetime.now()
                            )
                            
                            # Calculate gap percentage
                            if previous_close > 0:
                                stock_data.gap_percent = ((current_price - previous_close) / previous_close) * 100
                            
                            results[symbol] = stock_data
                            
                    except Exception as e:
                        logger.warning(f"Error fetching yfinance data for {symbol}: {e}")
                        continue
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in yfinance data fetch: {e}")
        
        return results
    
    async def _fetch_yahoo_premarket_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """Fetch premarket data from Yahoo Finance API"""
        results = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for symbol in symbols:
                task = self._get_yahoo_quote(session, symbol)
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, response in zip(symbols, responses):
                if isinstance(response, dict):
                    results[symbol] = response
        
        return results
    
    async def _get_yahoo_quote(self, session: aiohttp.ClientSession, symbol: str) -> Dict:
        """Get quote data from Yahoo Finance API"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {
                'region': 'US',
                'lang': 'en-US',
                'includePrePost': 'true',
                'interval': '1m',
                'range': '1d'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    chart_data = data.get('chart', {}).get('result', [])
                    
                    if chart_data:
                        meta = chart_data[0].get('meta', {})
                        premarket_price = meta.get('regularMarketPrice')
                        premarket_volume = meta.get('regularMarketVolume', 0)
                        
                        return {
                            'premarket_price': premarket_price,
                            'premarket_volume': premarket_volume
                        }
        except Exception as e:
            logger.warning(f"Error fetching Yahoo premarket data for {symbol}: {e}")
        
        return {}
    
    def get_most_active_premarket(self) -> List[str]:
        """
        Get most active premarket stocks
        For now, returns the watchlist but could be enhanced with real-time data
        """
        try:
            # This could be enhanced to fetch real most active stocks
            # For now, we'll use our predefined watchlist
            return WATCHLIST_SYMBOLS[:trading_config.max_stocks_to_analyze]
        except Exception as e:
            logger.error(f"Error getting most active premarket stocks: {e}")
            return WATCHLIST_SYMBOLS[:20]  # Fallback to first 20
    
    def filter_stocks_by_criteria(self, stock_data: Dict[str, StockData]) -> Dict[str, StockData]:
        """Filter stocks based on trading criteria"""
        filtered = {}
        
        for symbol, data in stock_data.items():
            # Price filter
            if data.current_price < trading_config.min_price or data.current_price > trading_config.max_price:
                continue
            
            # Volume filter (must have some volume)
            if data.regular_volume == 0 and data.premarket_volume == 0:
                continue
            
            # Gap filter (absolute value)
            if abs(data.gap_percent) < 1.0:  # At least 1% gap
                continue
            
            filtered[symbol] = data
        
        return filtered

# Async helper function for easy usage
async def fetch_premarket_stocks() -> Dict[str, StockData]:
    """Main function to fetch and filter premarket stock data"""
    fetcher = PremarketDataFetcher()
    
    # Get most active stocks
    symbols = fetcher.get_most_active_premarket()
    logger.info(f"Fetching data for {len(symbols)} symbols")
    
    # Fetch data
    stock_data = await fetcher.get_premarket_data(symbols)
    logger.info(f"Retrieved data for {len(stock_data)} stocks")
    
    # Filter based on criteria
    filtered_data = fetcher.filter_stocks_by_criteria(stock_data)
    logger.info(f"Filtered to {len(filtered_data)} stocks meeting criteria")
    
    return filtered_data