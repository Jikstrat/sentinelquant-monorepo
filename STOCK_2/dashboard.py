import os
import streamlit as st
import pandas as pd
import yfinance as yf

from market_ranker import rank_market
from sentiment_system.predictor import predict_stock

STOCK_FILE = "sentiment_system/data/nifty50_stocks.csv"

# ---------------------------------------------------------------------------
# Navigation URLs — set these env vars for production, defaults for local dev
# ---------------------------------------------------------------------------
LANDING_URL = os.environ.get("LANDING_URL", "http://localhost:5173")
QUANT_URL   = os.environ.get("QUANT_URL",   "http://localhost:8502")


def get_stock_chart(symbol):

    ticker = symbol + ".NS"

    data = yf.download(
        ticker,
        period="3mo",
        interval="1d",
        progress=False
    )

    if data.empty:
        return None

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()

    chart_data = data[["Date", "Close"]]

    chart_data = chart_data.set_index("Date")

    return chart_data


st.set_page_config(
    page_title="Market Sentiment Dashboard",
    layout="wide"
)

# ---------------------------------------------------------------------------
# Navbar
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

/* ── Global font override ── */
html, body, .stApp, [class*="css"] {{
    font-family: 'DM Sans', sans-serif !important;
}}

/* ── Hide Streamlit default header/hamburger ── */
[data-testid="stHeader"] {{ display: none !important; }}

/* ── Navbar ── */
.sq-nav {{
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
    height: 56px;
    background: rgba(10, 14, 20, 0.92);
    backdrop-filter: blur(14px);
    border-bottom: 1px solid #1C2B3A;
    box-sizing: border-box;
}}

/* ── Logo mark ── */
.sq-logo {{
    display: flex;
    align-items: center;
    gap: 9px;
    text-decoration: none;
    color: #E8EDF2;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: -0.3px;
}}
.sq-logo-icon {{
    width: 28px; height: 28px;
    border-radius: 6px;
    border: 1px solid rgba(59,158,255,0.3);
    background: rgba(59,158,255,0.08);
    display: flex; align-items: center; justify-content: center;
    position: relative;
    cursor: default;
}}
.sq-logo-icon svg {{
    width: 15px; height: 15px;
    stroke: #3B9EFF;
    fill: none;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
}}

/* ── Nav links ── */
.sq-nav-links {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.sq-btn {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    font-weight: 500;
    padding: 7px 16px;
    border-radius: 6px;
    text-decoration: none;
    transition: all 0.15s ease;
    cursor: pointer;
    white-space: nowrap;
}}
.sq-btn-ghost {{
    color: #8899AA;
    background: transparent;
    border: 1px solid transparent;
}}
.sq-btn-ghost:hover {{
    color: #E8EDF2;
    border-color: #1C2B3A;
    background: #0F1620;
}}
.sq-btn-primary {{
    color: #ffffff !important;
    background: #3B9EFF !important;
    border: 1px solid rgba(59,158,255,0.4);
    box-shadow: 0 2px 12px rgba(59,158,255,0.20);
}}
.sq-btn-primary:hover {{
    color: #ffffff !important;
    background: #2b8ef0 !important;
    box-shadow: 0 2px 18px rgba(59,158,255,0.30);
}}

/* ── Push page content below navbar ── */
.block-container {{
    padding-top: 72px !important;
}}
</style>

<nav class="sq-nav">
  <a class="sq-logo" href="{LANDING_URL}" target="_blank" rel="noopener noreferrer">
    <div class="sq-logo-icon" title="SentinelQuant — Market Signal Platform">
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <polyline points="2 18 8 10 13 14 19 6"/>
        <line x1="19" y1="6" x2="22" y2="6"/>
        <line x1="19" y1="6" x2="19" y2="9"/>
      </svg>
    </div>
    SentinelQuant
  </a>
  <div class="sq-nav-links">
    <a class="sq-btn sq-btn-ghost" href="{LANDING_URL}" target="_blank" rel="noopener noreferrer">
      ← Home
    </a>
    <a class="sq-btn sq-btn-primary" href="{QUANT_URL}" target="_blank" rel="noopener noreferrer">
      Quant Dashboard →
    </a>
  </div>
</nav>
""", unsafe_allow_html=True)

st.title("Market Sentiment Dashboard")

st.caption("News-driven market analysis for NIFTY 50 equities")

stocks = pd.read_csv(STOCK_FILE)

# ------------------------------
# STOCK ANALYSIS

st.subheader("Stock Analysis")

stock_symbols = stocks["symbol"].tolist()

selected_stock = st.selectbox("Select Stock", stock_symbols)

company = stocks[stocks["symbol"] == selected_stock]["company"].values[0]

if st.button("Analyze Stock"):

    with st.spinner("Analyzing latest market signals..."):
        result = predict_stock(selected_stock, company)

    if result:

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Market Outlook", result["prediction"])

        with col2:
            st.metric("Upside Probability", round(result["up_prob"], 3))

        with col3:
            st.metric("Downside Probability", round(result["down_prob"], 3))

        st.divider()

        st.subheader("Relevant Market Headlines")

        for headline in result["news"]:
            st.write("•", headline)

        st.divider()

        st.subheader("Price Trend (3 Months)")

        price_data = get_stock_chart(selected_stock)

        if price_data is not None:
            st.line_chart(price_data)
        else:
            st.warning("Price data unavailable.")

    else:
        st.warning("No recent market news available for this stock.")

st.divider()

# ------------------------------
# MARKET SENTIMENT

st.subheader("Market Sentiment Overview")

if st.button("Generate Market Overview"):

    with st.spinner("Scanning market sentiment..."):
        bullish, bearish = rank_market()

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("**Top Positive Sentiment Stocks**")

        if not bullish.empty:
            st.dataframe(bullish[["symbol", "up_prob"]])
        else:
            st.write("No strong positive sentiment detected.")

    with col2:

        st.markdown("**Top Negative Sentiment Stocks**")

        if not bearish.empty:
            st.dataframe(bearish[["symbol", "down_prob"]])
        else:
            st.write("No strong negative sentiment detected.")

st.divider()

# ------------------------------
# ------------------------------
# SYSTEM DETAILS

st.subheader("System Details")

st.write(
    "This system analyzes financial news sentiment and recent market momentum to estimate "
    "the short-term directional outlook for NIFTY 50 equities."
)

col1, col2 = st.columns(2)

with col1:

    st.markdown("**Prediction Pipeline**")

    st.write(
        "Financial news headlines are collected and analyzed using the **FinBERT** "
        "natural language model to extract sentiment signals. "
        "These signals are aggregated over multiple days and combined with "
        "recent price momentum indicators."
    )

    st.write(
        "The engineered features are then evaluated using a **Gradient Boosting "
        "machine learning model** trained to predict next-day price direction."
    )

with col2:

    st.markdown("**Model Performance**")

    st.write(
        "The model achieves approximately **56% directional accuracy** on unseen data."
    )

    st.write(
        "In financial prediction tasks, even small improvements above random chance "
        "(50%) are considered meaningful due to the inherently noisy nature of markets."
    )

st.caption(
    "Sentiment analysis powered by FinBERT (ProsusAI). Market data sourced from Yahoo Finance."
)