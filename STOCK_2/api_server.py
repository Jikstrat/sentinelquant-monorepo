import os
from typing import Any

import pandas as pd
import requests
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from market_ranker import rank_market
from sentiment_system.predictor import predict_stock

STOCK_FILE = os.path.join("sentiment_system", "data", "nifty50_stocks.csv")

app = FastAPI(title="Sentiment API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SentimentRequest(BaseModel):
    symbol: str
    market: str = "US"


US_FALLBACK_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "NFLX", "AMD", "INTC"]
YF_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"
YF_HEADERS = {"User-Agent": "Mozilla/5.0"}


def normalize_market(value: str) -> str:
    return "INDIA" if value.strip().upper().startswith("IN") else "US"


def get_stock_chart(symbol: str, market: str) -> list[dict[str, Any]]:
    is_india = normalize_market(market) == "INDIA"
    ticker = symbol if (symbol.endswith(".NS") or not is_india) else f"{symbol}.NS"
    data = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if data.empty:
        return []

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    chart = data.reset_index()[["Date", "Close"]].copy()
    chart["Date"] = chart["Date"].astype(str)
    rows = chart.to_dict(orient="records")
    for row in rows:
        row["Close"] = float(row["Close"])
    return rows


def resolve_company(symbol: str, market: str) -> str | None:
    if normalize_market(market) == "INDIA":
        if not os.path.exists(STOCK_FILE):
            return None
        stocks = pd.read_csv(STOCK_FILE)
        row = stocks[stocks["symbol"].astype(str).str.upper() == symbol.upper()]
        if row.empty:
            return None
        return str(row.iloc[0]["company"])

    try:
        info = yf.Ticker(symbol).info
        return str(info.get("shortName") or info.get("longName") or symbol)
    except Exception:
        return symbol


@app.get("/api/sentiment/symbols")
def symbols(market: str = "US") -> dict[str, Any]:
    selected_market = normalize_market(market)
    if selected_market == "INDIA":
        if not os.path.exists(STOCK_FILE):
            return {"market": selected_market, "symbols": []}
        stocks = pd.read_csv(STOCK_FILE)
        return {"market": selected_market, "symbols": stocks["symbol"].astype(str).tolist()}
    return {"market": selected_market, "symbols": US_FALLBACK_SYMBOLS}


@app.get("/api/sentiment/symbol-search")
def symbol_search(market: str = "US", q: str = "") -> dict[str, Any]:
    selected_market = normalize_market(market)
    query = q.strip()

    if selected_market == "INDIA":
        if not os.path.exists(STOCK_FILE):
            return {"market": selected_market, "symbols": []}
        stocks = pd.read_csv(STOCK_FILE)
        if not query:
            return {"market": selected_market, "symbols": stocks["symbol"].astype(str).tolist()}
        mask = (
            stocks["symbol"].astype(str).str.contains(query, case=False, na=False)
            | stocks["company"].astype(str).str.contains(query, case=False, na=False)
        )
        return {"market": selected_market, "symbols": stocks.loc[mask, "symbol"].astype(str).tolist()}

    if not query:
        return {"market": selected_market, "symbols": US_FALLBACK_SYMBOLS}

    try:
        response = requests.get(
            YF_SEARCH_URL,
            params={
                "q": query,
                "lang": "en-US",
                "region": "US",
                "quotesCount": 25,
                "newsCount": 0,
            },
            headers=YF_HEADERS,
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        quotes = data.get("quotes", [])
        symbols = []
        for quote in quotes:
            symbol = quote.get("symbol")
            quote_type = quote.get("quoteType", "")
            if not symbol:
                continue
            if quote_type not in ("EQUITY", "ETF", "MUTUALFUND", ""):
                continue
            if "." in symbol:
                continue
            symbols.append(str(symbol).upper())
        deduped = list(dict.fromkeys(symbols))
        return {"market": selected_market, "symbols": deduped or US_FALLBACK_SYMBOLS}
    except Exception:
        return {"market": selected_market, "symbols": US_FALLBACK_SYMBOLS}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/sentiment/analyze")
def analyze_sentiment(payload: SentimentRequest) -> dict[str, Any]:
    symbol = payload.symbol.strip().upper()
    market = normalize_market(payload.market)
    company = resolve_company(symbol, market)
    if not company:
        raise HTTPException(status_code=400, detail="Unable to resolve company for this symbol.")

    result = predict_stock(symbol, company)
    if not result:
        raise HTTPException(status_code=404, detail="No recent market news available for this stock.")

    return {
        **result,
        "company": company,
        "market": market,
        "price_chart": get_stock_chart(symbol, market),
    }


@app.get("/api/sentiment/market-overview")
def market_overview() -> dict[str, Any]:
    bullish, bearish = rank_market()
    return {
        "bullish": bullish[["symbol", "up_prob"]].to_dict(orient="records") if not bullish.empty else [],
        "bearish": bearish[["symbol", "down_prob"]].to_dict(orient="records") if not bearish.empty else [],
    }
