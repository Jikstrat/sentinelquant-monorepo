import base64
import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import requests
import yfinance as yf
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from market_ranker import rank_market
from sentiment_system.predictor import predict_stock

STOCK_FILE = os.path.join("sentiment_system", "data", "nifty50_stocks.csv")
AUTH_DB_PATH = os.path.join(os.path.dirname(__file__), "sentinelquant_local.db")
SESSION_TTL_HOURS = 24 * 30

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


class SignupRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=160)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=160)
    password: str = Field(min_length=6, max_length=128)


def get_db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db() -> None:
    conn = get_db_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                revoked_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash)")
        conn.commit()
    finally:
        conn.close()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str, salt_b64: str) -> str:
    salt = base64.b64decode(salt_b64.encode("utf-8"))
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return base64.b64encode(digest).decode("utf-8")


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_session(user_id: int) -> str:
    raw_token = secrets.token_urlsafe(48)
    token_digest = hash_token(raw_token)
    created_at = now_utc()
    expires_at = created_at + timedelta(hours=SESSION_TTL_HOURS)
    conn = get_db_conn()
    try:
        conn.execute(
            "INSERT INTO sessions (user_id, token_hash, expires_at, created_at, revoked_at) VALUES (?, ?, ?, ?, NULL)",
            (user_id, token_digest, expires_at.isoformat(), created_at.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    return raw_token


def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization token.")
    raw_token = authorization.split(" ", 1)[1].strip()
    if not raw_token:
        raise HTTPException(status_code=401, detail="Missing or invalid authorization token.")

    token_digest = hash_token(raw_token)
    conn = get_db_conn()
    try:
        row = conn.execute(
            """
            SELECT u.id, u.name, u.email, s.expires_at, s.revoked_at
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ?
            """,
            (token_digest,),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Session not found.")
    if row["revoked_at"] is not None:
        raise HTTPException(status_code=401, detail="Session has been logged out.")
    if datetime.fromisoformat(row["expires_at"]) < now_utc():
        raise HTTPException(status_code=401, detail="Session expired.")

    return {"id": row["id"], "name": row["name"], "email": row["email"]}


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
def symbols(market: str = "US", _: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    selected_market = normalize_market(market)
    if selected_market == "INDIA":
        if not os.path.exists(STOCK_FILE):
            return {"market": selected_market, "symbols": []}
        stocks = pd.read_csv(STOCK_FILE)
        return {"market": selected_market, "symbols": stocks["symbol"].astype(str).tolist()}
    return {"market": selected_market, "symbols": US_FALLBACK_SYMBOLS}


@app.get("/api/sentiment/symbol-search")
def symbol_search(market: str = "US", q: str = "", _: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
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
def analyze_sentiment(payload: SentimentRequest, _: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
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
def market_overview(_: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    bullish, bearish = rank_market()
    return {
        "bullish": bullish[["symbol", "up_prob"]].to_dict(orient="records") if not bullish.empty else [],
        "bearish": bearish[["symbol", "down_prob"]].to_dict(orient="records") if not bearish.empty else [],
    }


@app.on_event("startup")
def on_startup() -> None:
    init_auth_db()


@app.post("/api/auth/signup")
def signup(payload: SignupRequest) -> dict[str, Any]:
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    salt_b64 = base64.b64encode(os.urandom(16)).decode("utf-8")
    password_hash = hash_password(payload.password, salt_b64)
    created_at = now_utc().isoformat()

    conn = get_db_conn()
    try:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?)",
            (payload.name.strip(), email, password_hash, salt_b64, created_at),
        )
        user_id = int(cursor.lastrowid)
        conn.commit()
    finally:
        conn.close()

    token = create_session(user_id)
    return {"token": token, "user": {"id": user_id, "name": payload.name.strip(), "email": email}}


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    conn = get_db_conn()
    try:
        row = conn.execute(
            "SELECT id, name, email, password_hash, salt FROM users WHERE email = ?",
            (email,),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if hash_password(payload.password, row["salt"]) != row["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_session(int(row["id"]))
    return {
        "token": token,
        "user": {"id": int(row["id"]), "name": row["name"], "email": row["email"]},
    }


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None)) -> dict[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization token.")
    raw_token = authorization.split(" ", 1)[1].strip()
    if not raw_token:
        raise HTTPException(status_code=401, detail="Missing or invalid authorization token.")

    token_digest = hash_token(raw_token)
    conn = get_db_conn()
    try:
        row = conn.execute("SELECT id FROM sessions WHERE token_hash = ?", (token_digest,)).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Session not found.")
        conn.execute("UPDATE sessions SET revoked_at = ? WHERE id = ?", (now_utc().isoformat(), int(row["id"])))
        conn.commit()
    finally:
        conn.close()
    return {"message": "Logged out"}


@app.get("/api/auth/me")
def me(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {"user": user}
