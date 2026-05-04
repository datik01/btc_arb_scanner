"""
app.py - Prediction Markets BTC Hourly Arbitrage Assistant
"""

import streamlit as st
import pandas as pd
import json
from dotenv import load_dotenv
import sys
import importlib

load_dotenv(override=True)

# Force reload of agents to ensure changes are picked up by Streamlit
import agents
if "agents" in sys.modules:
    importlib.reload(agents)

from agents import run_pipeline

st.set_page_config(
    page_title="BTC Hourly Arbitrage Scanner",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM CSS INJECTION
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root overrides ── */
html, body, [class*="st-"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
code, pre, [data-testid="stCode"] * {
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer, header {visibility: hidden;}

/* ── Animated gradient keyframes ── */
@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 15px rgba(0, 212, 170, 0.15); }
    50% { box-shadow: 0 0 30px rgba(0, 212, 170, 0.3); }
}
@keyframes borderGlow {
    0%, 100% { border-color: rgba(0, 212, 170, 0.2); }
    50% { border-color: rgba(0, 212, 170, 0.5); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ── Glassmorphism panels (all bordered containers) ── */
[data-testid="stVerticalBlock"] > div > div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(135deg, rgba(22, 27, 39, 0.85), rgba(10, 12, 16, 0.95)) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(0, 212, 170, 0.15) !important;
    border-radius: 16px !important;
    animation: fadeInUp 0.5s ease-out, pulseGlow 4s ease-in-out infinite;
}

/* ── Column panels ── */
[data-testid="stColumn"] {
    animation: fadeInUp 0.6s ease-out;
}
[data-testid="stColumn"]:nth-child(2) { animation-delay: 0.1s; }
[data-testid="stColumn"]:nth-child(3) { animation-delay: 0.2s; }

/* ── Primary button — gradient with glow ── */
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #00d4aa 0%, #00b894 30%, #0984e3 100%) !important;
    background-size: 200% 200% !important;
    animation: gradientShift 3s ease infinite !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    letter-spacing: 0.5px !important;
    padding: 0.75rem 2rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 20px rgba(0, 212, 170, 0.25) !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(0, 212, 170, 0.4) !important;
}

/* ── Subheaders — gradient text ── */
[data-testid="stSubheader"] {
    background: linear-gradient(90deg, #00d4aa, #0984e3, #a29bfe) !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    font-weight: 700 !important;
    font-size: 1.3rem !important;
    letter-spacing: -0.3px !important;
    padding-bottom: 8px !important;
    border-bottom: 2px solid rgba(0, 212, 170, 0.2) !important;
    margin-bottom: 16px !important;
}

/* ── Metrics — sleek cards ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(0, 212, 170, 0.06), rgba(9, 132, 227, 0.06)) !important;
    border: 1px solid rgba(0, 212, 170, 0.15) !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    animation: borderGlow 3s ease-in-out infinite;
}
[data-testid="stMetricLabel"] {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
    color: rgba(0, 212, 170, 0.7) !important;
}
[data-testid="stMetricValue"] {
    font-weight: 800 !important;
    font-size: 1.4rem !important;
    color: #e0e0e0 !important;
}

/* ── Expander — glassmorphism ── */
[data-testid="stExpander"] {
    background: rgba(22, 27, 39, 0.5) !important;
    border: 1px solid rgba(0, 212, 170, 0.1) !important;
    border-radius: 12px !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
}

/* ── Code blocks — dark glass ── */
[data-testid="stCode"] {
    background: rgba(10, 12, 16, 0.8) !important;
    border: 1px solid rgba(0, 212, 170, 0.12) !important;
    border-radius: 10px !important;
    padding: 16px !important;
}

/* ── Dividers ── */
[data-testid="stDivider"] {
    border-color: rgba(0, 212, 170, 0.12) !important;
}

/* ── Info/Success/Warning/Error boxes ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left-width: 4px !important;
    backdrop-filter: blur(10px) !important;
}

/* ── Caption text refinement ── */
[data-testid="stCaptionContainer"] {
    opacity: 0.75;
    font-size: 0.82rem !important;
    line-height: 1.5 !important;
}

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #00d4aa, #0984e3) !important;
    border-radius: 8px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0c10; }
::-webkit-scrollbar-thumb { background: rgba(0, 212, 170, 0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 212, 170, 0.5); }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="
    text-align: center;
    padding: 2rem 1rem 1.5rem 1rem;
    background: linear-gradient(135deg, rgba(0,212,170,0.08), rgba(9,132,227,0.08), rgba(162,155,254,0.05));
    border-radius: 16px;
    border: 1px solid rgba(0,212,170,0.12);
    margin-bottom: 1rem;
">
    <h1 style="
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 2.6rem;
        background: linear-gradient(135deg, #00d4aa, #0984e3, #a29bfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 0.5rem 0;
        letter-spacing: -1px;
    ">₿TC Arbitrage Scanner</h1>
    <p style="
        color: rgba(224,224,224,0.6);
        font-size: 0.9rem;
        font-weight: 400;
        margin: 0;
        letter-spacing: 1.5px;
    ">LIVE CROSS-EXCHANGE INTELLIGENCE · KALSHI × POLYMARKET · 3-AGENT AI PIPELINE · RAG: WOLFERS & ZITZEWITZ (2006)</p>
</div>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────

if "pipeline" not in st.session_state:
    st.session_state.pipeline = None

# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_price(v):
    try: return f"${float(v):.3f}"
    except: return "—"

VERDICT_MAP = {
    "EXECUTE": "green",
    "MONITOR": "orange",
    "REJECT":  "red",
    "ERROR":   "normal",
}

# ═══════════════════════════════════════════════════════════════════════════════
# RUN BUTTON
# ═══════════════════════════════════════════════════════════════════════════════

run_btn = st.button("▶ Run BTC Arbitrage Scan", type="primary", use_container_width=True)

if run_btn:
    prog_bar    = st.progress(0, text="Starting...")
    step_holder = st.empty()
    step_labels = []

    SPINNER_URL = 'data:image/svg+xml;utf8,<svg width="14" height="14" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="%2300d4aa"><style>.spinner{transform-origin:center;animation:spin .75s infinite linear}@keyframes spin{100%{transform:rotate(360deg)}}</style><path d="M12,1A11,11,0,1,0,23,12,11,11,0,0,0,12,1Zm0,19a8,8,0,1,1,8-8A8,8,0,0,1,12,20Z" opacity=".25"/><path d="M10.14,1.16a11,11,0,0,0-9,8.92A1.59,1.59,0,0,0,2.46,12,1.52,1.52,0,0,0,4.11,10.7a8,8,0,0,1,6.66-6.61A1.42,1.42,0,0,0,12,2.69h0A1.57,1.57,0,0,0,10.14,1.16Z" class="spinner"/></svg>'

    def update(step, total, label):
        step_labels.append(label)
        prog_bar.progress(int(step/total*100), text=label)
        with step_holder.container():
            for i, l in enumerate(step_labels):
                if i < len(step_labels)-1:
                    st.caption(f"✅ {l}")
                else:
                    st.markdown(f"<span style='color: #a0aab4; font-size: 14px;'><img src='{SPINNER_URL}' style='margin-right: 6px; margin-bottom: -2px;'> {l}</span>", unsafe_allow_html=True)

    try:
        results = run_pipeline(progress_callback=update)
        st.session_state.pipeline = results

        prog_bar.progress(100, text="Done")
        step_holder.empty()
        prog_bar.empty()
        st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")

# ── Stop here if no pipeline yet ──────────────────────────────────────────────

if not st.session_state.pipeline:
    st.info("Click **▶ Run BTC Arbitrage Scan** to fetch live markets and calculate edge.", icon="ℹ️")
    st.stop()

pipeline = st.session_state.pipeline
if pipeline.get("error"):
    st.error(f"Pipeline error: {pipeline['error']}", icon="❌")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

col1, col2, col3 = st.columns(3, gap="large")

# ── AGENT 1: COLLECTOR ──
with col1:
    st.subheader("🔍 Agent 1: Data Fetcher")
    c_data = pipeline.get("collector", {})
    if c_data.get("fetch_error"):
        st.error(c_data["fetch_error"])
    else:
        poly = c_data.get("polymarket", {})
        kalshi = c_data.get("kalshi", {})
        
        st.write("**Polymarket Target Event:**")
        st.caption(f"Slug: `{poly.get('slug')}`")
        st.write(f"Title: {poly.get('title')}")
        poly_strike_val = poly.get('strike', 0)
        st.write(f"Strike: **\\${poly_strike_val:,.2f}**")
        up_p = poly.get('up_price', 0)
        dn_p = poly.get('down_price', 0)
        st.text(f"Up: ${up_p:.3f} · Down: ${dn_p:.3f}")
        st.caption(f"Price Range: \\${min(up_p, dn_p):.3f} — \\${max(up_p, dn_p):.3f}")
        
        st.divider()
        st.caption("ℹ️ *Polymarket names by candle open, Kalshi by candle close. Both resolve the same hourly market.*")
        st.write("**Kalshi Target Event:**")
        st.caption(f"Ticker: `{kalshi.get('event_ticker')}`")
        
        kalshi_mkts = kalshi.get('markets', [])
        st.write(f"Active Strikes Pulled: **{len(kalshi_mkts)}**")
        
        if kalshi_mkts:
            # Show the title from the first market
            st.write(f"Title: {kalshi_mkts[0].get('title', 'N/A')}")
            
            # Find closest strike to Polymarket's strike
            poly_strike = poly.get('strike', 0)
            if poly_strike:
                closest = min(kalshi_mkts, key=lambda m: abs(m.get('strike', 0) - poly_strike))
                st.write(f"Nearest Strike: **\\${closest.get('strike', 0):,.0f}**")
                c_yes = closest.get('yes_price', 0)
                c_no = closest.get('no_price', 0)
                # If both are $1.00, the book is empty — show last_price if available
                if c_yes >= 1.0 and c_no >= 1.0:
                    st.text("Yes: N/A · No: N/A (no active orders)")
                else:
                    st.text(f"Yes: ${c_yes:.3f} · No: ${c_no:.3f}")
            
            # Strike range
            strikes = [m.get('strike', 0) for m in kalshi_mkts if m.get('strike', 0) > 0]
            if strikes:
                st.caption(f"Range: \\${min(strikes):,.0f} — \\${max(strikes):,.0f}")

# ── AGENT 2: QUANT STRATEGIST ──
with col2:
    st.subheader("📊 Agent 2: Quant Strategist")
    q_data = pipeline.get("quant", {})
    
    if q_data.get("error"):
        st.error(q_data["error"])
    elif not q_data.get("matched"):
        st.warning("No identical strike could be matched across platforms.")
    else:
        arb_found = q_data.get("arbitrage_found", False)
        
        if arb_found:
            st.success("Arbitrage Opportunity Detected!")
        else:
            st.info("No arbitrage detected at this time.")
            
        matched_strike = q_data.get('strike', 0)
        st.write(f"**Matched Strike:** \\${matched_strike:,.0f}")
        cost_str = fmt_price(q_data.get('total_cost')).replace('$', '\\$')
        st.write(f"**Total Cost of Legs:** {cost_str}")
        if arb_found:
            profit_str = fmt_price(q_data.get('guaranteed_profit')).replace('$', '\\$')
            st.write(f"**Guaranteed Profit:** :green[{profit_str}]")
            st.write("**Execution Legs:**")
            for leg in q_data.get("buy_legs", []):
                leg_price = fmt_price(leg.get('price')).replace('$', '\\$')
                st.caption(f"- Buy **{leg.get('side', '').upper()}** on {leg.get('platform', '').title()} at {leg_price}")
                
        with st.expander("Quant LLM Reasoning"):
            reasoning_text = q_data.get("reasoning", "")
            # Escape $ signs so Streamlit doesn't render them as LaTeX
            st.write(reasoning_text.replace("$", r"\$"))
        
        # ── Live Spread Equation ──
        legs = q_data.get("buy_legs", [])
        if len(legs) == 2:
            l1, l2 = legs[0], legs[1]
            l1_label = f"{l1.get('platform','').title()} {l1.get('side','').upper()}"
            l2_label = f"{l2.get('platform','').title()} {l2.get('side','').upper()}"
            l1_price = l1.get('price', 0)
            l2_price = l2.get('price', 0)
            total = q_data.get('total_cost', l1_price + l2_price)
            profit = q_data.get('guaranteed_profit', 1.0 - total)
            arb_symbol = "✅ < $1.00" if total < 1.0 else "❌ ≥ $1.00"
            
            st.divider()
            st.caption("**Live Spread Equation:**")
            pnl_label = "Guaranteed Profit" if profit >= 0 else "Guaranteed Loss"
            st.code(
                f"{l1_label} (${l1_price:.3f}) + {l2_label} (${l2_price:.3f})\n"
                f"= ${total:.4f}  {arb_symbol}\n"
                f"{pnl_label} = $1.00 - ${total:.4f} = ${profit:.4f}",
                language=None
            )

# ── AGENT 3: RISK MANAGER ──
with col3:
    st.subheader("⚖️ Agent 3: Risk Manager")
    r_data = pipeline.get("risk", {})
    
    if r_data.get("error"):
        st.error(r_data["error"])
    else:
        decision = r_data.get("final_decision", "ERROR")
        d_color = VERDICT_MAP.get(decision, "normal")
        
        st.markdown(f"### Final Verdict: :{d_color}[{decision}]")
        st.write(r_data.get("ui_summary", ""))
        st.write("**Risk Assessment:**")
        st.caption(r_data.get("risk_assessment", ""))
        st.write("**Academic Grounding (RAG):**")
        st.caption(f"📚 *{r_data.get('academic_citation', '')}*")

# ═══════════════════════════════════════════════════════════════════════════════
# QUALITY CONTROL FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.divider()

qc_metrics = pipeline.get("qc_metrics", {})
if qc_metrics:
    with st.container(border=True):
        st.write("**🔍 AI Quality Control & Validation Metrics**")
        
        m1, m2, m3, m4 = st.columns(4)
        c_succ = "✅ Passed" if qc_metrics.get("collector_success") else "❌ Failed"
        q_succ = "✅ Passed" if qc_metrics.get("quant_success") else "❌ Failed"
        r_succ = "✅ Passed" if qc_metrics.get("risk_success") else "❌ Failed"
        
        m1.metric("Total Latency", f"{qc_metrics.get('total_time_sec', 0)}s")
        m2.metric("Collector Validation", c_succ)
        m3.metric("Quant LLM Schema", q_succ)
        m4.metric("Risk LLM Schema", r_succ)
        
        st.caption("JSON Schema enforcement active. Agent workflows fully deterministic.")

st.markdown("<div style='text-align: center; color: gray; font-size: 0.8em;'>Wolfers & Zitzewitz (2006) · NBER Working Paper 12083 · Prediction Markets in Theory and Practice</div>", unsafe_allow_html=True)

with st.expander("🔧 Raw pipeline JSON"):
    st.json(pipeline)
