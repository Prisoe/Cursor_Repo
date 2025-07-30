# Signals Bot - Premarket Trading Signal Generator

A sophisticated Python-based trading signals bot that analyzes premarket stock data and generates actionable trading signals with entry/exit prices, risk-reward ratios, and position sizing recommendations.

## Features

### 📊 **Data Analysis**
- Fetches real-time premarket stock data using yfinance and Yahoo Finance API
- Analyzes volume, price gaps, and momentum indicators
- Filters stocks based on configurable criteria (price, volume, gap percentage)

### 🧠 **Trading Strategies**
- **Gap Momentum Strategy**: Trades price gaps with volume confirmation
- **Volume Breakout Strategy**: Identifies volume spikes for momentum plays
- **Premarket Momentum Strategy**: Analyzes premarket price action for trading opportunities

### 💰 **Risk Management**
- Automatic position sizing based on risk tolerance
- Configurable risk-reward ratios (minimum 2:1 default)
- Stop-loss and take-profit calculations
- Maximum position size limits

### 📈 **Signal Generation**
- Confidence scoring for each signal (0-100%)
- Entry price, stop-loss, and take-profit levels
- Expected risk-reward ratios
- Detailed reasoning for each signal

## Installation

1. **Clone or download the project files**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Optional: Set up API keys (create `.env` file):**
```env
ALPHA_VANTAGE_KEY=your_key_here
FINNHUB_KEY=your_key_here
```

## Quick Start

### Basic Usage
```python
from signals_bot import SignalsBot
import asyncio

async def run_bot():
    bot = SignalsBot()
    result = await bot.run_analysis()
    
    # Print formatted report
    report = bot.format_signals_report(result)
    print(report)

# Run the bot
asyncio.run(run_bot())
```

### Command Line Usage
```bash
# Run with default settings
python signals_bot.py

# Run examples with different configurations
python example_usage.py
```

## Configuration

Edit `config.py` to customize the bot's behavior:

```python
@dataclass
class TradingConfig:
    max_risk_per_trade: float = 0.02        # 2% max risk per trade
    min_risk_reward_ratio: float = 2.0      # Minimum 2:1 R:R
    max_position_size: float = 0.10         # 10% max position size
    gap_threshold_percent: float = 3.0      # Minimum 3% gap
    volume_threshold_multiplier: float = 2.0 # Volume must be 2x average
```

## Signal Output

Each signal includes:

```json
{
  "symbol": "AAPL",
  "strategy": "Gap Momentum",
  "signal_type": "BUY",
  "confidence": 0.85,
  "current_price": 150.25,
  "entry_price": 150.25,
  "stop_loss": 145.74,
  "take_profit": 159.27,
  "risk_reward_ratio": 2.0,
  "gap_percent": 4.2,
  "reasoning": "Gap up 4.2% with 2.5x volume",
  "position_sizing": {
    "shares": 444,
    "position_value": 66710.0,
    "position_percent": 6.7,
    "risk_amount": 2000.0,
    "potential_profit": 4005.68,
    "potential_loss": 2000.44
  }
}
```

## Trading Strategies Explained

### 1. Gap Momentum Strategy
- **What it does**: Identifies stocks with significant price gaps (up or down) from previous close
- **Entry criteria**: 
  - Gap ≥ 3% (configurable)
  - Volume ≥ 2x average (configurable)
- **Use case**: Momentum continuation or reversal plays

### 2. Volume Breakout Strategy  
- **What it does**: Finds stocks with unusual volume spikes
- **Entry criteria**:
  - Volume ≥ 3x average
  - Price movement > 1%
- **Use case**: Early momentum detection

### 3. Premarket Momentum Strategy
- **What it does**: Analyzes premarket price action vs previous close
- **Entry criteria**:
  - Premarket move ≥ 2%
  - Significant premarket volume
- **Use case**: Premarket continuation or reversal plays

## Risk Management

The bot implements several risk management features:

- **Position Sizing**: Automatically calculates share quantity based on risk tolerance
- **Stop Losses**: Sets appropriate stop-loss levels for each strategy
- **Risk-Reward**: Ensures minimum risk-reward ratios are met
- **Portfolio Limits**: Prevents over-concentration in single positions

## Example Scenarios

### Conservative Trading (Low Risk)
```python
conservative_config = TradingConfig(
    max_risk_per_trade=0.01,    # 1% risk
    min_risk_reward_ratio=3.0,  # 3:1 R:R minimum
    gap_threshold_percent=5.0   # Higher gap requirement
)
```

### Aggressive Trading (Higher Risk)
```python
aggressive_config = TradingConfig(
    max_risk_per_trade=0.03,    # 3% risk
    min_risk_reward_ratio=1.5,  # 1.5:1 R:R minimum
    gap_threshold_percent=1.5   # Lower gap requirement
)
```

## Files Overview

- **`signals_bot.py`**: Main bot orchestrator and signal generator
- **`data_fetcher.py`**: Stock data retrieval and processing
- **`strategies.py`**: Trading strategy implementations
- **`config.py`**: Configuration settings and parameters
- **`example_usage.py`**: Usage examples and demonstrations
- **`requirements.txt`**: Python dependencies

## Sample Output

```
================================================================================
               PREMARKET TRADING SIGNALS REPORT
================================================================================
Generated: 2024-01-15T09:25:33.123456
Analysis Duration: 12.3 seconds

SUMMARY:
  • Total Stocks Analyzed: 50
  • Signals Generated: 7
  • Average Confidence: 67.2%
  • Average Risk:Reward: 2.4:1
  • Buy Signals: 6
  • Sell Signals: 1
  • Total Risk Amount: $14,000.00
  • Total Position Value: $167,450.00

TOP TRADING SIGNALS:
--------------------------------------------------------------------------------

1. TSLA - Gap Momentum Strategy
   Signal: BUY | Confidence: 85.0%
   Current Price: $242.15 | Gap: +5.2%
   Entry: $242.15 | Stop: $234.88 | Target: $256.69
   Risk:Reward: 2.0:1
   Position: 275 shares ($66,591.25)
   Risk: $2,000.25 | Potential Profit: $4,000.50
   Volume: 3.2x normal
   Reasoning: Gap up 5.2% with 3.2x volume

[Additional signals...]
================================================================================
```

## Limitations & Disclaimers

⚠️ **Important Notes:**
- This is for educational purposes only
- Not financial advice - always do your own research
- Past performance doesn't guarantee future results
- Use paper trading first to test strategies
- Consider transaction costs and slippage
- Markets can be unpredictable

## Customization

You can easily customize the bot by:

1. **Adding new strategies** in `strategies.py`
2. **Modifying risk parameters** in `config.py`  
3. **Adding new data sources** in `data_fetcher.py`
4. **Changing the watchlist** in `config.py`

## Performance Tips

- Run during premarket hours (4:00 AM - 9:30 AM ET) for best results
- Use on a schedule (every 5-15 minutes) for real-time monitoring
- Combine with your own analysis and market knowledge
- Start with paper trading to validate signals

## Support & Contributing

This is an open-source educational project. Feel free to:
- Modify the code for your needs
- Add new strategies or features
- Improve the data sources
- Enhance the risk management

## License

This project is provided as-is for educational purposes. Use at your own risk.
