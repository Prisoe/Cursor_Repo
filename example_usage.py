#!/usr/bin/env python3
"""
Example usage of the Signals Bot
This script demonstrates how to use the signals bot with different configurations
"""
import asyncio
import json
from datetime import datetime
from signals_bot import SignalsBot
from config import trading_config, TradingConfig

async def basic_example():
    """Basic example - run the bot with default settings"""
    print("=" * 60)
    print("BASIC EXAMPLE - Default Settings")
    print("=" * 60)
    
    bot = SignalsBot()
    result = await bot.run_analysis()
    
    # Print formatted report
    report = bot.format_signals_report(result)
    print(report)
    
    return result

async def conservative_example():
    """Conservative trading example with tighter risk management"""
    print("\n" + "=" * 60)
    print("CONSERVATIVE EXAMPLE - Tight Risk Management")
    print("=" * 60)
    
    # Create conservative config
    conservative_config = TradingConfig(
        max_risk_per_trade=0.01,  # 1% max risk
        min_risk_reward_ratio=3.0,  # Minimum 3:1 R:R
        max_position_size=0.05,  # 5% max position
        gap_threshold_percent=5.0,  # Higher gap threshold
        volume_threshold_multiplier=3.0,  # Higher volume requirement
    )
    
    # Temporarily override global config
    original_config = trading_config
    import config
    config.trading_config = conservative_config
    
    try:
        bot = SignalsBot()
        result = await bot.run_analysis()
        
        report = bot.format_signals_report(result)
        print(report)
        
        return result
    finally:
        # Restore original config
        config.trading_config = original_config

async def aggressive_example():
    """Aggressive trading example with looser risk management"""
    print("\n" + "=" * 60)
    print("AGGRESSIVE EXAMPLE - Higher Risk/Reward")
    print("=" * 60)
    
    # Create aggressive config
    aggressive_config = TradingConfig(
        max_risk_per_trade=0.03,  # 3% max risk
        min_risk_reward_ratio=1.5,  # Lower R:R requirement
        max_position_size=0.15,  # 15% max position
        gap_threshold_percent=1.5,  # Lower gap threshold
        volume_threshold_multiplier=1.5,  # Lower volume requirement
    )
    
    # Temporarily override global config
    original_config = trading_config
    import config
    config.trading_config = aggressive_config
    
    try:
        bot = SignalsBot()
        result = await bot.run_analysis()
        
        report = bot.format_signals_report(result)
        print(report)
        
        return result
    finally:
        # Restore original config
        config.trading_config = original_config

async def custom_watchlist_example():
    """Example with custom watchlist of specific stocks"""
    print("\n" + "=" * 60)
    print("CUSTOM WATCHLIST EXAMPLE - Tech Stocks Only")
    print("=" * 60)
    
    # Override the watchlist temporarily
    original_watchlist = None
    try:
        import config
        original_watchlist = config.WATCHLIST_SYMBOLS
        
        # Custom tech-focused watchlist
        tech_watchlist = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
            'CRM', 'ADBE', 'ORCL', 'INTC', 'AMD', 'SNOW', 'PLTR', 'SQ',
            'PYPL', 'SHOP', 'ZM', 'DOCU', 'OKTA', 'TWLO', 'DDOG', 'NET'
        ]
        
        config.WATCHLIST_SYMBOLS = tech_watchlist
        
        bot = SignalsBot()
        result = await bot.run_analysis()
        
        report = bot.format_signals_report(result)
        print(report)
        
        return result
        
    finally:
        if original_watchlist:
            import config
            config.WATCHLIST_SYMBOLS = original_watchlist

def analyze_results(results):
    """Analyze and compare results from different strategies"""
    print("\n" + "=" * 60)
    print("RESULTS ANALYSIS")
    print("=" * 60)
    
    for i, (name, result) in enumerate(results.items()):
        summary = result['summary']
        print(f"\n{i+1}. {name}:")
        print(f"   Stocks Analyzed: {summary['total_stocks_analyzed']}")
        print(f"   Signals Generated: {summary['signals_generated']}")
        
        if summary['signals_generated'] > 0:
            print(f"   Avg Confidence: {summary['avg_confidence']:.1%}")
            print(f"   Avg R:R Ratio: {summary['avg_risk_reward']:.1f}:1")
            print(f"   Total Risk: ${summary['total_risk_amount']:,.2f}")
            print(f"   Total Position Value: ${summary['total_position_value']:,.2f}")
            
            # Show top signal
            top_signal = result['signals'][0] if result['signals'] else None
            if top_signal:
                print(f"   Top Signal: {top_signal['symbol']} ({top_signal['strategy']})")
                print(f"   Top Signal Confidence: {top_signal['confidence']:.1%}")

async def schedule_example():
    """Example of running the bot on a schedule"""
    print("\n" + "=" * 60)
    print("SCHEDULED EXAMPLE - Run Every 5 Minutes")
    print("=" * 60)
    print("Running signals bot every 5 minutes... (Press Ctrl+C to stop)")
    
    bot = SignalsBot()
    run_count = 0
    
    try:
        while True:
            run_count += 1
            print(f"\n--- Run #{run_count} at {datetime.now().strftime('%H:%M:%S')} ---")
            
            result = await bot.run_analysis()
            
            # Quick summary
            summary = result['summary']
            print(f"Found {summary['signals_generated']} signals from {summary['total_stocks_analyzed']} stocks")
            
            if result['signals']:
                top_signal = result['signals'][0]
                print(f"Top signal: {top_signal['symbol']} ({top_signal['confidence']:.1%} confidence)")
            
            # Save timestamped results
            filename = f"scheduled_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
            
            print(f"Results saved to {filename}")
            
            # Wait 5 minutes
            print("Waiting 5 minutes for next run...")
            await asyncio.sleep(300)  # 5 minutes
            
    except KeyboardInterrupt:
        print(f"\nScheduled runs stopped. Completed {run_count} runs.")

async def main():
    """Run all examples"""
    print("SIGNALS BOT - EXAMPLE USAGE")
    print("This script demonstrates various ways to use the signals bot")
    print("\nMake sure you have installed all dependencies:")
    print("pip install -r requirements.txt\n")
    
    results = {}
    
    try:
        # Run different examples
        results['Basic'] = await basic_example()
        results['Conservative'] = await conservative_example()
        results['Aggressive'] = await aggressive_example()
        results['Tech Watchlist'] = await custom_watchlist_example()
        
        # Analyze results
        analyze_results(results)
        
        # Ask user if they want to run scheduled example
        print("\n" + "=" * 60)
        print("Would you like to run the scheduled example?")
        print("This will run the bot every 5 minutes until stopped.")
        print("Type 'yes' to continue, or press Enter to skip:")
        
        # For demo purposes, we'll skip the interactive part
        # In a real scenario, you could use input() here
        print("Skipping scheduled example for demo purposes.")
        
        print("\n" + "=" * 60)
        print("EXAMPLE USAGE COMPLETE")
        print("=" * 60)
        print("Check the generated JSON files for detailed results.")
        print("You can modify the configuration in config.py to customize behavior.")
        
    except Exception as e:
        print(f"Error running examples: {e}")

if __name__ == "__main__":
    asyncio.run(main())