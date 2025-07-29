"""
Main Signals Bot - Generates trading signals from premarket data
"""
import asyncio
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import logging
import json
from dataclasses import asdict

from data_fetcher import fetch_premarket_stocks, StockData
from strategies import StrategyManager, StrategySignal
from config import trading_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SignalsBot:
    """Main signals bot class"""
    
    def __init__(self):
        self.strategy_manager = StrategyManager()
        self.last_run_time = None
        
    async def run_analysis(self) -> Dict:
        """Run complete analysis and return trading signals"""
        logger.info("Starting signals bot analysis...")
        start_time = datetime.now()
        
        try:
            # Fetch premarket stock data
            logger.info("Fetching premarket stock data...")
            stock_data = await fetch_premarket_stocks()
            
            if not stock_data:
                logger.warning("No stock data retrieved")
                return self._create_empty_result("No stock data available")
            
            logger.info(f"Analyzing {len(stock_data)} stocks for signals...")
            
            # Analyze stocks and generate signals
            all_signals = []
            for symbol, data in stock_data.items():
                signals = self.strategy_manager.analyze_stock(data)
                if signals:
                    # Get best signal for this stock
                    best_signal = self.strategy_manager.get_best_signal(signals)
                    if best_signal:
                        # Add position sizing information
                        position_info = self._calculate_position_info(best_signal, data)
                        all_signals.append((best_signal, data, position_info))
            
            # Sort signals by confidence and filter by minimum criteria
            valid_signals = [
                (signal, data, position_info) for signal, data, position_info in all_signals
                if signal.confidence >= 0.4 and signal.risk_reward_ratio >= trading_config.min_risk_reward_ratio
            ]
            
            # Sort by weighted score (confidence * R:R ratio)
            valid_signals.sort(
                key=lambda x: x[0].confidence * x[0].risk_reward_ratio, 
                reverse=True
            )
            
            # Take top signals
            top_signals = valid_signals[:10]  # Top 10 signals
            
            # Create result
            result = self._create_result(top_signals, stock_data, start_time)
            
            logger.info(f"Analysis complete. Found {len(top_signals)} valid signals")
            self.last_run_time = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in signals bot analysis: {e}")
            return self._create_empty_result(f"Error: {str(e)}")
    
    def _calculate_position_info(self, signal: StrategySignal, stock_data: StockData) -> Dict:
        """Calculate position sizing and risk information"""
        account_value = 100000  # $100k account assumption
        risk_amount = account_value * trading_config.max_risk_per_trade
        
        price_risk = abs(signal.entry_price - signal.stop_loss)
        if price_risk == 0:
            return {'shares': 0, 'position_value': 0, 'risk_amount': 0, 'position_percent': 0}
        
        shares = int(risk_amount / price_risk)
        position_value = shares * signal.entry_price
        max_position_value = account_value * trading_config.max_position_size
        
        # Don't exceed max position size
        if position_value > max_position_value:
            shares = int(max_position_value / signal.entry_price)
            position_value = shares * signal.entry_price
        
        return {
            'shares': shares,
            'position_value': position_value,
            'risk_amount': shares * price_risk,
            'position_percent': (position_value / account_value) * 100,
            'potential_profit': shares * (signal.take_profit - signal.entry_price),
            'potential_loss': shares * (signal.entry_price - signal.stop_loss)
        }
    
    def _create_result(self, signals_data: List, all_stock_data: Dict, start_time: datetime) -> Dict:
        """Create formatted result dictionary"""
        signals_list = []
        
        for signal, stock_data, position_info in signals_data:
            signal_dict = {
                'symbol': signal.symbol,
                'strategy': signal.strategy_name,
                'signal_type': signal.signal_type,
                'confidence': round(signal.confidence, 3),
                'current_price': round(stock_data.current_price, 2),
                'entry_price': round(signal.entry_price, 2),
                'stop_loss': round(signal.stop_loss, 2),
                'take_profit': round(signal.take_profit, 2),
                'risk_reward_ratio': round(signal.risk_reward_ratio, 2),
                'gap_percent': round(stock_data.gap_percent, 2),
                'reasoning': signal.reasoning,
                'position_sizing': {
                    'shares': position_info['shares'],
                    'position_value': round(position_info['position_value'], 2),
                    'position_percent': round(position_info['position_percent'], 1),
                    'risk_amount': round(position_info['risk_amount'], 2),
                    'potential_profit': round(position_info['potential_profit'], 2),
                    'potential_loss': round(position_info['potential_loss'], 2)
                },
                'volume_info': {
                    'current_volume': stock_data.regular_volume + stock_data.premarket_volume,
                    'avg_volume': int(stock_data.avg_volume),
                    'volume_ratio': round((stock_data.regular_volume + stock_data.premarket_volume) / max(stock_data.avg_volume, 1), 2)
                }
            }
            signals_list.append(signal_dict)
        
        # Summary statistics
        summary = {
            'total_stocks_analyzed': len(all_stock_data),
            'signals_generated': len(signals_list),
            'avg_confidence': round(sum(s['confidence'] for s in signals_list) / len(signals_list), 3) if signals_list else 0,
            'avg_risk_reward': round(sum(s['risk_reward_ratio'] for s in signals_list) / len(signals_list), 2) if signals_list else 0,
            'buy_signals': len([s for s in signals_list if s['signal_type'] == 'BUY']),
            'sell_signals': len([s for s in signals_list if s['signal_type'] == 'SELL']),
            'total_risk_amount': round(sum(s['position_sizing']['risk_amount'] for s in signals_list), 2),
            'total_position_value': round(sum(s['position_sizing']['position_value'] for s in signals_list), 2)
        }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'analysis_duration_seconds': (datetime.now() - start_time).total_seconds(),
            'summary': summary,
            'signals': signals_list,
            'config': {
                'max_risk_per_trade': trading_config.max_risk_per_trade,
                'min_risk_reward_ratio': trading_config.min_risk_reward_ratio,
                'gap_threshold_percent': trading_config.gap_threshold_percent,
                'volume_threshold_multiplier': trading_config.volume_threshold_multiplier
            }
        }
    
    def _create_empty_result(self, reason: str) -> Dict:
        """Create empty result when no signals found"""
        return {
            'timestamp': datetime.now().isoformat(),
            'analysis_duration_seconds': 0,
            'summary': {
                'total_stocks_analyzed': 0,
                'signals_generated': 0,
                'error': reason
            },
            'signals': [],
            'config': {
                'max_risk_per_trade': trading_config.max_risk_per_trade,
                'min_risk_reward_ratio': trading_config.min_risk_reward_ratio,
                'gap_threshold_percent': trading_config.gap_threshold_percent,
                'volume_threshold_multiplier': trading_config.volume_threshold_multiplier
            }
        }
    
    def format_signals_report(self, result: Dict) -> str:
        """Format signals into a readable report"""
        report = []
        report.append("=" * 80)
        report.append("               PREMARKET TRADING SIGNALS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {result['timestamp']}")
        report.append(f"Analysis Duration: {result['analysis_duration_seconds']:.1f} seconds")
        report.append("")
        
        # Summary
        summary = result['summary']
        report.append("SUMMARY:")
        report.append(f"  • Total Stocks Analyzed: {summary['total_stocks_analyzed']}")
        report.append(f"  • Signals Generated: {summary['signals_generated']}")
        
        if summary['signals_generated'] > 0:
            report.append(f"  • Average Confidence: {summary['avg_confidence']:.1%}")
            report.append(f"  • Average Risk:Reward: {summary['avg_risk_reward']}:1")
            report.append(f"  • Buy Signals: {summary['buy_signals']}")
            report.append(f"  • Sell Signals: {summary['sell_signals']}")
            report.append(f"  • Total Risk Amount: ${summary['total_risk_amount']:,.2f}")
            report.append(f"  • Total Position Value: ${summary['total_position_value']:,.2f}")
        
        if 'error' in summary:
            report.append(f"  • Error: {summary['error']}")
        
        report.append("")
        
        # Individual signals
        if result['signals']:
            report.append("TOP TRADING SIGNALS:")
            report.append("-" * 80)
            
            for i, signal in enumerate(result['signals'], 1):
                report.append(f"\n{i}. {signal['symbol']} - {signal['strategy']} Strategy")
                report.append(f"   Signal: {signal['signal_type']} | Confidence: {signal['confidence']:.1%}")
                report.append(f"   Current Price: ${signal['current_price']:.2f} | Gap: {signal['gap_percent']:+.1f}%")
                report.append(f"   Entry: ${signal['entry_price']:.2f} | Stop: ${signal['stop_loss']:.2f} | Target: ${signal['take_profit']:.2f}")
                report.append(f"   Risk:Reward: {signal['risk_reward_ratio']}:1")
                report.append(f"   Position: {signal['position_sizing']['shares']} shares (${signal['position_sizing']['position_value']:,.2f})")
                report.append(f"   Risk: ${signal['position_sizing']['risk_amount']:,.2f} | Potential Profit: ${signal['position_sizing']['potential_profit']:,.2f}")
                report.append(f"   Volume: {signal['volume_info']['volume_ratio']:.1f}x normal")
                report.append(f"   Reasoning: {signal['reasoning']}")
        else:
            report.append("No trading signals generated.")
        
        report.append("\n" + "=" * 80)
        report.append("DISCLAIMER: This is for educational purposes only. Always do your own research.")
        report.append("=" * 80)
        
        return "\n".join(report)

# Main execution function
async def main():
    """Main function to run the signals bot"""
    bot = SignalsBot()
    
    try:
        # Run analysis
        result = await bot.run_analysis()
        
        # Print formatted report
        report = bot.format_signals_report(result)
        print(report)
        
        # Optionally save to file
        with open(f"signals_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(result, f, indent=2)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        print(f"Error running signals bot: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())