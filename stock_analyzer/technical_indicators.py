import pandas as pd
import numpy as np
import ta

def calculate_all_indicators(df: pd.DataFrame) -> dict:
    """
    Calculate various technical indicators.

    Args:
        df: DataFrame with OHLCV data

    Returns:
        Dictionary with all technical indicators
    """
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']

    # Momentum Indicators
    rsi = ta.momentum.rsi(close, window=14)

    # MACD
    macd = ta.trend.MACD(close)
    macd_line = macd.macd()
    macd_signal = macd.macd_signal()
    macd_hist = macd.macd_hist()

    # Moving Averages
    sma_20 = ta.trend.sma_indicator(close, window=20)
    sma_50 = ta.trend.sma_indicator(close, window=50)
    ema_20 = ta.trend.ema_indicator(close, window=20)
    ema_50 = ta.trend.ema_indicator(close, window=50)

    # Volatility
    bollinger = ta.volatility.bollinger_bands(close, window=20)
    bb_upper = bollinger.bollinger_hband()
    bb_middle = bollinger.bollinger_mavg()
    bb_lower = bollinger.bollinger_lband()

    # Volume indicators
    obv = ta.volume.on_balance_volume(high, low, volume)

    # Trend
    adx = ta.trend.average_directional_index(high, low, close, window=14)

    # Compile results
    indicators = {
        'RSI': rsi,
        'MACD': macd_line,
        'MACD_Signal': macd_signal,
        'MACD_Histogram': macd_hist,
        'SMA_20': sma_20,
        'SMA_50': sma_50,
        'EMA_20': ema_20,
        'EMA_50': ema_50,
        'BB_Upper': bb_upper,
        'BB_Middle': bb_middle,
        'BB_Lower': bb_lower,
        'OBV': obv,
        'ADX': adx
    }

    return indicators


def get_signal(indicators: dict, current_price: float) -> dict:
    """
    Generate trading signals based on technical indicators.

    Returns:
        Dictionary with signals for each indicator
    """
    signals = {}

    # RSI Signal
    rsi_val = indicators['RSI'].iloc[-1]
    if rsi_val < 30:
        signals['RSI'] = 'BUY'
    elif rsi_val > 70:
        signals['RSI'] = 'SELL'
    else:
        signals['RSI'] = 'HOLD'

    # MACD Signal
    macd = indicators['MACD'].iloc[-1]
    macd_sig = indicators['MACD_Signal'].iloc[-1]
    if macd > macd_sig:
        signals['MACD'] = 'BUY'
    else:
        signals['MACD'] = 'SELL'

    # Moving Average Signal
    if current_price > indicators['SMA_20'].iloc[-1]:
        signals['SMA_20'] = 'BUY'
    else:
        signals['SMA_20'] = 'SELL'

    if current_price > indicators['SMA_50'].iloc[-1]:
        signals['SMA_50'] = 'BUY'
    else:
        signals['SMA_50'] = 'SELL'

    # Bollinger Bands Signal
    if current_price < indicators['BB_Lower'].iloc[-1]:
        signals['Bollinger'] = 'BUY'
    elif current_price > indicators['BB_Upper'].iloc[-1]:
        signals['Bollinger'] = 'SELL'
    else:
        signals['Bollinger'] = 'HOLD'

    return signals
