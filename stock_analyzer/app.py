import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import get_stock_data, get_info
from technical_indicators import calculate_all_indicators, get_signal
from statistical_models import arima_predict, exponential_smoothing_predict
from ml_models import random_forest_predict, gradient_boosting_predict
from lstm_model import lstm_predict

# Page config
st.set_page_config(
    page_title="Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {font-size: 2rem; font-weight: bold; color: #1f77b4;}
    .sub-header {font-size: 1.2rem; font-weight: bold; margin-top: 1rem;}
    .buy {color: #2ecc71; font-weight: bold;}
    .sell {color: #e74c3c; font-weight: bold;}
    .hold {color: #f39c12; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">📈 Stock Analysis Dashboard</p>', unsafe_allow_html=True)

# Sidebar
st.sidebar.header("Settings")
ticker = st.sidebar.text_input("Ticker Symbol", value="AAPL").upper()
period = st.sidebar.selectbox("Time Period", ['1mo', '3mo', '6mo', '1y', '2y', '5y'], index=3)
days_ahead = st.sidebar.slider("Days Ahead", 1, 30, 7)

# Analysis options
st.sidebar.subheader("Analysis Models")
use_technical = st.sidebar.checkbox("Technical Indicators", value=True)
use_arima = st.sidebar.checkbox("ARIMA", value=True)
use_rf = st.sidebar.checkbox("Random Forest", value=True)
use_gb = st.sidebar.checkbox("Gradient Boosting", value=False)
use_lstm = st.sidebar.checkbox("LSTM", value=False)

# Main analysis button
if st.sidebar.button("🚀 Analyze"):
    with st.spinner(f"Analyzing {ticker}..."):
        try:
            # Fetch data
            df = get_stock_data(ticker, period)
            info = get_info(ticker)

            # Display company info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", f"${df['Close'].iloc[-1]:.2f}",
                         f"${df['Close'].iloc[-1] - df['Close'].iloc[-2]:+.2f}")
            with col2:
                st.metric("Change %", f"{df['Close'].pct_change().iloc[-1]*100:.2f}%")
            with col3:
                st.metric("Volume", f"{df['Volume'].iloc[-1]:,}")

            # Price chart
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               vertical_spacing=0.05, row_heights=[0.7, 0.3])

            fig.add_trace(go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name='Price'), row=1, col=1)

            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume'), row=2, col=1)

            fig.update_layout(title=f'{ticker} Price & Volume', height=600,
                            xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # Technical Indicators
            if use_technical:
                st.subheader("📊 Technical Indicators")
                indicators = calculate_all_indicators(df)
                signals = get_signal(indicators, df['Close'].iloc[-1])

                # Display current values
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    rsi_val = indicators['RSI'].iloc[-1]
                    st.metric("RSI (14)", f"{rsi_val:.2f}", signals['RSI'])
                with col2:
                    macd_val = indicators['MACD'].iloc[-1]
                    st.metric("MACD", f"{macd_val:.4f}", signals['MACD'])
                with col3:
                    sma_20 = indicators['SMA_20'].iloc[-1]
                    st.metric("SMA 20", f"${sma_20:.2f}", signals['SMA_20'])
                with col4:
                    sma_50 = indicators['SMA_50'].iloc[-1]
                    st.metric("SMA 50", f"${sma_50:.2f}", signals['SMA_50'])

                # Plot indicators
                fig_ind = make_subplots(rows=3, cols=1, shared_xaxes=True,
                                       vertical_spacing=0.05, row_heights=[0.35, 0.35, 0.3])

                # Price with moving averages
                fig_ind.add_trace(go.Line(x=df.index, y=df['Close'], name='Close'), row=1, col=1)
                fig_ind.add_trace(go.Line(x=df.index, y=indicators['SMA_20'], name='SMA 20'), row=1, col=1)
                fig_ind.add_trace(go.Line(x=df.index, y=indicators['SMA_50'], name='SMA 50'), row=1, col=1)

                # RSI
                fig_ind.add_trace(go.Line(x=df.index, y=indicators['RSI'], name='RSI', line=dict(color='orange')), row=2, col=1)
                fig_ind.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig_ind.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

                # MACD
                fig_ind.add_trace(go.Line(x=df.index, y=indicators['MACD'], name='MACD'), row=3, col=1)
                fig_ind.add_trace(go.Line(x=df.index, y=indicators['MACD_Signal'], name='Signal'), row=3, col=1)
                fig_ind.add_trace(go.Bar(x=df.index, y=indicators['MACD_Histogram'], name='Hist'), row=3, col=1)

                fig_ind.update_layout(title='Technical Indicators', height=600)
                st.plotly_chart(fig_ind, use_container_width=True)

                # Overall signal
                buy_count = sum(1 for s in signals.values() if s == 'BUY')
                sell_count = sum(1 for s in signals.values() if s == 'SELL')
                if buy_count > sell_count:
                    overall = "BUY"
                    color = "#2ecc71"
                elif sell_count > buy_count:
                    overall = "SELL"
                    color = "#e74c3c"
                else:
                    overall = "HOLD"
                    color = "#f39c12"

                st.markdown(f"**Overall Signal: <span style='color:{color};font-weight:bold;'>{overall}</span>**",
                           unsafe_allow_html=True)

            # Predictions comparison
            st.subheader("🔮 Predictions Comparison")

            predictions_df = pd.DataFrame()
            current_price = df['Close'].iloc[-1]

            # ARIMA
            if use_arima:
                pred, ci = arima_predict(df, days_ahead)
                if pred is not None:
                    predictions_df['ARIMA'] = pred
                    st.success(f"✓ ARIMA model completed")

            # Random Forest
            if use_rf:
                pred, metrics = random_forest_predict(df, days_ahead)
                if pred is not None:
                    predictions_df['Random Forest'] = pred
                    st.success(f"✓ Random Forest completed (RMSE: {metrics['rmse']:.2f})")

            # Gradient Boosting
            if use_gb:
                pred, metrics = gradient_boosting_predict(df, days_ahead)
                if pred is not None:
                    predictions_df['Gradient Boosting'] = pred
                    st.success(f"✓ Gradient Boosting completed (RMSE: {metrics['rmse']:.2f})")

            # LSTM
            if use_lstm:
                pred, metrics = lstm_predict(df, days_ahead)
                if pred is not None:
                    predictions_df['LSTM'] = pred
                    st.success(f"✓ LSTM completed (RMSE: {metrics['rmse']:.2f})")

            # Plot predictions
            if not predictions_df.empty:
                fig_pred = go.Figure()

                # Historical data
                fig_pred.add_trace(go.Line(x=df.index, y=df['Close'],
                                          name='Historical', line=dict(width=2)))

                # Future predictions
                future_dates = pd.date_range(start=df.index[-1] + pd.Timedelta(days=1),
                                            periods=days_ahead, freq='D')

                for model in predictions_df.columns:
                    fig_pred.add_trace(go.Line(x=future_dates, y=predictions_df[model],
                                              name=model, mode='lines+markers',
                                              line=dict(dash='dot')))

                fig_pred.update_layout(
                    title=f'{ticker} - {days_ahead} Day Predictions',
                    height=500,
                    xaxis_title='Date',
                    yaxis_title='Price'
                )
                st.plotly_chart(fig_pred, use_container_width=True)

                # Prediction summary table
                st.markdown("### Prediction Summary")
                summary_data = []
                for model in predictions_df.columns:
                    pred_price = predictions_df[model].iloc[-1]
                    change = ((pred_price - current_price) / current_price) * 100
                    summary_data.append({
                        'Model': model,
                        f'Day {days_ahead} Price': f"${pred_price:.2f}",
                        'Change': f"{change:+.2f}%"
                    })

                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True)

        except Exception as e:
            st.error(f"Error: {str(e)}")
else:
    st.info("👈 Enter a ticker symbol and click 'Analyze' to get started!")

# Footer
st.markdown("---")
st.caption("⚠️ This tool is for educational purposes only. Not financial advice.")
