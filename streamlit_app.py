import streamlit as st
import pandas as pd
import yfinance as yf
from transformers import pipeline
from streamlit_lightweight_charts import renderLightweightCharts

# --- 1. SETTINGS & TITLE ---
st.set_page_config(page_title="AI Institutional Terminal", layout="wide", initial_sidebar_state="collapsed")
st.title("🏛️ AI Market Intelligence & Institutional Flow")

# Asset Selection
symbol = st.sidebar.selectbox("Select Market", ["EURUSD=X", "GC=F", "^GSPC", "BTC-USD"], index=1)
period = "60d"
interval = "1d"

# --- 2. THE AI BRAIN (Sentiment & Catalysts) ---
@st.cache_resource
def load_ai():
    # FinBERT is specifically trained for financial news sentiment
    return pipeline("sentiment-analysis", model="ProsusAI/finbert")

ai_analyzer = load_ai()

def get_sentiment():
    # In a real app, use a News API. Here are simulated real-time catalysts:
    catalysts = [
        "Fed signals neutral stance on interest rates for Q1",
        "Geopolitical tensions in the Middle East drive gold demand",
        "Institutional buy orders detected at major support levels"
    ]
    scores = [ai_analyzer(c)[0] for c in catalysts]
    return catalysts, scores

# --- 3. DATA & ORDER BLOCK LOGIC ---
data = yf.download(symbol, period=period, interval=interval)
data.reset_index(inplace=True)

def detect_order_blocks(df):
    # Detects zones where high volume preceded a massive move
    avg_vol = df['Volume'].rolling(window=20).mean()
    df['OB'] = (df['Volume'] > avg_vol * 1.5) & (df['Close'].diff().abs() > df['Close'].std())
    return df[df['OB'] == True]

ob_zones = detect_order_blocks(data)

# --- 4. THE DASHBOARD UI ---
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("📊 Real-Time Trajectory")
    
    # Format data for TradingView Lightweight Charts
    chart_data = data[['Date', 'Open', 'High', 'Low', 'Close']].copy()
    chart_data.columns = ['time', 'open', 'high', 'low', 'close']
    chart_data['time'] = chart_data['time'].astype(str)
    
    chart_options = {
        "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"color": "#2B2B43"}, "horzLines": {"color": "#2B2B43"}},
        "priceScale": {"borderColor": "#485c7b"},
        "timeScale": {"borderColor": "#485c7b"}
    }
    
    renderLightweightCharts([{"type": "Candlestick", "data": chart_data.to_dict('records')}], chart_options)

with col2:
    st.subheader("🔥 AI Barometer")
    news, scores = get_sentiment()
    
    # Sentiment Meter
    bullish_count = sum(1 for s in scores if s['label'] == 'positive')
    if bullish_count >= 2:
        st.success("STANCE: BULLISH (Buy Blocks Strong)")
    elif bullish_count == 0:
        st.error("STANCE: BEARISH (Sell Blocks Heavy)")
    else:
        st.warning("STANCE: NEUTRAL (No Action)")

    st.write("---")
    st.write("**Latest Catalysts:**")
    for n in news:
        st.caption(f"• {n}")

# --- 5. INSTITUTIONAL ORDER BLOCKS TABLE ---
st.write("### 🏦 Institutional Activity detected")
if not ob_zones.empty:
    st.dataframe(ob_zones[['Date', 'Close', 'Volume']].tail(5))
else:
    st.write("No major institutional footprint in the last 24 hours.")
