import feedparser
import pandas as pd
import re
from tqdm import tqdm

STOCK_FILE = "sentiment_system/data/nifty50_stocks.csv"
OUTPUT_FILE = "sentiment_system/data/raw_news.csv"


def clean_text(text):

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^A-Za-z0-9 ]+", "", text)

    return text.lower().strip()


def fetch_news(company):

    queries = [
        f"{company} stock",
        f"{company} earnings",
        f"{company} results",
        f"{company} share price",
        f"{company} revenue",
        f"{company} market"
    ]

    articles = []

    for query in queries:

        query = query.replace(" ", "+")

        url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

        feed = feedparser.parse(url)

        for entry in feed.entries:

            headline = entry.title
            clean_headline = clean_text(headline)

            if len(clean_headline.split()) < 5:
                continue

            link = entry.link
            source = entry.source.title if "source" in entry else "Unknown"
            date = entry.published if "published" in entry else None

            articles.append({
                "headline": headline,
                "clean_headline": clean_headline,
                "date": date,
                "source": source,
                "link": link
            })

    return articles


def main():

    stocks = pd.read_csv(STOCK_FILE)

    all_articles = []

    for _, row in tqdm(stocks.iterrows(), total=len(stocks)):

        symbol = row["symbol"]
        company = row["company"]

        print(f"\nFetching news for {company}")

        articles = fetch_news(company)

        for article in articles:

            article["symbol"] = symbol
            article["company"] = company

            all_articles.append(article)

    df = pd.DataFrame(all_articles)

    df.drop_duplicates(subset=["clean_headline"], inplace=True)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nDataset saved to:", OUTPUT_FILE)
    print("Total rows:", len(df))


if __name__ == "__main__":
    main()