import { useEffect, useMemo, useRef, useState } from "react";
import { Activity, Loader2 } from "lucide-react";
import Plotly from "plotly.js-dist-min";
import { Button } from "@/components/ui/button";

const SENTIMENT_API_URL = import.meta.env.VITE_SENTIMENT_API_URL ?? "http://localhost:8601";
const QUANT_API_URL = import.meta.env.VITE_QUANT_API_URL ?? "http://localhost:8602";
const AUTH_TOKEN_KEY = "sentinelquant_auth_token";

type MarketType = "US" | "INDIA";

type SentimentResponse = {
  symbol: string;
  market: MarketType;
  prediction: string;
  up_prob: number;
  down_prob: number;
  news: string[];
  price_chart: Array<{ Date: string; Close: number }>;
};

type QuantComparison = {
  strategy: string;
  final_value: number;
  total_return: number;
  total_trades: number;
  win_rate: number;
  max_drawdown: number;
  sharpe_ratio: number;
};

type QuantResponse = {
  symbol: string;
  market: MarketType;
  timeframe: string;
  period: string;
  best_strategy: QuantComparison;
  comparison: QuantComparison[];
  chart_figures: Record<string, { data: unknown[]; layout: Record<string, unknown> }>;
  chart_rows: Array<Record<string, string | number>>;
  strategy_reference: Array<{
    signal_column: string;
    name: string;
    description: string;
    rules: string;
  }>;
  trade_logs: Record<
    string,
    Array<{
      Date?: string;
      Action?: string;
      Price?: number;
      Shares?: number;
      Profit?: number | null;
    }>
  >;
};

type SymbolsResponse = {
  market: MarketType;
  symbols: string[];
};

type AuthUser = {
  id: number;
  name: string;
  email: string;
};

type AuthResponse = {
  token: string;
  user: AuthUser;
};

const strategyOptions = [
  { key: "ma", label: "Moving Average", signalColumn: "MA_signal" },
  { key: "rsi", label: "RSI", signalColumn: "RSI_signal" },
  { key: "macd", label: "MACD", signalColumn: "MACD_signal_trade" },
  { key: "bb", label: "Bollinger Bands", signalColumn: "BB_signal" },
  { key: "ema", label: "EMA Crossover", signalColumn: "EMA_signal" },
];

const formatPct = (value: number) => `${(value * 100).toFixed(1)}%`;
const currencyForMarket = (market: MarketType) => (market === "INDIA" ? "INR" : "USD");
const symbolForCurrency = (currency: string) => (currency === "INR" ? "₹" : "$");
const INITIAL_CAPITAL = 10000;

const toTitle = (value: string) =>
  value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (m) => m.toUpperCase());

const Index = () => {
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");
  const [authToken, setAuthToken] = useState<string | null>(() => localStorage.getItem(AUTH_TOKEN_KEY));
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [authName, setAuthName] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [isAuthLoading, setIsAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [market, setMarket] = useState<MarketType>("US");
  const [symbols, setSymbols] = useState<string[]>([]);
  const [symbol, setSymbol] = useState("AAPL");
  const [symbolQuery, setSymbolQuery] = useState("AAPL");
  const [timeframe, setTimeframe] = useState("1d");
  const [strategies, setStrategies] = useState<string[]>(["ma", "macd", "ema"]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSymbolsLoading, setIsSymbolsLoading] = useState(false);
  const [error, setError] = useState("");
  const [sentimentResult, setSentimentResult] = useState<SentimentResponse | null>(null);
  const [quantResult, setQuantResult] = useState<QuantResponse | null>(null);
  const [selectedSignalColumn, setSelectedSignalColumn] = useState("MA_signal");
  const plotRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const fetchMe = async () => {
      if (!authToken) {
        setAuthUser(null);
        return;
      }

      try {
        const response = await fetch(`${SENTIMENT_API_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${authToken}` },
        });
        if (!response.ok) {
          localStorage.removeItem(AUTH_TOKEN_KEY);
          setAuthToken(null);
          setAuthUser(null);
          return;
        }
        const data: { user: AuthUser } = await response.json();
        setAuthUser(data.user);
      } catch {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        setAuthToken(null);
        setAuthUser(null);
      }
    };

    fetchMe();
  }, [authToken]);

  useEffect(() => {
    if (!authUser || !authToken) return;

    const fetchSymbols = async () => {
      setIsSymbolsLoading(true);
      try {
        const response = await fetch(`${SENTIMENT_API_URL}/api/sentiment/symbols?market=${market}`, {
          headers: { Authorization: `Bearer ${authToken}` },
        });
        const data: SymbolsResponse = await response.json();
        const nextSymbols = Array.isArray(data.symbols) ? data.symbols : [];
        setSymbols(nextSymbols);
        if (nextSymbols.length > 0) {
          setSymbol(nextSymbols[0]);
          setSymbolQuery(nextSymbols[0]);
        }
      } catch {
        setSymbols([]);
      } finally {
        setIsSymbolsLoading(false);
      }
    };

    fetchSymbols();
  }, [market, authToken, authUser]);

  useEffect(() => {
    if (!authUser || !authToken) return;

    const controller = new AbortController();
    const timeout = setTimeout(async () => {
      try {
        const response = await fetch(
          `${SENTIMENT_API_URL}/api/sentiment/symbol-search?market=${market}&q=${encodeURIComponent(symbolQuery)}`,
          {
            signal: controller.signal,
            headers: { Authorization: `Bearer ${authToken}` },
          },
        );
        const data: SymbolsResponse = await response.json();
        setSymbols(Array.isArray(data.symbols) ? data.symbols : []);
      } catch {
        // Ignore aborted requests and transient fetch errors for typeahead.
      }
    }, 220);
    return () => {
      controller.abort();
      clearTimeout(timeout);
    };
  }, [market, symbolQuery, authToken, authUser]);

  const handleAuthSubmit = async () => {
    setAuthError("");
    setIsAuthLoading(true);
    try {
      const endpoint = authMode === "signup" ? "/api/auth/signup" : "/api/auth/login";
      const payload =
        authMode === "signup"
          ? { name: authName.trim(), email: authEmail.trim(), password: authPassword }
          : { email: authEmail.trim(), password: authPassword };

      const response = await fetch(`${SENTIMENT_API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = (await response.json()) as AuthResponse | { detail?: string };
      if (!response.ok || !("token" in data)) {
        throw new Error((data as { detail?: string }).detail ?? "Authentication failed.");
      }

      localStorage.setItem(AUTH_TOKEN_KEY, data.token);
      setAuthToken(data.token);
      setAuthUser(data.user);
      setAuthPassword("");
      setAuthError("");
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setIsAuthLoading(false);
    }
  };

  const handleLogout = async () => {
    if (authToken) {
      try {
        await fetch(`${SENTIMENT_API_URL}/api/auth/logout`, {
          method: "POST",
          headers: { Authorization: `Bearer ${authToken}` },
        });
      } catch {
        // Ignore logout network errors; local clear is enough.
      }
    }
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setAuthToken(null);
    setAuthUser(null);
    setSentimentResult(null);
    setQuantResult(null);
  };

  const toggleStrategy = (key: string) => {
    setStrategies((prev) => {
      if (prev.includes(key)) {
        if (prev.length === 1) return prev;
        return prev.filter((item) => item !== key);
      }
      return [...prev, key];
    });
  };

  const runAnalysis = async () => {
    setError("");
    setIsLoading(true);
    setSentimentResult(null);
    setQuantResult(null);

    try {
      const [sentimentRes, quantRes] = await Promise.all([
        fetch(`${SENTIMENT_API_URL}/api/sentiment/analyze`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify({ symbol, market }),
        }),
        fetch(`${QUANT_API_URL}/api/quant/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ symbol, market, timeframe, strategies }),
        }),
      ]);

      const sentimentData = await sentimentRes.json();
      const quantData = await quantRes.json();

      if (!sentimentRes.ok) throw new Error(sentimentData.detail ?? "Sentiment analysis failed.");
      if (!quantRes.ok) throw new Error(quantData.detail ?? "Quant analysis failed.");

      setSentimentResult(sentimentData);
      setQuantResult(quantData);
      setSelectedSignalColumn(quantData.best_strategy?.strategy ?? "MA_signal");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run analysis.");
    } finally {
      setIsLoading(false);
    }
  };

  const latestPrice = useMemo(() => {
    if (!sentimentResult?.price_chart?.length) return null;
    const row = sentimentResult.price_chart[sentimentResult.price_chart.length - 1];
    return Number(row.Close).toFixed(2);
  }, [sentimentResult]);
  const displayMarket = market;
  const currency = currencyForMarket(market);
  const currencySymbol = symbolForCurrency(currency);

  const availableSignalColumns = useMemo(() => {
    if (!quantResult?.comparison?.length) return [];
    return quantResult.comparison.map((item) => item.strategy);
  }, [quantResult]);

  useEffect(() => {
    const container = plotRef.current;
    if (!container || !quantResult?.chart_figures) return;

    const figure = quantResult.chart_figures[selectedSignalColumn];
    if (!figure) return;

    Plotly.react(container, figure.data as Plotly.Data[], figure.layout as Partial<Plotly.Layout>, {
      responsive: true,
      displayModeBar: false,
    });

    return () => {
      Plotly.purge(container);
    };
  }, [quantResult, selectedSignalColumn]);

  if (!authUser) {
    return (
      <div className="min-h-screen bg-background text-foreground">
        <main className="container flex min-h-screen items-center justify-center py-10">
          <section className="w-full max-w-md rounded-2xl border border-border bg-card p-6 md:p-8">
            <div className="mb-6 flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-md border border-primary/30 bg-primary/10">
                <Activity className="h-4 w-4 text-primary" strokeWidth={2.5} />
              </div>
              <span className="text-sm font-semibold tracking-tight">SentinelQuant</span>
            </div>
            <h1 className="text-2xl font-semibold tracking-tight">{authMode === "signup" ? "Create account" : "Welcome back"}</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              {authMode === "signup"
                ? "Sign up to start running sentiment and quant analysis."
                : "Log in to access your analysis dashboard."}
            </p>

            <div className="mt-6 space-y-4">
              {authMode === "signup" ? (
                <div>
                  <label className="text-xs text-muted-foreground">Name</label>
                  <input
                    className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                    value={authName}
                    onChange={(e) => setAuthName(e.target.value)}
                    placeholder="Your name"
                  />
                </div>
              ) : null}

              <div>
                <label className="text-xs text-muted-foreground">Email</label>
                <input
                  className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  type="email"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  placeholder="name@example.com"
                />
              </div>

              <div>
                <label className="text-xs text-muted-foreground">Password</label>
                <input
                  className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                  type="password"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  placeholder="Minimum 6 characters"
                />
              </div>

              {authError ? (
                <p className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">{authError}</p>
              ) : null}

              <Button onClick={handleAuthSubmit} className="w-full" disabled={isAuthLoading}>
                {isAuthLoading ? (
                  <span className="inline-flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Please wait...
                  </span>
                ) : authMode === "signup" ? (
                  "Sign Up"
                ) : (
                  "Log In"
                )}
              </Button>

              <button
                onClick={() => {
                  setAuthMode((prev) => (prev === "login" ? "signup" : "login"));
                  setAuthError("");
                }}
                className="w-full text-xs text-muted-foreground hover:text-foreground"
              >
                {authMode === "signup" ? "Already have an account? Log in" : "Need an account? Sign up"}
              </button>
            </div>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-xl">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-md border border-primary/30 bg-primary/10">
              <Activity className="h-4 w-4 text-primary" strokeWidth={2.5} />
            </div>
            <span className="text-sm font-semibold tracking-tight">SentinelQuant</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground">{authUser.email}</span>
            <span className="text-xs uppercase tracking-wide text-muted-foreground">{displayMarket === "INDIA" ? "NIFTY 50" : "US Market"}</span>
            <Button variant="outline" size="sm" onClick={handleLogout}>
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="container py-10">
        <section className="rounded-2xl border border-border bg-card p-6 md:p-8">
          <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Unified Market Analysis</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Run sentiment prediction and quant backtesting in one place.
          </p>

          <div className="mt-6 grid items-end gap-4 md:grid-cols-4">
            <div>
              <label className="text-xs text-muted-foreground">Market</label>
              <select
                className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={market}
                onChange={(e) => setMarket(e.target.value as MarketType)}
              >
                <option value="US">US Market</option>
                <option value="INDIA">NIFTY 50</option>
              </select>
            </div>

            <div>
              <label className="text-xs text-muted-foreground">Symbol</label>
              <input
                list="symbol-options"
                className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={symbolQuery}
                onChange={(e) => {
                  const value = e.target.value.toUpperCase().trimStart();
                  setSymbolQuery(value);
                  setSymbol(value);
                }}
                placeholder={market === "INDIA" ? "Search NIFTY 50 ticker" : "Search US ticker"}
              />
              <datalist id="symbol-options">
                {symbols.map((item) => (
                  <option key={item} value={item} />
                ))}
              </datalist>
            </div>

            <div>
              <label className="text-xs text-muted-foreground">Timeframe</label>
              <select
                className="mt-1 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
              >
                <option value="15m">15m</option>
                <option value="30m">30m</option>
                <option value="1h">1h</option>
                <option value="1d">1d</option>
              </select>
            </div>

            <div className="flex items-end">
              <Button onClick={runAnalysis} className="w-full" disabled={isLoading || isSymbolsLoading}>
                {isLoading ? (
                  <span className="inline-flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Running...
                  </span>
                ) : (
                  "Run Full Analysis"
                )}
              </Button>
            </div>
          </div>

          <div className="mt-5">
            <p className="text-xs text-muted-foreground">Strategies</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {strategyOptions.map((option) => (
                <button
                  key={option.key}
                  onClick={() => toggleStrategy(option.key)}
                  className={`rounded-full border px-3 py-1 text-xs ${
                    strategies.includes(option.key)
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border text-muted-foreground"
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {error ? (
            <p className="mt-4 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </p>
          ) : null}
        </section>

        {sentimentResult ? (
          <section className="mt-6 rounded-2xl border border-border bg-card p-6 md:p-8">
            <h2 className="text-xl font-semibold">Step 1: Sentiment Result</h2>
            <div className="mt-4 grid gap-4 md:grid-cols-4">
              <div className="rounded-lg border border-border p-4">
                <p className="text-xs text-muted-foreground">Prediction</p>
                <p className="mt-1 text-lg font-semibold">{sentimentResult.prediction}</p>
              </div>
              <div className="rounded-lg border border-border p-4">
                <p className="text-xs text-muted-foreground">Upside Probability</p>
                <p className="mt-1 text-lg font-semibold">{formatPct(sentimentResult.up_prob)}</p>
              </div>
              <div className="rounded-lg border border-border p-4">
                <p className="text-xs text-muted-foreground">Downside Probability</p>
                <p className="mt-1 text-lg font-semibold">{formatPct(sentimentResult.down_prob)}</p>
              </div>
              <div className="rounded-lg border border-border p-4">
                <p className="text-xs text-muted-foreground">Latest Price</p>
                <p className="mt-1 text-lg font-semibold">{latestPrice ? `${currencySymbol}${latestPrice}` : "N/A"}</p>
              </div>
            </div>

            <h3 className="mt-6 text-sm font-medium text-muted-foreground">Top Headlines</h3>
            <ul className="mt-2 space-y-2 text-sm">
              {sentimentResult.news.slice(0, 8).map((headline) => (
                <li key={headline} className="rounded-md border border-border px-3 py-2">
                  {headline}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {quantResult ? (
          <section className="mt-6 rounded-2xl border border-border bg-card p-6 md:p-8">
            <h2 className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
              Performance Summary - Best Strategy: {quantResult.best_strategy.strategy}
            </h2>
            <div className="mt-4 grid gap-3 md:grid-cols-6">
              <div className="rounded-lg border border-border bg-background/50 p-4 text-center">
                <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Final Value</p>
                <p
                  className={`mt-2 text-3xl font-semibold ${
                    Number(quantResult.best_strategy.final_value) >= INITIAL_CAPITAL ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {currencySymbol}{quantResult.best_strategy.final_value}
                </p>
              </div>
              <div className="rounded-lg border border-border bg-background/50 p-4 text-center">
                <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Total Return</p>
                <p
                  className={`mt-2 text-3xl font-semibold ${
                    Number(quantResult.best_strategy.total_return) >= 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {quantResult.best_strategy.total_return}%
                </p>
              </div>
              <div className="rounded-lg border border-border bg-background/50 p-4 text-center">
                <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Total Trades</p>
                <p className="mt-2 text-3xl font-semibold text-foreground">{quantResult.best_strategy.total_trades}</p>
              </div>
              <div className="rounded-lg border border-border bg-background/50 p-4 text-center">
                <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Win Rate</p>
                <p
                  className={`mt-2 text-3xl font-semibold ${
                    Number(quantResult.best_strategy.win_rate) >= 50 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {quantResult.best_strategy.win_rate}%
                </p>
              </div>
              <div className="rounded-lg border border-border bg-background/50 p-4 text-center">
                <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Max Drawdown</p>
                <p className="mt-2 text-3xl font-semibold text-rose-400">{quantResult.best_strategy.max_drawdown}%</p>
              </div>
              <div className="rounded-lg border border-border bg-background/50 p-4 text-center">
                <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">Sharpe Ratio</p>
                <p
                  className={`mt-2 text-3xl font-semibold ${
                    Number(quantResult.best_strategy.sharpe_ratio) >= 0 ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {quantResult.best_strategy.sharpe_ratio}
                </p>
              </div>
            </div>

            <div className="mt-6">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-medium text-muted-foreground">Buy/Sell Signal Chart (Backtest)</h3>
                <select
                  className="rounded-md border border-border bg-background px-3 py-1.5 text-xs"
                  value={selectedSignalColumn}
                  onChange={(e) => setSelectedSignalColumn(e.target.value)}
                >
                  {availableSignalColumns.map((col) => (
                    <option key={col} value={col}>
                      {toTitle(col)}
                    </option>
                  ))}
                </select>
              </div>
              <div className="w-full rounded-md border border-border bg-background/60 p-2">
                <div ref={plotRef} className="min-h-[560px] w-full" />
              </div>
            </div>

            <div className="mt-6 overflow-x-auto rounded-md border border-border">
              <table className="w-full min-w-[700px] text-sm">
                <thead className="border-b border-border bg-secondary/50">
                  <tr>
                    <th className="px-3 py-2 text-left">Strategy</th>
                    <th className="px-3 py-2 text-left">Final Value ({currency})</th>
                    <th className="px-3 py-2 text-left">Return</th>
                    <th className="px-3 py-2 text-left">Trades</th>
                    <th className="px-3 py-2 text-left">Win Rate</th>
                    <th className="px-3 py-2 text-left">Max Drawdown</th>
                    <th className="px-3 py-2 text-left">Sharpe</th>
                  </tr>
                </thead>
                <tbody>
                  {quantResult.comparison.map((row) => (
                    <tr key={row.strategy} className="border-b border-border/50">
                      <td className="px-3 py-2">{toTitle(row.strategy)}</td>
                      <td className="px-3 py-2">{currencySymbol}{row.final_value}</td>
                      <td className="px-3 py-2">{row.total_return}%</td>
                      <td className="px-3 py-2">{row.total_trades}</td>
                      <td className="px-3 py-2">{row.win_rate}%</td>
                      <td className="px-3 py-2">{row.max_drawdown}%</td>
                      <td className="px-3 py-2">{row.sharpe_ratio}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-8">
              <h3 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">Trade Logs</h3>
              <div className="mt-3 space-y-3">
                {quantResult.comparison.map((row) => {
                  const logs = quantResult.trade_logs?.[row.strategy] ?? [];
                  return (
                    <details key={row.strategy} className="rounded-md border border-border bg-background/50">
                      <summary className="cursor-pointer px-4 py-3 text-sm text-foreground">
                        {toTitle(row.strategy)} - {logs.length} trades
                      </summary>
                      <div className="border-t border-border p-3">
                        {logs.length === 0 ? (
                          <p className="text-xs text-muted-foreground">No trades executed for this strategy.</p>
                        ) : (
                          <div className="overflow-x-auto rounded-md border border-border">
                            <table className="w-full min-w-[720px] text-xs">
                              <thead className="border-b border-border bg-secondary/50">
                                <tr>
                                  <th className="px-2 py-2 text-left">Date</th>
                                  <th className="px-2 py-2 text-left">Action</th>
                                  <th className="px-2 py-2 text-left">Price</th>
                                  <th className="px-2 py-2 text-left">Shares</th>
                                  <th className="px-2 py-2 text-left">Profit</th>
                                </tr>
                              </thead>
                              <tbody>
                                {logs.map((log, index) => (
                                  <tr key={`${row.strategy}-${index}`} className="border-b border-border/50">
                                    <td className="px-2 py-2">{log.Date ?? "-"}</td>
                                    <td className="px-2 py-2">{log.Action ?? "-"}</td>
                                    <td className="px-2 py-2">{log.Price ?? "-"}</td>
                                    <td className="px-2 py-2">{log.Shares ?? "-"}</td>
                                    <td className="px-2 py-2">
                                      {log.Profit === null || log.Profit === undefined ? "-" : `${currencySymbol}${log.Profit}`}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    </details>
                  );
                })}
              </div>
            </div>

            <div className="mt-8">
              <h3 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">Strategy Reference</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                A concise description of the signal logic used by each selected strategy.
              </p>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                {quantResult.strategy_reference?.map((item) => (
                  <article key={item.signal_column} className="rounded-md border border-border bg-background/50 p-4">
                    <h4 className="text-sm font-semibold">{item.name}</h4>
                    <p className="mt-2 text-xs leading-6 text-muted-foreground">{item.description}</p>
                    <p className="mt-3 text-xs text-amber-300">{item.rules}</p>
                  </article>
                ))}
              </div>
            </div>
          </section>
        ) : null}
      </main>

      <footer className="border-t border-border">
        <div className="container flex flex-col items-center justify-between gap-4 py-8 text-sm text-muted-foreground md:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded border border-primary/30 bg-primary/10">
              <Activity className="h-3 w-3 text-primary" strokeWidth={2.5} />
            </div>
            <span>SentinelQuant</span>
          </div>
          <p>Market sentiment + quant backtesting</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
