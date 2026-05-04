# ₿TC Arbitrage Scanner - Live Demonstration Script

## 1. Introduction (1 min)
* **Hook:** "Prediction markets on Kalshi and Polymarket are pricing Bitcoin every single hour — but they use different naming conventions, different strike structures, and different order books. That creates a window for risk-free arbitrage if you can compare them fast enough."
* **Value Proposition:** "We built a 3-agent AI pipeline that fetches both platforms simultaneously, runs deterministic arbitrage math via LLM tool calling, and validates every trade against academic research — all in under 20 seconds."
* **Stakeholder Value:** "This gives quantitative traders an instant, verifiable answer to the question: *is there a risk-free cross-exchange spread right now?*"

## 2. App Walkthrough & Clarity (2 mins)
* **Action:** Click "▶ Run BTC Arbitrage Scan" to initiate the pipeline.
* **Explanation:**
    * "Watch the progress bar — it runs 3 agents sequentially."
    * "**Agent 1** fetches the current hourly BTC market from Polymarket (Up/Down) and Kalshi (188 strikes). Note the reference: Polymarket names by candle open, Kalshi by candle close — both resolve the same hourly market."
    * "**Agent 2** is the Quant Strategist. It uses OpenAI function calling — the LLM calls a `calculate_arbitrage` tool that does exact Python math across all 188 Kalshi strikes. No hallucinated arithmetic."
    * "**Agent 3** retrieves academic context via RAG (Wolfers & Zitzewitz 2006) and issues a final verdict: EXECUTE, MONITOR, or REJECT."
* **Streamlining:** "One button. No settings. No configuration. Click and get your answer."

## 3. Deep Dive — The Spread Equation (1 min)
* **Action:** Point to the Live Spread Equation in Agent 2's panel.
* **Explanation:**
    * "This is the exact equation the system bases its decision on."
    * "For example: Polymarket UP ($0.43) + Kalshi NO ($0.70) = $1.13. That's above $1.00, so there's a guaranteed *loss* of $0.13 — no arbitrage."
    * "But if the cost drops below $1.00 — say $0.85 — that's a guaranteed $0.15 profit regardless of where Bitcoin ends up. Risk-free."
    * "The LLM doesn't do this math — the `calculate_arbitrage` tool does. The LLM only explains *why* the pair was optimal."

## 4. Quality Control & Validation (1 min)
* **Action:** Scroll down to the "AI Quality Control & Validation Metrics" panel.
* **Explanation:**
    * "We track four QC metrics on every run: total latency, and schema validation for each of the three agents."
    * "If the LLM hallucinates or returns malformed JSON, the system catches it immediately and falls back to the deterministic calculation."
    * "The spread equation itself is user-verifiable — you can do the addition yourself and confirm the tool got it right."
    * "This is how we prove our AI prompting works: the numbers are deterministic, the reasoning is from the LLM, and the academic grounding comes from RAG."

## 5. Academic Foundation (30 sec)
* **Action:** Point to the Wolfers & Zitzewitz citation at the bottom.
* **Explanation:** "Agent 3's RAG module retrieves context from this NBER working paper. It specifically applies the *favorite-longshot bias* — the finding that extreme-probability contracts are systematically overpriced. This prevents us from chasing false arbitrage on illiquid strikes."

## 6. Conclusion (30 sec)
* **Summary:** "To summarize: we take two platforms pricing the same Bitcoin event differently, run exact math through an LLM tool-calling pipeline, validate against academic research, and present one clear answer — all in a single click."
* **Q&A:** "Thank you. We'd be happy to take any questions."
