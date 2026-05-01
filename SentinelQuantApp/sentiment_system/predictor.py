import joblib
import feedparser
import re
import streamlit as st
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_PATH = "models/random_forest_model.pkl"


# -------------------------
# LOAD MODELS (CACHED)
# -------------------------

@st.cache_resource
def load_models():

    model = joblib.load(MODEL_PATH)

    tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")

    sentiment_model = AutoModelForSequenceClassification.from_pretrained(
        "ProsusAI/finbert"
    )

    sentiment_model.eval()

    return model, tokenizer, sentiment_model


model, tokenizer, sentiment_model = load_models()


# -------------------------
# TEXT CLEANING
# -------------------------

def clean_text(text):

    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^A-Za-z0-9 ]+", "", text)

    return text.lower().strip()


# -------------------------
# FETCH NEWS
# -------------------------

def fetch_latest_news(company, symbol):

    query = company.replace(" ", "+") + "+stock+market"

    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

    feed = feedparser.parse(url)

    headlines = []

    finance_keywords = [
        "stock",
        "share",
        "shares",
        "earnings",
        "profit",
        "revenue",
        "results",
        "quarter",
        "market",
        "deal",
        "contract",
        "order",
        "investment",
        "price target"
    ]

    sports_words = [
        "transfer",
        "goal",
        "striker",
        "football",
        "palace",
        "wolves",
        "leeds",
        "premier league"
    ]

    for entry in feed.entries:

        headline = entry.title
        text = headline.lower()

        # remove sports noise
        if any(word in text for word in sports_words):
            continue

        # must contain financial context
        if not any(word in text for word in finance_keywords):
            continue

        # must reference company
        if company.lower() not in text and symbol.lower() not in text:
            continue

        headlines.append(headline)

        if len(headlines) >= 20:
            break

    return headlines


# -------------------------
# SENTIMENT ANALYSIS
# -------------------------

def analyze_sentiment(headlines):

    scores = []

    for headline in headlines:

        inputs = tokenizer(
            headline,
            return_tensors="pt",
            truncation=True,
            padding=True
        )

        with torch.no_grad():

            outputs = sentiment_model(**inputs)

            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

        negative = probs[0][0].item()
        positive = probs[0][2].item()

        sentiment_score = positive - negative

        scores.append(sentiment_score)

    if len(scores) == 0:
        return None

    scores = np.array(scores)

    sentiment_mean = scores.mean()

    news_count = len(scores)

    # rolling approximations
    rolling_3 = sentiment_mean
    rolling_7 = sentiment_mean

    # IMPORTANT: Must match training features
    features = [[
        news_count,
        rolling_3,
        rolling_7,
        0,
        0,
        0
    ]]

    return features


# -------------------------
# PREDICTION
# -------------------------

def predict_stock(symbol, company):

    headlines = fetch_latest_news(company, symbol)

    if len(headlines) == 0:
        return None

    features = analyze_sentiment(headlines)

    if features is None:
        return None

    probabilities = model.predict_proba(features)[0]

    up_prob = probabilities[1]
    down_prob = probabilities[0]

    total = up_prob + down_prob

    if total > 0:
        up_prob = up_prob / total
        down_prob = down_prob / total

    prediction = "UP" if up_prob > down_prob else "DOWN"

    return {
        "symbol": symbol,
        "prediction": prediction,
        "up_prob": round(up_prob, 3),
        "down_prob": round(down_prob, 3),
        "news": headlines[:10]
    }