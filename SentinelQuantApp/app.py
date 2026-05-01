"""
SentinelQuant — Landing Page (app.py)
Single entry point for the multi-page Streamlit app.
"""
import streamlit as st
from components.navbar import render_navbar

st.set_page_config(
    page_title="SentinelQuant — Market Signal Platform",
    layout="wide",
    initial_sidebar_state="collapsed",
)

render_navbar(active="home")

st.markdown("""
<style>
:root {
    --bg:        #0A0E14;
    --surface:   #0F1620;
    --border:    #1C2B3A;
    --accent:    #3B9EFF;
    --text-hi:   #E8EDF2;
    --text-mid:  #8899AA;
    --text-lo:   #3D5166;
}
html, body, .stApp { background: var(--bg) !important; }

/* ── Hero ── */
.hero {
    text-align: center;
    padding: 80px 24px 60px;
    position: relative;
}
.hero-badge {
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 12px; color: var(--text-mid);
    border: 1px solid var(--border); border-radius: 20px;
    padding: 4px 14px; margin-bottom: 32px;
    background: rgba(15,22,32,0.6); backdrop-filter: blur(8px);
}
.hero-badge-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--accent); animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
.hero-title {
    font-size: clamp(36px, 6vw, 72px);
    font-weight: 600; letter-spacing: -1.5px;
    color: var(--text-hi); line-height: 1.1; margin-bottom: 24px;
}
.hero-accent {
    position: relative; display: inline-block; color: var(--text-hi);
}
.hero-accent::after {
    content: ''; position: absolute;
    bottom: -4px; left: 0; right: 0;
    height: 3px; background: var(--accent); border-radius: 2px;
}
.hero-desc {
    font-size: 16px; color: var(--text-mid);
    max-width: 600px; margin: 0 auto 40px;
    line-height: 1.75;
}
.hero-btns {
    display: flex; flex-wrap: wrap;
    align-items: center; justify-content: center; gap: 14px;
    margin-bottom: 64px;
}
.hero-btn-primary {
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--accent); color: #fff !important;
    font-size: 15px; font-weight: 500;
    padding: 13px 28px; border-radius: 9px;
    text-decoration: none;
    box-shadow: 0 4px 20px rgba(59,158,255,0.3);
    transition: all 0.2s;
}
.hero-btn-primary:hover { background: #2b8ef0; transform: translateY(-2px); }
.hero-btn-outline {
    display: inline-flex; align-items: center; gap: 8px;
    background: transparent; color: var(--text-hi) !important;
    font-size: 15px; font-weight: 500;
    padding: 13px 28px; border-radius: 9px;
    border: 1px solid var(--border);
    text-decoration: none; transition: all 0.2s;
}
.hero-btn-outline:hover {
    border-color: var(--accent); color: var(--accent) !important;
    transform: translateY(-2px);
}

/* ── Stats ── */
.stats-strip {
    display: flex; justify-content: center; gap: 48px;
    border-top: 1px solid var(--border);
    padding-top: 32px; margin: 0 auto; max-width: 480px;
}
.stat-item { text-align: center; }
.stat-val {
    font-size: 20px; font-weight: 600;
    color: var(--text-hi); letter-spacing: -0.5px;
}
.stat-lbl { font-size: 12px; color: var(--text-mid); margin-top: 4px; }

/* ── Section heading ── */
.sec-label {
    font-size: 11px; font-weight: 500; letter-spacing: 0.18em;
    text-transform: uppercase; color: var(--accent);
    margin-bottom: 12px;
}
.sec-title {
    font-size: clamp(24px, 4vw, 36px);
    font-weight: 600; letter-spacing: -0.5px;
    color: var(--text-hi); margin-bottom: 40px;
}
.sec-title span { color: var(--text-mid); }

/* ── Feature cards ── */
.cards-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
    max-width: 960px; margin: 0 auto;
}
.feat-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 14px; padding: 32px 28px;
    transition: all 0.25s; position: relative; overflow: hidden;
}
.feat-card:hover {
    border-color: rgba(59,158,255,0.5);
    transform: translateY(-3px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.feat-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(59,158,255,0.6), transparent);
    opacity: 0; transition: opacity 0.25s;
}
.feat-card:hover::before { opacity: 1; }
.feat-icon {
    width: 44px; height: 44px; border-radius: 10px;
    border: 1px solid var(--border); background: var(--bg);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 20px;
}
.feat-icon svg {
    width: 20px; height: 20px; stroke: var(--text-mid);
    fill: none; stroke-width: 1.8;
    stroke-linecap: round; stroke-linejoin: round;
    transition: stroke 0.2s;
}
.feat-card:hover .feat-icon svg { stroke: var(--accent); }
.feat-tag {
    float: right; font-size: 10px; font-weight: 500;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--text-mid); border: 1px solid var(--border);
    border-radius: 20px; padding: 2px 10px;
}
.feat-title {
    font-size: 18px; font-weight: 600; color: var(--text-hi);
    margin-bottom: 14px; clear: both;
}
.feat-list { list-style: none; padding: 0; margin: 0; }
.feat-list li {
    display: flex; gap: 10px; align-items: flex-start;
    font-size: 14px; color: var(--text-mid);
    line-height: 1.6; margin-bottom: 10px;
}
.feat-list li::before {
    content: ''; width: 5px; height: 5px; border-radius: 50%;
    background: var(--accent); flex-shrink: 0; margin-top: 8px;
}

/* ── How it works ── */
.how-grid {
    display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;
    max-width: 960px; margin: 0 auto;
}
.how-card {
    background: var(--bg); border: 1px solid var(--border);
    border-radius: 12px; padding: 28px 24px;
    transition: border-color 0.2s;
}
.how-card:hover { border-color: rgba(59,158,255,0.4); }
.how-step {
    font-family: 'DM Mono', monospace; font-size: 11px;
    color: var(--accent); margin-bottom: 16px;
}
.how-icon {
    width: 36px; height: 36px; border-radius: 8px;
    border: 1px solid var(--border); background: var(--surface);
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 16px;
}
.how-icon svg {
    width: 17px; height: 17px; stroke: var(--text-mid);
    fill: none; stroke-width: 1.8;
    stroke-linecap: round; stroke-linejoin: round;
}
.how-title {
    font-size: 15px; font-weight: 600;
    color: var(--text-hi); margin-bottom: 8px;
}
.how-desc { font-size: 13px; color: var(--text-mid); line-height: 1.65; }

/* ── CTA ── */
.cta-wrap {
    border: 1px solid var(--border); border-radius: 20px;
    background: var(--surface); text-align: center;
    padding: 64px 32px; position: relative; overflow: hidden;
    max-width: 960px; margin: 0 auto;
}
.cta-glow {
    position: absolute; top: -80px; left: 50%;
    transform: translateX(-50%);
    width: 500px; height: 250px;
    background: radial-gradient(ellipse, rgba(59,158,255,0.12) 0%, transparent 70%);
    pointer-events: none;
}
.cta-title {
    font-size: clamp(22px, 4vw, 34px); font-weight: 600;
    color: var(--text-hi); letter-spacing: -0.5px;
    max-width: 540px; margin: 0 auto 14px;
}
.cta-desc {
    font-size: 14px; color: var(--text-mid); margin-bottom: 32px;
}

/* ── Footer ── */
.footer {
    text-align: center; padding: 32px 0 16px;
    border-top: 1px solid var(--border);
    font-size: 12px; color: var(--text-lo);
    font-family: 'DM Mono', monospace;
}
</style>

<!-- HERO -->
<section class="hero">
  <div class="hero-badge">
    <span class="hero-badge-dot"></span>
    Live market intelligence engine
  </div>
  <h1 class="hero-title">
    Market <span class="hero-accent">Signal</span> Platform
  </h1>
  <p class="hero-desc">
    Predict market direction using financial news sentiment and evaluate
    strategies using quantitative analysis.
  </p>
  <div class="hero-btns">
    <a class="hero-btn-primary" href="/Quant_Dashboard">
      Open Quant Dashboard &rarr;
    </a>
    <a class="hero-btn-outline" href="/Sentiment_Predictor">
      Open Sentiment Predictor &rarr;
    </a>
  </div>
  <div class="stats-strip">
    <div class="stat-item">
      <div class="stat-val">FinBERT</div>
      <div class="stat-lbl">NLP Engine</div>
    </div>
    <div class="stat-item">
      <div class="stat-val">5</div>
      <div class="stat-lbl">Indicators</div>
    </div>
    <div class="stat-item">
      <div class="stat-val">Real-time</div>
      <div class="stat-lbl">Backtesting</div>
    </div>
  </div>
</section>

<hr style="border:none;border-top:1px solid #1C2B3A;margin:0 0 56px;">

<!-- FEATURES -->
<section id="features" style="max-width:960px;margin:0 auto;padding:0 24px 72px;">
  <p class="sec-label">Modules</p>
  <h2 class="sec-title">Two engines. <span>One platform.</span></h2>
  <div class="cards-grid">
    <article class="feat-card">
      <span class="feat-tag">NLP</span>
      <div class="feat-icon">
        <svg viewBox="0 0 24 24"><path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8V6Z"/></svg>
      </div>
      <h3 class="feat-title">News Sentiment Prediction</h3>
      <ul class="feat-list">
        <li>Uses NLP (FinBERT) to analyze financial news</li>
        <li>Predicts next-day stock direction (UP / DOWN)</li>
        <li>Machine learning with engineered sentiment features</li>
      </ul>
    </article>
    <article class="feat-card">
      <span class="feat-tag">Quant</span>
      <div class="feat-icon">
        <svg viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
      </div>
      <h3 class="feat-title">Quant Trading Dashboard</h3>
      <ul class="feat-list">
        <li>5 technical indicators: MA, RSI, MACD, Bollinger Bands, EMA</li>
        <li>Generates buy / sell signals automatically</li>
        <li>Historical backtesting and performance analysis</li>
      </ul>
    </article>
  </div>
</section>

<!-- HOW IT WORKS -->
<section id="how" style="background:#0F1620;border-top:1px solid #1C2B3A;border-bottom:1px solid #1C2B3A;padding:56px 24px;margin-bottom:72px;">
  <div style="max-width:960px;margin:0 auto;">
    <p class="sec-label" style="text-align:center;">Process</p>
    <h2 class="sec-title" style="text-align:center;">How it works</h2>
    <div class="how-grid">
      <div class="how-card">
        <div class="how-step">01</div>
        <div class="how-icon">
          <svg viewBox="0 0 24 24"><path d="M12 2a5 5 0 1 0 0 10A5 5 0 0 0 12 2Z"/><path d="M12 16c-5.33 0-8 2.67-8 4v2h16v-2c0-1.33-2.67-4-8-4Z"/></svg>
        </div>
        <h4 class="how-title">Analyze News Sentiment</h4>
        <p class="how-desc">FinBERT processes financial news to extract directional sentiment signals.</p>
      </div>
      <div class="how-card">
        <div class="how-step">02</div>
        <div class="how-icon">
          <svg viewBox="0 0 24 24"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
        </div>
        <h4 class="how-title">Generate Predictions</h4>
        <p class="how-desc">ML models forecast next-day price direction from engineered features.</p>
      </div>
      <div class="how-card">
        <div class="how-step">03</div>
        <div class="how-icon">
          <svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        </div>
        <h4 class="how-title">Evaluate with Backtesting</h4>
        <p class="how-desc">Test strategies against historical data and measure real performance.</p>
      </div>
    </div>
  </div>
</section>

<!-- CTA -->
<section style="padding:0 24px 80px;">
  <div class="cta-wrap">
    <div class="cta-glow"></div>
    <h2 class="cta-title">Ready to explore the modules?</h2>
    <p class="cta-desc">Two specialised engines — pick where to start.</p>
    <div class="hero-btns">
      <a class="hero-btn-primary" href="/Quant_Dashboard">Open Quant Dashboard</a>
      <a class="hero-btn-outline" href="/Sentiment_Predictor">Open Sentiment Predictor</a>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer class="footer">
  SentinelQuant &nbsp;·&nbsp; Built for financial analytics and machine learning demonstration
</footer>
""", unsafe_allow_html=True)
