"""
Shared navbar component for SentinelQuant multi-page app.
Call render_navbar(active) at the top of every page.
active: 'home' | 'sentiment' | 'quant'
"""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, .stApp, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stHeader"]  { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }

.sq-nav {
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2.5rem;
    height: 56px;
    background: rgba(10,14,20,0.95);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid #1C2B3A;
    box-sizing: border-box;
}
.sq-logo {
    display: flex; align-items: center; gap: 9px;
    text-decoration: none; color: #E8EDF2;
    font-size: 14px; font-weight: 600; letter-spacing: -0.3px;
}
.sq-logo-icon {
    width: 30px; height: 30px; border-radius: 7px;
    border: 1px solid rgba(59,158,255,0.35);
    background: rgba(59,158,255,0.08);
    display: flex; align-items: center; justify-content: center;
}
.sq-logo-icon svg {
    width: 16px; height: 16px; stroke: #3B9EFF;
    fill: none; stroke-width: 2;
    stroke-linecap: round; stroke-linejoin: round;
}
.sq-nav-links { display: flex; align-items: center; gap: 8px; }
.sq-btn {
    display: inline-flex; align-items: center; gap: 5px;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px; font-weight: 500;
    padding: 7px 16px; border-radius: 7px;
    text-decoration: none;
    transition: all 0.15s ease;
    white-space: nowrap;
}
.sq-btn-ghost {
    color: #8899AA; background: transparent;
    border: 1px solid transparent;
}
.sq-btn-ghost:hover {
    color: #E8EDF2; border-color: #1C2B3A; background: #0F1620;
}
.sq-btn-active {
    color: #E8EDF2; border: 1px solid #1C2B3A; background: #0F1620;
}
.sq-btn-primary {
    color: #ffffff !important; background: #3B9EFF !important;
    border: 1px solid rgba(59,158,255,0.4);
    box-shadow: 0 2px 12px rgba(59,158,255,0.2);
}
.sq-btn-primary:hover {
    color: #ffffff !important; background: #2b8ef0 !important;
}
.block-container { padding-top: 80px !important; }
</style>
"""

_LOGO_SVG = """
<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <polyline points="2 18 8 10 13 14 19 6"/>
  <line x1="19" y1="6" x2="22" y2="6"/>
  <line x1="19" y1="6" x2="19" y2="9"/>
</svg>
"""


def render_navbar(active: str = "home") -> None:
    """Inject the shared navbar. active = 'home' | 'sentiment' | 'quant'"""

    def _cls(page: str) -> str:
        return "sq-btn sq-btn-active" if active == page else "sq-btn sq-btn-ghost"

    sentiment_cls = _cls("sentiment")
    quant_cls     = _cls("quant")
    home_cls      = _cls("home")

    st.markdown(f"""
{_CSS}
<nav class="sq-nav">
  <a class="sq-logo" href="/" title="SentinelQuant — Market Signal Platform">
    <div class="sq-logo-icon">{_LOGO_SVG}</div>
    SentinelQuant
  </a>
  <div class="sq-nav-links">
    <a class="{home_cls}"      href="/">&#8962; Home</a>
    <a class="{sentiment_cls}" href="/Sentiment_Predictor">Sentiment Predictor</a>
    <a class="sq-btn sq-btn-primary" href="/Quant_Dashboard">Quant Dashboard</a>
  </div>
</nav>
""", unsafe_allow_html=True)
