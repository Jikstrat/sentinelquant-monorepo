import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sentiment_system.predictor import predict_stock

STOCK_FILE = "sentiment_system/data/nifty50_stocks.csv"

_CACHE_TTL = timedelta(seconds=600)

_cached_at: Optional[datetime] = None
_cached_result: Optional[Tuple[pd.DataFrame, pd.DataFrame]] = None


def rank_market():

    global _cached_at, _cached_result

    now = datetime.now(timezone.utc)
    if (
        _cached_result is not None
        and _cached_at is not None
        and now - _cached_at < _CACHE_TTL
    ):
        return _cached_result

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

    _cached_at = now
    _cached_result = (bullish, bearish)
    return bullish, bearish