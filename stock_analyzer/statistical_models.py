import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def arima_predict(df: pd.DataFrame, days_ahead: int = 7) -> tuple:
    """
    Predict future prices using ARIMA model.

    Args:
        df: DataFrame with historical data
        days_ahead: Number of days to predict

    Returns:
        Tuple of (predictions, confidence intervals)
    """
    close = df['Close']

    try:
        # Fit ARIMA model (5,1,0) is a good starting point
        model = ARIMA(close, order=(5, 1, 0))
        fitted = model.fit()

        # Forecast
        forecast = fitted.get_forecast(steps=days_ahead)
        predictions = forecast.predicted_mean
        ci = forecast.conf_int()

        return predictions, ci
    except Exception as e:
        return None, None


def exponential_smoothing_predict(df: pd.DataFrame, days_ahead: int = 7) -> tuple:
    """
    Predict using Exponential Smoothing (Holt-Winters).

    Returns:
        Tuple of (predictions, confidence intervals)
    """
    close = df['Close']

    try:
        # Fit Holt-Winters model
        model = ExponentialSmoothing(
            close,
            trend='add',
            seasonal=None,
            initialization_method='estimated'
        )
        fitted = model.fit()

        # Forecast
        forecast = fitted.get_forecast(steps=days_ahead)
        predictions = forecast.predicted_mean
        ci = forecast.conf_int()

        return predictions, ci
    except Exception as e:
        return None, None
