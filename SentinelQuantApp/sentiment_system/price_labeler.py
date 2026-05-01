import pandas as pd
import yfinance as yf
from tqdm import tqdm

INPUT_FILE = "sentiment_system/data/feature_dataset.csv"
OUTPUT_FILE = "sentiment_system/data/training_dataset.csv"


def get_stock_prices(symbol):

    ticker = symbol + ".NS"

    data = yf.download(
        ticker,
        period="3y",
        progress=False
    )

    data.reset_index(inplace=True)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    return data[["Date", "Close"]]


def main():

    print("Loading feature dataset...")

    df = pd.read_csv(INPUT_FILE)

    df["date"] = pd.to_datetime(df["date"])

    symbols = df["symbol"].unique()

    price_data = {}

    print("Downloading stock price data...")

    for symbol in tqdm(symbols):

        prices = get_stock_prices(symbol)

        prices["Date"] = pd.to_datetime(prices["Date"])

        prices = prices.sort_values("Date")

        prices["return_1d"] = prices["Close"].pct_change(1)
        prices["return_3d"] = prices["Close"].pct_change(3)
        prices["return_7d"] = prices["Close"].pct_change(7)

        price_data[symbol] = prices

    rows = []

    print("Labeling price movements...")

    for _, row in tqdm(df.iterrows(), total=len(df)):

        symbol = row["symbol"]
        news_date = row["date"]

        prices = price_data[symbol]

        future_prices = prices[prices["Date"] >= news_date]

        if len(future_prices) < 2:
            continue

        today_row = future_prices.iloc[0]
        next_row = future_prices.iloc[1]

        today_price = float(today_row["Close"])
        next_price = float(next_row["Close"])

        ret = (next_price - today_price) / today_price

        # Stronger signal threshold
        if ret > 0.005:
            direction = "UP"
        elif ret < -0.005:
            direction = "DOWN"
        else:
            continue

        rows.append({
            "symbol": symbol,
            "date": news_date,
            "news_count": row["news_count"],
            "rolling_3_sentiment": row["rolling_3_sentiment"],
            "rolling_7_sentiment": row["rolling_7_sentiment"],
            "return_1d": today_row["return_1d"],
            "return_3d": today_row["return_3d"],
            "return_7d": today_row["return_7d"],
            "direction": direction
        })

    df_final = pd.DataFrame(rows)

    df_final = df_final.dropna()

    print("Final training dataset size:", len(df_final))

    df_final.to_csv(OUTPUT_FILE, index=False)

    print("Training dataset saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()