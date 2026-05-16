import yfinance as yf
import pandas as pd

def get_stock_data(ticker: str, period: str = '2y') -> pd.DataFrame:
    """
    Fetch historical stock data from Yahoo Finance.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        period: Time period (1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

    Returns:
        DataFrame with OHLCV data
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty:
            raise ValueError(f"No data found for ticker: {ticker}")

        return df
    except Exception as e:
        raise Exception(f"Error fetching data for {ticker}: {str(e)}")


def get_info(ticker: str) -> dict:
    """Get company information."""
    try:
        stock = yf.Ticker(ticker)
        return stock.info
    except Exception as e:
        return {"error": str(e)}
