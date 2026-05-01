import os
import sys
import json
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from plotly.utils import PlotlyJSONEncoder
from pydantic import BaseModel, Field

_root = os.path.dirname(__file__)
for _p in ("data", "indicators", "strategies", "backtesting", "dashboard"):
    sys.path.append(os.path.join(_root, _p))

from backtester import backtest
from chart_generator import generate_chart
from data_fetcher import fetch_stock_data
from indicators import calculate_indicators
from trading_strategies import run_strategies, strategies_info

PERIOD_MAP = {"15m": "5d", "30m": "1mo", "1h": "3mo", "1d": "6mo"}
STRATEGY_TO_SIGNAL_COL = {
    "ma": "MA_signal",
    "rsi": "RSI_signal",
    "macd": "MACD_signal_trade",
    "bb": "BB_signal",
    "ema": "EMA_signal",
}

app = FastAPI(title="Quant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuantRequest(BaseModel):
    symbol: str
    market: str = "US"
    timeframe: str = Field(default="1d", pattern="^(15m|30m|1h|1d)$")
    strategies: list[str] = Field(default_factory=lambda: ["ma", "macd", "ema"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/quant/analyze")
def analyze_quant(payload: QuantRequest) -> dict[str, Any]:
    symbol = payload.symbol.strip().upper()
    market = payload.market.strip().upper()
    if market.startswith("IN") and not symbol.endswith(".NS"):
        symbol = f"{symbol}.NS"

    timeframe = payload.timeframe
    period = PERIOD_MAP[timeframe]
    strategies = [s.strip().lower() for s in payload.strategies if s.strip().lower() in STRATEGY_TO_SIGNAL_COL]
    if not strategies:
        raise HTTPException(status_code=400, detail="At least one valid strategy is required.")

    try:
        df_raw = fetch_stock_data(symbol, timeframe, period)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Data fetch failed: {exc}") from exc

    if df_raw.empty:
        raise HTTPException(status_code=404, detail="No data returned for this symbol.")

    df_ind = calculate_indicators(df_raw)
    df_sigs = run_strategies(df_ind, strategies)

    rows = []
    trade_logs: dict[str, list[dict[str, Any]]] = {}
    for key in strategies:
        col = STRATEGY_TO_SIGNAL_COL[key]
        result = backtest(df_sigs, col)
        trade_log_df = result["trade_log"].copy()
        if not trade_log_df.empty and "Date" in trade_log_df.columns:
            trade_log_df["Date"] = trade_log_df["Date"].astype(str)
        trade_logs[col] = trade_log_df.to_dict(orient="records") if not trade_log_df.empty else []
        rows.append(
            {
                "strategy": col,
                "final_value": result["final_value"],
                "total_return": result["total_return"],
                "total_trades": result["total_trades"],
                "win_rate": result["win_rate"],
                "max_drawdown": result["max_drawdown"],
                "sharpe_ratio": result["sharpe_ratio"],
            }
        )

    comparison_df = pd.DataFrame(rows).sort_values("total_return", ascending=False).reset_index(drop=True)
    best = comparison_df.iloc[0].to_dict()

    chart_figures: dict[str, Any] = {}
    for key in strategies:
        signal_col = STRATEGY_TO_SIGNAL_COL[key]
        fig = generate_chart(
            df_sigs,
            strategy_column=signal_col,
            show_sma=True,
            show_ema=True,
            show_bb=True,
            open_in_browser=False,
        )
        chart_figures[signal_col] = json.loads(json.dumps(fig.to_plotly_json(), cls=PlotlyJSONEncoder))

    signal_columns = [STRATEGY_TO_SIGNAL_COL[s] for s in strategies]
    trimmed = df_sigs[["Date", "Close", *signal_columns]].tail(150).copy()
    trimmed["Date"] = trimmed["Date"].astype(str)
    chart_rows = trimmed.to_dict(orient="records")
    strategy_reference = [
        {
            "signal_column": STRATEGY_TO_SIGNAL_COL[key],
            "name": strategies_info[key]["name"],
            "description": strategies_info[key]["description"],
            "rules": strategies_info[key]["rules"],
        }
        for key in strategies
    ]

    return {
        "symbol": symbol,
        "market": "INDIA" if market.startswith("IN") else "US",
        "timeframe": timeframe,
        "period": period,
        "best_strategy": best,
        "comparison": comparison_df.to_dict(orient="records"),
        "chart_figures": chart_figures,
        "chart_rows": chart_rows,
        "strategy_reference": strategy_reference,
        "trade_logs": trade_logs,
    }
