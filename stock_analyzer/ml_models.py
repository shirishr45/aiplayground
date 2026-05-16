import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

def prepare_features(df: pd.DataFrame) -> tuple:
    """
    Prepare features for ML models.

    Returns:
        Tuple of (X_features, y_target, feature_names)
    """
    df = df.copy()

    # Create lag features
    for lag in [1, 2, 3, 5, 10]:
        df[f'close_lag_{lag}'] = df['Close'].shift(lag)

    # Moving averages as features
    df['sma_5'] = df['Close'].rolling(window=5).mean()
    df['sma_10'] = df['Close'].rolling(window=10).mean()
    df['sma_20'] = df['Close'].rolling(window=20).mean()

    # Volatility features
    df['volatility_5'] = df['Close'].rolling(window=5).std()
    df['volatility_10'] = df['Close'].rolling(window=10).std()

    # Price changes
    df['return_1d'] = df['Close'].pct_change()
    df['return_5d'] = df['Close'].pct_change(5)

    # Volume features
    df['volume_ma_5'] = df['Volume'].rolling(window=5).mean()
    df['volume_change'] = df['Volume'].pct_change()

    # Drop NaN
    df = df.dropna()

    # Features and target
    feature_cols = [col for col in df.columns if col not in ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']]
    X = df[feature_cols]
    y = df['Close'].shift(-1)  # Predict next day's close

    # Align X and y
    X = X.iloc[:-1]
    y = y.iloc[:-1]
    y.index = X.index

    return X, y, feature_cols


def random_forest_predict(df: pd.DataFrame, days_ahead: int = 7) -> tuple:
    """
    Predict using Random Forest.

    Returns:
        Tuple of (predictions, metrics)
    """
    X, y, features = prepare_features(df)

    if len(X) < 50:
        return None, None

    # Split data
    train_size = int(len(X) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    metrics = {
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
        'r2': r2_score(y_test, y_pred)
    }

    # Predict future days iteratively
    predictions = []
    current_data = df.copy()

    for _ in range(days_ahead):
        # Prepare last row as features
        last_row = prepare_features(current_data)[0].iloc[-1:].values
        pred = model.predict(last_row)[0]
        predictions.append(pred)

        # Add prediction to data for next iteration
        new_row = pd.DataFrame([{
            'Open': pred,
            'High': pred * 1.02,
            'Low': pred * 0.98,
            'Close': pred,
            'Volume': current_data['Volume'].iloc[-1]
        }], index=[current_data.index[-1] + pd.Timedelta(days=1)])
        current_data = pd.concat([current_data, new_row])

    return np.array(predictions), metrics


def gradient_boosting_predict(df: pd.DataFrame, days_ahead: int = 7) -> tuple:
    """
    Predict using Gradient Boosting.

    Returns:
        Tuple of (predictions, metrics)
    """
    X, y, features = prepare_features(df)

    if len(X) < 50:
        return None, None

    # Split data
    train_size = int(len(X) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]

    # Train model
    model = GradientBoostingRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    metrics = {
        'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
        'r2': r2_score(y_test, y_pred)
    }

    # Predict future
    predictions = []
    current_data = df.copy()

    for _ in range(days_ahead):
        last_row = prepare_features(current_data)[0].iloc[-1:].values
        pred = model.predict(last_row)[0]
        predictions.append(pred)

        new_row = pd.DataFrame([{
            'Open': pred,
            'High': pred * 1.02,
            'Low': pred * 0.98,
            'Close': pred,
            'Volume': current_data['Volume'].iloc[-1]
        }], index=[current_data.index[-1] + pd.Timedelta(days=1)])
        current_data = pd.concat([current_data, new_row])

    return np.array(predictions), metrics
