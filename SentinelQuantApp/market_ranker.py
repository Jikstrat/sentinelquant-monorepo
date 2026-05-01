import pandas as pd
import streamlit as st

from sentiment_system.predictor import predict_stock

STOCK_FILE = "sentiment_system/data/nifty50_stocks.csv"


@st.cache_data(ttl=600)
def rank_market():

    stocks = pd.read_csv(STOCK_FILE)

    results = []

    for _, row in stocks.iterrows():

        symbol = row["symbol"]
        company = row["company"]

        try:

            result = predict_stock(symbol, company)

            if result:
                results.append(result)

        except Exception as e:
            print("Prediction failed for:", symbol, e)

    if len(results) == 0:
        return pd.DataFrame(), pd.DataFrame()

    df = pd.DataFrame(results)

    bullish = df.sort_values("up_prob", ascending=False).head(5)
    bearish = df.sort_values("down_prob", ascending=False).head(5)

    return bullish, bearish