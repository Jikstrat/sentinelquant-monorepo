import pandas as pd

INPUT_FILE = "sentiment_system/data/sentiment_news.csv"
OUTPUT_FILE = "sentiment_system/data/feature_dataset.csv"


def main():

    print("Loading sentiment dataset...")

    df = pd.read_csv(INPUT_FILE)

    df["date"] = pd.to_datetime(df["date"])

    sentiment_map = {
        "positive": 1,
        "neutral": 0,
        "negative": -1
    }

    df["sentiment_numeric"] = df["sentiment_label"].map(sentiment_map)

    print("Aggregating sentiment by day...")

    daily = df.groupby(["symbol", "date"]).agg(

        sentiment_mean=("sentiment_numeric", "mean"),
        sentiment_std=("sentiment_numeric", "std"),
        positive_ratio=("sentiment_numeric", lambda x: (x == 1).mean()),
        negative_ratio=("sentiment_numeric", lambda x: (x == -1).mean()),
        news_count=("headline", "count")

    ).reset_index()

    print("Generating rolling sentiment features...")

    daily = daily.sort_values(["symbol", "date"])

    daily["rolling_3_sentiment"] = (
        daily.groupby("symbol")["sentiment_mean"]
        .rolling(3)
        .mean()
        .reset_index(level=0, drop=True)
    )

    daily["rolling_7_sentiment"] = (
        daily.groupby("symbol")["sentiment_mean"]
        .rolling(7)
        .mean()
        .reset_index(level=0, drop=True)
    )

    daily = daily.dropna()

    print("Final dataset size:", len(daily))

    daily.to_csv(OUTPUT_FILE, index=False)

    print("Feature dataset saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()