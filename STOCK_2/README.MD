# 📈 NSE Market Sentiment Dashboard

### Financial News Sentiment + Machine Learning Prediction System

---

# 1. Project Overview

This project implements a **complete end-to-end machine learning pipeline** that predicts the **next-day price direction (UP/DOWN)** for stocks in the **NIFTY 50 index** using **financial news sentiment and market momentum features**.

Rather than attempting to predict exact prices (which is extremely difficult due to market noise), the system predicts the **probability of directional movement**.

The system integrates:

```
Financial News Scraping
↓
Financial NLP (FinBERT)
↓
Feature Engineering
↓
Momentum Indicators
↓
Machine Learning Prediction
↓
Interactive Dashboard
```

The final system is deployed as a **Streamlit dashboard** that allows users to analyze **individual stocks and overall market sentiment**.

---

# 2. Motivation

Financial markets react strongly to information released through news and corporate announcements.

Examples include:

* Earnings reports
* Corporate investments
* Government policy changes
* Mergers and acquisitions
* Analyst upgrades/downgrades
* Macroeconomic developments

Markets respond not just to events, but to **the sentiment and tone of the information**.

Example:

```
"Tata Motors reports record EV sales growth"
```

This likely produces **positive investor sentiment**, increasing buying pressure.

Therefore this project models **news sentiment momentum combined with price momentum** to estimate short-term stock direction.

---

# 3. System Architecture

The project is structured as a **multi-stage machine learning pipeline**.

```
Google News RSS
        │
        ▼
news_scraper.py
        │
        ▼
sentiment_model.py
(FinBERT sentiment)
        │
        ▼
feature_engineer.py
(sentiment aggregation)
        │
        ▼
price_labeler.py
(momentum features + labels)
        │
        ▼
train_model.py
(Gradient Boosting model)
        │
        ▼
Saved Model
random_forest_model.pkl
        │
        ▼
predictor.py
(real-time inference)
        │
        ▼
market_ranker.py
(market-wide ranking)
        │
        ▼
dashboard.py
(Streamlit interface)
```

---

# 4. Project Structure

```
stock_ai_project
│
├ sentiment_system
│   ├ news_scraper.py
│   ├ sentiment_model.py
│   ├ feature_engineer.py
│   ├ price_labeler.py
│   ├ train_model.py
│   └ predictor.py
│
├ models
│   └ random_forest_model.pkl
│
├ market_ranker.py
├ dashboard.py
└ README.md
```

---

# 5. Data Source – Financial News

File:

```
news_scraper.py
```

The system collects financial headlines for NIFTY 50 companies using:

```
Google News RSS
```

Advantages:

* Aggregates multiple financial news sources
* Consistent RSS structure
* High coverage of Indian markets
* Reliable and easy to parse

Each news entry stores:

```
headline
date
company
symbol
source
link
```

This forms the **raw financial news dataset**.

---

# 6. Financial Sentiment Analysis (FinBERT)

File:

```
sentiment_model.py
```

The system uses **FinBERT**, a transformer model trained specifically on financial text.

FinBERT understands financial language such as:

* earnings
* losses
* forecasts
* guidance revisions
* market expectations

Example:

```
Headline:
"Infosys narrows losses in European market"

Generic NLP sentiment → negative  
Financial interpretation → positive
```

FinBERT correctly interprets such financial contexts.

---

### Sentiment Output

Each headline generates:

```
sentiment_label
positive / neutral / negative

sentiment_score
confidence probability
```

Example:

```
Headline:
Reliance invests in renewable energy expansion

Sentiment: Positive
Score: 0.82
```

---

# 7. Feature Engineering

File:

```
feature_engineer.py
```

Raw news sentiment is extremely noisy.

To capture **market reaction dynamics**, several engineered features are created.

---

## Sentiment Features

### Rolling Sentiment Momentum

```
rolling_3_sentiment
rolling_7_sentiment
```

These capture **multi-day sentiment trends**.

Example:

```
1 positive headline → weak signal
5 positive headlines → stronger signal
```

Markets react to **accumulated information**, not isolated news.

---

### News Volume

```
news_count
```

Higher news coverage often indicates:

* increased market attention
* higher volatility
* stronger reactions

---

# 8. Momentum Features

File:

```
price_labeler.py
```

Financial markets are highly momentum-driven.

To capture this behavior the system adds **price momentum features**.

### Momentum Indicators

```
return_1d
return_3d
return_7d
```

These measure recent price movements before the news event.

Example:

```
Strong uptrend + positive news → stronger continuation probability
```

Combining **sentiment + momentum** improves predictive performance.

---

# 9. Label Generation

Each training observation is labeled based on **next-day price movement**.

Price data is obtained using:

```
Yahoo Finance API (yfinance)
```

Return calculation:

```
(next_day_close − today_close) / today_close
```

Label rules:

```
UP   → positive return
DOWN → negative return
```

Small price fluctuations are filtered to remove noise.

---

# 10. Final Training Dataset

The supervised dataset contains:

```
news_count
rolling_3_sentiment
rolling_7_sentiment
return_1d
return_3d
return_7d
↓
direction (UP/DOWN)
```

This forms a **binary classification problem**.

---

# 11. Machine Learning Model

File:

```
train_model.py
```

The project uses a:

```
Gradient Boosting Classifier
```

Gradient Boosting builds an ensemble of sequential decision trees where each tree improves the previous model's errors.

---

# 12. Why Gradient Boosting?

Gradient Boosting is well suited for financial tabular datasets.

Advantages include:

| Advantage                       | Benefit                        |
| ------------------------------- | ------------------------------ |
| Handles nonlinear relationships | Markets are nonlinear          |
| Captures feature interactions   | Sentiment + momentum effects   |
| Works well on small datasets    | No need for huge training sets |
| Strong predictive performance   | Widely used in finance         |

---

# 13. Model Optimization

Several improvements were implemented during training:

### Time-Based Train/Test Split

```
80% historical data → training
20% recent data → testing
```

This simulates **real-world forecasting conditions**.

---

### Hyperparameter Search

Grid search was used to tune:

```
learning_rate
max_depth
n_estimators
```

---

### Threshold Optimization

The prediction threshold was optimized to improve classification balance.

Default:

```
UP if probability > 0.50
```

Optimized threshold:

```
≈ 0.41
```

---

# 14. Model Performance

Final test accuracy:

```
≈ 56.4%
```

In financial prediction:

```
50% → random guessing
55–60% → meaningful predictive signal
```

Therefore the model demonstrates **statistical predictive power above random chance**.

---

# 15. Feature Importance

The trained model identifies the most important predictors.

| Feature             | Importance |
| ------------------- | ---------- |
| return_1d           | highest    |
| return_7d           | high       |
| return_3d           | high       |
| rolling_7_sentiment | moderate   |
| rolling_3_sentiment | moderate   |
| news_count          | lower      |

This indicates that **price momentum is the strongest driver**, while **news sentiment adds additional predictive context**.

This finding aligns with financial research literature.

---

# 16. Prediction Engine

File:

```
predictor.py
```

The prediction module performs **real-time sentiment analysis and inference**.

Steps:

```
Fetch latest news headlines
↓
Run FinBERT sentiment analysis
↓
Generate sentiment features
↓
Load trained ML model
↓
Predict UP/DOWN probability
```

Example output:

```
Prediction: UP
UP probability: 0.64
DOWN probability: 0.36
```

---

# 17. Market Ranking Engine

File:

```
market_ranker.py
```

This module runs predictions across **all NIFTY 50 stocks** and ranks them by sentiment strength.

Output includes:

```
Top Positive Sentiment Stocks
Top Negative Sentiment Stocks
```

This provides a **market-wide sentiment snapshot**.

---

# 18. Interactive Dashboard

File:

```
dashboard.py
```

The final system is deployed as an **interactive analytics dashboard using Streamlit**.

Features include:

```
Stock sentiment analysis
Real-time news sentiment
Prediction probabilities
3-month price chart
Market sentiment ranking
Model explanation
```

Run the dashboard locally:

```
streamlit run dashboard.py
```

---

# 19. Technologies Used

```
Python
Pandas
Scikit-learn
Transformers (FinBERT)
Streamlit
Yahoo Finance API
Google News RSS
NumPy
yfinance
```

---

# 20. Limitations

Current system limitations include:

```
Limited historical news coverage
No sector-specific models
No technical indicators
No macroeconomic variables
```

Financial markets are influenced by many additional factors.

---

# 21. Future Improvements

Possible extensions include:

```
Transformer-based time series models
Technical indicator integration
Sector-specific sentiment models
Real-time streaming data pipelines
Portfolio optimization strategies
```

---

# 22. Resume Description

**Financial News Sentiment Prediction System**

Developed an end-to-end machine learning pipeline that predicts next-day NIFTY 50 stock direction using FinBERT sentiment analysis and Gradient Boosting models. Implemented automated news scraping, sentiment feature engineering, momentum indicators, model training, and deployed a real-time market analytics dashboard using Streamlit.

---

# 23. Interview Summary (Short Version)

Built an end-to-end financial NLP and machine learning system that predicts next-day stock direction for NIFTY 50 companies using FinBERT sentiment analysis combined with price momentum features. The system automates news ingestion, feature engineering, supervised learning, and real-time predictions through an interactive dashboard.

---

# 24. Final Statement

This project demonstrates expertise in:

```
Financial NLP
Feature Engineering
Machine Learning Pipelines
Data Engineering
Model Deployment
Interactive Analytics Dashboards
```


