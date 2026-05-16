import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False


def prepare_lstm_data(df: pd.DataFrame, seq_length: int = 60) -> tuple:
    """
    Prepare data for LSTM model.

    Returns:
        Tuple of (X, y, scaler)
    """
    close = df['Close'].values.reshape(-1, 1)

    # Scale data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(close)

    # Create sequences
    X, y = [], []
    for i in range(seq_length, len(scaled)):
        X.append(scaled[i-seq_length:i])
        y.append(scaled[i][0])

    return np.array(X), np.array(y), scaler


def lstm_predict(df: pd.DataFrame, days_ahead: int = 7, seq_length: int = 60) -> tuple:
    """
    Predict using LSTM model.

    Returns:
        Tuple of (predictions, metrics)
    """
    if not TENSORFLOW_AVAILABLE:
        return None, None

    try:
        X, y, scaler = prepare_lstm_data(df, seq_length)

        if len(X) < 100:
            return None, None

        # Split data
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]

        # Build LSTM model
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(seq_length, 1)),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25, activation='relu'),
            Dense(1)
        ])

        model.compile(optimizer='adam', loss='mean_squared_error')

        # Train with early stopping
        early_stop = EarlyStopping(monitor='loss', patience=5, restore_best_weights=True)
        model.fit(
            X_train, y_train,
            epochs=30,
            batch_size=32,
            validation_split=0.1,
            callbacks=[early_stop],
            verbose=0
        )

        # Evaluate
        y_pred_scaled = model.predict(X_test, verbose=0)
        y_pred = scaler.inverse_transform(y_pred_scaled.reshape(-1, 1))
        y_test_real = scaler.inverse_transform(y_test.reshape(-1, 1))

        rmse = np.sqrt(np.mean((y_pred - y_test_real) ** 2))
        metrics = {'rmse': rmse[0][0]}

        # Predict future days
        predictions = []
        current_data = df.copy()

        for _ in range(days_ahead):
            X_future, _, _ = prepare_lstm_data(current_data, seq_length)
            pred_scaled = model.predict(X_future, verbose=0)[0][0]

            # Inverse transform
            pred = scaler.inverse_transform([[pred_scaled]])[0][0]
            predictions.append(pred)

            # Add to data
            new_row = pd.DataFrame([{
                'Open': pred,
                'High': pred * 1.02,
                'Low': pred * 0.98,
                'Close': pred,
                'Volume': current_data['Volume'].iloc[-1]
            }], index=[current_data.index[-1] + pd.Timedelta(days=1)])
            current_data = pd.concat([current_data, new_row])

        return np.array(predictions), metrics

    except Exception as e:
        return None, None
