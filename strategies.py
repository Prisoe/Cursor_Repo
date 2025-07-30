"""
Trading strategies for the Signals Bot
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
from data_fetcher import StockData
from config import trading_config

logger = logging.getLogger(__name__)

@dataclass
class StrategySignal:
    """Trading signal from a strategy"""
    symbol: str
    strategy_name: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float  # 0.0 to 1.0
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    reasoning: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class BaseStrategy:
    """Base class for all trading strategies"""
    
    def __init__(self, name: str):
        self.name = name
    
    def analyze(self, stock_data: StockData) -> Optional[StrategySignal]:
        """Analyze stock data and return a trading signal"""
        raise NotImplementedError
    
    def calculate_position_sizing(self, stock_data: StockData, entry_price: float, stop_loss: float) -> Dict:
        """Calculate position sizing based on risk management rules"""
        account_value = 100000  # Assume $100k account for calculation
        risk_amount = account_value * trading_config.max_risk_per_trade
        
        price_risk = abs(entry_price - stop_loss)
        if price_risk == 0:
            return {'shares': 0, 'position_value': 0, 'risk_amount': 0}
        
        shares = int(risk_amount / price_risk)
        position_value = shares * entry_price
        max_position_value = account_value * trading_config.max_position_size
        
        # Don't exceed max position size
        if position_value > max_position_value:
            shares = int(max_position_value / entry_price)
            position_value = shares * entry_price
        
        return {
            'shares': shares,
            'position_value': position_value,
            'risk_amount': shares * price_risk,
            'position_percent': (position_value / account_value) * 100
        }

class GapMomentumStrategy(BaseStrategy):
    """Gap momentum strategy - trades gaps with volume confirmation"""
    
    def __init__(self):
        super().__init__("Gap Momentum")
    
    def analyze(self, stock_data: StockData) -> Optional[StrategySignal]:
        """Analyze gap momentum signals"""
        try:
            gap_percent = stock_data.gap_percent
            current_price = stock_data.current_price
            volume_ratio = 1.0
            
            # Calculate volume ratio if we have average volume data
            if stock_data.avg_volume > 0:
                total_volume = stock_data.regular_volume + stock_data.premarket_volume
                volume_ratio = total_volume / stock_data.avg_volume
            
            # Gap up strategy
            if gap_percent >= trading_config.gap_threshold_percent:
                if volume_ratio >= trading_config.volume_threshold_multiplier:
                    # Strong gap up with volume - bullish signal
                    entry_price = current_price
                    stop_loss = current_price * 0.97  # 3% stop loss
                    take_profit = current_price * 1.06  # 6% take profit
                    
                    confidence = min(0.9, (gap_percent / 10.0) * (volume_ratio / 3.0))
                    
                    return StrategySignal(
                        symbol=stock_data.symbol,
                        strategy_name=self.name,
                        signal_type='BUY',
                        confidence=confidence,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        risk_reward_ratio=(take_profit - entry_price) / (entry_price - stop_loss),
                        reasoning=f"Gap up {gap_percent:.1f}% with {volume_ratio:.1f}x volume"
                    )
            
            # Gap down strategy
            elif gap_percent <= -trading_config.gap_threshold_percent:
                if volume_ratio >= trading_config.volume_threshold_multiplier:
                    # Strong gap down with volume - potential bounce
                    entry_price = current_price
                    stop_loss = current_price * 0.95  # 5% stop loss
                    take_profit = current_price * 1.08  # 8% take profit (bigger target for counter-trend)
                    
                    confidence = min(0.8, (abs(gap_percent) / 15.0) * (volume_ratio / 3.0))
                    
                    return StrategySignal(
                        symbol=stock_data.symbol,
                        strategy_name=self.name,
                        signal_type='BUY',
                        confidence=confidence,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        risk_reward_ratio=(take_profit - entry_price) / (entry_price - stop_loss),
                        reasoning=f"Gap down {gap_percent:.1f}% bounce play with {volume_ratio:.1f}x volume"
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in gap momentum analysis for {stock_data.symbol}: {e}")
            return None

class VolumeBreakoutStrategy(BaseStrategy):
    """Volume breakout strategy - trades volume spikes"""
    
    def __init__(self):
        super().__init__("Volume Breakout")
    
    def analyze(self, stock_data: StockData) -> Optional[StrategySignal]:
        """Analyze volume breakout signals"""
        try:
            current_price = stock_data.current_price
            total_volume = stock_data.regular_volume + stock_data.premarket_volume
            
            if stock_data.avg_volume == 0:
                return None
            
            volume_ratio = total_volume / stock_data.avg_volume
            
            # Look for significant volume spike
            if volume_ratio >= trading_config.volume_threshold_multiplier * 1.5:  # 3x normal volume
                gap_percent = stock_data.gap_percent
                
                # Determine direction based on gap
                if gap_percent > 1.0:  # Positive momentum
                    entry_price = current_price
                    stop_loss = current_price * 0.96  # 4% stop loss
                    take_profit = current_price * 1.08  # 8% take profit
                    signal_type = 'BUY'
                    reasoning = f"Volume breakout {volume_ratio:.1f}x with {gap_percent:.1f}% gap up"
                    
                elif gap_percent < -1.0:  # Negative momentum - short opportunity
                    entry_price = current_price
                    stop_loss = current_price * 1.04  # 4% stop loss for short
                    take_profit = current_price * 0.92  # 8% take profit for short
                    signal_type = 'SELL'
                    reasoning = f"Volume breakout {volume_ratio:.1f}x with {gap_percent:.1f}% gap down"
                
                else:
                    return None
                
                confidence = min(0.85, volume_ratio / 5.0)
                
                rr_ratio = abs(take_profit - entry_price) / abs(entry_price - stop_loss)
                
                return StrategySignal(
                    symbol=stock_data.symbol,
                    strategy_name=self.name,
                    signal_type=signal_type,
                    confidence=confidence,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_reward_ratio=rr_ratio,
                    reasoning=reasoning
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in volume breakout analysis for {stock_data.symbol}: {e}")
            return None

class PremarketMomentumStrategy(BaseStrategy):
    """Premarket momentum strategy - trades premarket price action"""
    
    def __init__(self):
        super().__init__("Premarket Momentum")
    
    def analyze(self, stock_data: StockData) -> Optional[StrategySignal]:
        """Analyze premarket momentum signals"""
        try:
            current_price = stock_data.current_price
            previous_close = stock_data.previous_close
            premarket_price = stock_data.premarket_price or current_price
            
            # Calculate premarket move
            if previous_close > 0:
                premarket_move = ((premarket_price - previous_close) / previous_close) * 100
            else:
                return None
            
            # Look for significant premarket moves
            if abs(premarket_move) >= 2.0:  # At least 2% premarket move
                premarket_volume_ratio = 1.0
                if stock_data.avg_volume > 0 and stock_data.premarket_volume > 0:
                    # Calculate what portion of daily volume happened premarket
                    premarket_volume_ratio = stock_data.premarket_volume / (stock_data.avg_volume * 0.1)  # 10% of daily volume is significant premarket
                
                if premarket_move > 2.0:  # Positive premarket momentum
                    entry_price = current_price
                    stop_loss = current_price * 0.97  # 3% stop loss
                    take_profit = current_price * 1.06  # 6% take profit
                    signal_type = 'BUY'
                    reasoning = f"Premarket momentum +{premarket_move:.1f}% with volume"
                    
                elif premarket_move < -2.0:  # Negative premarket momentum
                    # Look for potential reversal
                    entry_price = current_price
                    stop_loss = current_price * 0.94  # 6% stop loss (wider for counter-trend)
                    take_profit = current_price * 1.09  # 9% take profit
                    signal_type = 'BUY'
                    reasoning = f"Premarket oversold {premarket_move:.1f}% reversal play"
                
                else:
                    return None
                
                confidence = min(0.8, (abs(premarket_move) / 8.0) * premarket_volume_ratio)
                
                rr_ratio = (take_profit - entry_price) / (entry_price - stop_loss)
                
                return StrategySignal(
                    symbol=stock_data.symbol,
                    strategy_name=self.name,
                    signal_type=signal_type,
                    confidence=confidence,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    risk_reward_ratio=rr_ratio,
                    reasoning=reasoning
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in premarket momentum analysis for {stock_data.symbol}: {e}")
            return None

class StrategyManager:
    """Manages multiple trading strategies"""
    
    def __init__(self):
        self.strategies = [
            GapMomentumStrategy(),
            VolumeBreakoutStrategy(),
            PremarketMomentumStrategy()
        ]
    
    def analyze_stock(self, stock_data: StockData) -> List[StrategySignal]:
        """Run all strategies on a stock and return signals"""
        signals = []
        
        for strategy in self.strategies:
            try:
                signal = strategy.analyze(stock_data)
                if signal and signal.confidence > 0.3:  # Minimum confidence threshold
                    # Check risk-reward ratio
                    if signal.risk_reward_ratio >= trading_config.min_risk_reward_ratio:
                        signals.append(signal)
            except Exception as e:
                logger.error(f"Error running strategy {strategy.name} on {stock_data.symbol}: {e}")
        
        return signals
    
    def get_best_signal(self, signals: List[StrategySignal]) -> Optional[StrategySignal]:
        """Get the best signal from multiple signals for a stock"""
        if not signals:
            return None
        
        # Weight signals by strategy weights and confidence
        weighted_signals = []
        
        for signal in signals:
            strategy_weight = trading_config.strategy_weights.get(
                signal.strategy_name.lower().replace(' ', '_'), 0.5
            )
            weighted_score = signal.confidence * strategy_weight
            weighted_signals.append((weighted_score, signal))
        
        # Return signal with highest weighted score
        weighted_signals.sort(key=lambda x: x[0], reverse=True)
        return weighted_signals[0][1]