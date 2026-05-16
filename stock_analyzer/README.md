# Stock Analysis Dashboard

A multi-model stock analysis application with technical indicators and predictive modeling.

## Features

- **Technical Indicators**: RSI, MACD, Moving Averages, Bollinger Bands
- **Statistical Models**: ARIMA, Exponential Smoothing
- **Machine Learning**: Random Forest, Gradient Boosting
- **Deep Learning**: LSTM Neural Networks
- **Interactive Visualizations**: Price charts, indicator plots, prediction comparisons

## Setup

### 1. Create Virtual Environment
```bash
cd stock_analyzer
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
streamlit run app.py
```

## Usage

1. Enter a ticker symbol (e.g., AAPL, TSLA, GOOGL)
2. Select time period and days ahead
3. Choose which models to run
4. Click "Analyze"

## Models Explained

| Model | Description | Speed |
|-------|-------------|-------|
| Technical Indicators | RSI, MACD, Moving Averages | ⚡ Fast |
| ARIMA | Statistical time series | ⚡ Fast |
| Random Forest | Ensemble ML model | 🐌 Medium |
| Gradient Boosting | Boosted decision trees | 🐌🐌 Slow |
| LSTM | Deep learning sequence model | 🐌🐌🐌 Slowest |

## Notes

- First LSTM run downloads model weights (takes time)
- Use 2y+ data for better ML model accuracy
- TensorFlow required for LSTM (heavy dependency)

## Disclaimer

This tool is for **educational purposes only**. Not financial advice.
