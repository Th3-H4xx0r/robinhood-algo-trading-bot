"""
Simple Backtest Example

Demonstrates how to run a basic backtest using the BuyAndHoldStrategy.
This script loads historical data for AAPL in 2023 and runs a buy-and-hold
strategy to establish baseline performance.

Usage:
    python simple_backtest.py

Requirements:
    - ALPACA_API_KEY environment variable set
    - ALPACA_API_SECRET environment variable set
    - Or Yahoo Finance fallback enabled

Output:
    Prints backtest results including:
    - Total return percentage
    - Number of trades
    - Win rate
    - Maximum drawdown
    - Sharpe ratio
    - List of all trades with entry/exit details

Example Output:
    === Simple Backtest: AAPL 2023 ===

    Strategy: BuyAndHoldStrategy
    Symbol: AAPL
    Period: 2023-01-01 to 2023-12-31
    Initial Capital: $100,000.00

    Performance Metrics:
    --------------------------------------------------
    Total Return:     +48.25%
    Annualized Return: +48.25%
    CAGR:             +48.25%
    Win Rate:         100.00%
    Profit Factor:    N/A (no losing trades)
    Max Drawdown:     -12.34%
    Sharpe Ratio:     2.15

    Trade Summary:
    --------------------------------------------------
    Total Trades:     1
    Winning Trades:   1
    Losing Trades:    0
    Average Win:      $48,250.00
    Average Loss:     $0.00

    Trade Details:
    --------------------------------------------------
    Trade #1: AAPL
      Entry: 2023-01-03 at $130.50 (550 shares)
      Exit:  2023-12-29 at $193.58 (550 shares)
      P&L:   +$34,694.00 (+48.25%)
      Duration: 360 days
      Reason: end_of_data
"""
import logging
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from dotenv import load_dotenv

# --- CONFIGURATION START ---

# 1. Get the folder where THIS script (backtest.py) is located
# Since backtest.py is in the project root, this IS the project root.
project_root = Path(__file__).resolve().parent

# 2. Point to the .env file in this same folder
env_path = project_root / ".env"

# 3. Load the .env file
loaded = load_dotenv(dotenv_path=env_path)

# Debug: Verify it worked
print(f"DEBUG: Loading .env from: {env_path}")
print(f"DEBUG: Success? {loaded}")

# 4. Ensure imports work by adding project root to Python path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- CONFIGURATION END ---

# ... Continue with your normal imports ...
import pandas as pd
import yfinance as yf
# Note: Since backtest.py is in the root, we import directly from src or examples
from examples.sample_strategies import BuyAndHoldStrategy
from src.trading_bot.backtest.models import BacktestConfig

logger = logging.getLogger(__name__)

# Check if engine is available (it may not be implemented yet)
try:
    from src.trading_bot.backtest.engine import BacktestEngine
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False
    print("WARNING: BacktestEngine not yet implemented.")
    print("This example will be functional once T027 (BacktestEngine) is completed.")
    sys.exit(0)


def format_currency(value: Decimal) -> str:
    """Format Decimal as currency string."""
    return f"${value:,.2f}"


def format_percentage(value: Decimal) -> str:
    """Format Decimal as percentage string."""
    return f"{value * 100:+.2f}%"

def fetch_historical_data(symbol: str = "SPY", period: str = "2y") -> pd.DataFrame:
    """Fetch historical OHLCV data.

    Args:
        symbol: Ticker symbol
        period: Data period (1y, 2y, 5y, etc.)

    Returns:
        DataFrame with OHLCV data
    """
    logger.info(f"Fetching historical data for {symbol} ({period})")

    ticker = yf.Ticker(symbol)
    data = ticker.history(period=period, interval="1d")

    # Rename columns to match expected format
    data.columns = [c.lower() for c in data.columns]

    logger.info(f"Downloaded {len(data)} bars of data")

    return data


def main() -> None:
    """Run simple backtest example."""
    print("=== Simple Backtest: AAPL 2023 ===")
    print()

    # Check for API credentials
    api_key = os.getenv("ALPACA_API_KEY")
    api_secret = os.getenv("ALPACA_API_SECRET")

    if not api_key or not api_secret:
        print("WARNING: ALPACA_API_KEY and ALPACA_API_SECRET not set.")
        print("Backtest will attempt to use Yahoo Finance fallback.")
        print()

    symbols = ["AAPL"]
    market_data = {}

    for symbol in symbols:
        try:
            data = fetch_historical_data(symbol, period="2y")
            market_data[symbol] = data
        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")

    if not market_data:
        logger.error("No market data available. Exiting.")
        return

    # Use SPY for main pipeline
    data = market_data["AAPL"]
    
    # Configure backtest
    config = BacktestConfig(
        strategy_class=BuyAndHoldStrategy,
        symbols=["AAPL"],
        start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 1, 30, tzinfo=timezone.utc),
        initial_capital=Decimal("7000.0"),
        commission=Decimal("0.0"),  # Robinhood: $0 commission
        slippage_pct=Decimal("0.001"),  # 0.1% slippage
        risk_free_rate=Decimal("0.02"),  # 2% risk-free rate
        cache_enabled=True,
    )

    print(f"Strategy: {config.strategy_class.__name__}")
    print(f"Symbol: {config.symbols[0]}")
    print(f"Period: {config.start_date.date()} to {config.end_date.date()}")
    print(f"Initial Capital: {format_currency(config.initial_capital)}")
    print()

    # Run backtest
    print("Running backtest...")
    engine = BacktestEngine()
    result = engine.run(config, historical_data=data)
    print("Backtest complete.")
    print()

    # Print performance metrics
    metrics = result.metrics
    print("Performance Metrics:")
    print("-" * 50)
    print(f"Total Return:     {format_percentage(metrics.total_return)}")
    print(f"Annualized Return: {format_percentage(metrics.annualized_return)}")
    print(f"CAGR:             {format_percentage(metrics.cagr)}")
    print(f"Win Rate:         {metrics.win_rate * 100:.2f}%")
    if metrics.profit_factor > 0:
        print(f"Profit Factor:    {metrics.profit_factor:.2f}")
    else:
        print("Profit Factor:    N/A (no losing trades)")
    print(f"Max Drawdown:     {format_percentage(metrics.max_drawdown)}")
    print(f"Sharpe Ratio:     {metrics.sharpe_ratio:.2f}")
    print()

    # Print trade summary
    print("Trade Summary:")
    print("-" * 50)
    print(f"Total Trades:     {metrics.total_trades}")
    print(f"Winning Trades:   {metrics.winning_trades}")
    print(f"Losing Trades:    {metrics.losing_trades}")
    print(f"Average Win:      {format_currency(metrics.average_win)}")
    print(f"Average Loss:     {format_currency(metrics.average_loss)}")
    print()

    # Print trade details
    if result.trades:
        print("Trade Details:")
        print("-" * 50)
        for i, trade in enumerate(result.trades, 1):
            print(f"Trade #{i}: {trade.symbol}")
            print(f"  Entry: {trade.entry_date.date()} at {format_currency(trade.entry_price)} ({trade.shares} shares)")
            print(f"  Exit:  {trade.exit_date.date()} at {format_currency(trade.exit_price)} ({trade.shares} shares)")
            print(f"  P&L:   {format_percentage(trade.pnl_pct)} ({format_currency(trade.pnl)})")
            print(f"  Duration: {trade.duration_days} days")
            print(f"  Reason: {trade.exit_reason}")
            print()

    # Print data quality warnings
    if result.data_warnings:
        print("Data Quality Warnings:")
        print("-" * 50)
        for warning in result.data_warnings:
            print(f"  - {warning}")
        print()

    print(f"Execution Time: {result.execution_time_seconds:.2f} seconds")
    print()
    print("Tip: Run with different symbols or date ranges to compare performance.")


if __name__ == "__main__":
    main()
