# ₿TC Arbitrage Scanner - TOOL3 Assignment Submission

## Links
* **GitHub Repository:** https://github.com/datik01/btc_arb_scanner
* **Live App (DigitalOcean/Posit Connect):** [Insert your deployed app link here]
* **Presentation Materials / Video:** [Insert link to your presentation slides or video here]

---

## 1. Stakeholder Alignment
**Does it solve a real problem for your stakeholders?**
Yes. Quantitative researchers and retail traders need to identify cross-exchange arbitrage opportunities in Bitcoin prediction markets before they disappear. Kalshi and Polymarket price the same hourly BTC event using different naming conventions and strike structures, making manual comparison impractical across 188+ strike levels. Our app automates this by fetching live data from both platforms, running deterministic arbitrage math via an LLM tool-calling pipeline, and validating the result against academic research (Wolfers & Zitzewitz, 2006) — all in under 20 seconds.

## 2. Clarity & Streamlining
**Does a user really know what to do with the tool? Are unnecessary features removed?**
Yes. The app is a single-page dashboard with one clear action: "▶ Run BTC Arbitrage Scan". No configuration, no dropdowns, no settings. The user clicks the button and receives a 3-panel result:
- **Agent 1** shows what was fetched (Polymarket Up/Down, Kalshi 188 strikes, Binance strike)
- **Agent 2** shows the optimal pair, the live spread equation, and whether an arbitrage exists
- **Agent 3** shows the risk verdict (EXECUTE / REJECT / MONITOR) grounded in academic context

A reference note clarifies that both platforms resolve the same hourly market despite different naming conventions.

## 3. Efficiency & Reliability
**Is the app fast and consistent?**
Yes. The pipeline runs 3 agents sequentially in ~15-20 seconds. Agent 2 uses **OpenAI function calling** with a `calculate_arbitrage` tool — the LLM calls the tool, the tool does exact Python math, and the result is fed back for reasoning. This eliminates LLM arithmetic hallucinations while maintaining the agentic tool-calling loop. All agents have retry logic (3 attempts with 22s backoff for rate limits) and graceful fallbacks — if the LLM fails entirely, the deterministic calculation still runs.

## 4. Quality Control and Validation
**Evidence that your AI prompting works effectively:**
We implemented an embedded **"AI Quality Control & Validation Metrics"** panel at the bottom of the dashboard. This panel dynamically tracks:
* **Total Latency** — End-to-end pipeline execution time
* **Collector Validation** — Both Polymarket and Kalshi APIs returned valid market data
* **Quant LLM Schema** — Agent 2 returned valid JSON with the correct fields (matched, strike, buy_legs, total_cost)
* **Risk LLM Schema** — Agent 3 returned valid JSON with a final_decision and academic citation

Additionally, the **Live Spread Equation** display shows the exact arithmetic the decision is based on, allowing the user to independently verify the calculation. The deterministic `calculate_arbitrage` tool guarantees correct math regardless of LLM behavior.

## 5. Agentic Loop
**Design of the agentic loop:**
The pipeline implements a 3-agent agentic loop with tool calling:
1. **Agent 1 (Data Fetcher)** → Fetches raw data from Polymarket CLOB, Kalshi Trade API, and Binance
2. **Agent 2 (Quant Strategist)** → LLM receives data, calls `calculate_arbitrage` tool, receives exact result, generates reasoning
3. **Agent 3 (Risk Manager)** → Retrieves academic context via RAG (Wolfers & Zitzewitz 2006), evaluates the trade, issues verdict

Agent 2's tool-calling flow is a true agentic loop: the LLM decides what parameters to pass → calls the tool → receives the result → reasons about it → produces structured output.

---

*(Note: Copy this content into your single `.docx` file for submission on Canvas!)*
