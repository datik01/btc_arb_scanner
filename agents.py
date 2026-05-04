"""
agents.py - Agentic Pipeline for BTC Hourly Arbitrage
Agent 1: Collector  — Fetches raw BTC hourly markets from Polymarket and Kalshi
Agent 2: Quant Strategist — Uses LLM to identify the matching strike and calculate arbitrage spread
Agent 3: Risk Manager — Reviews the strategy against RAG context and issues a final verdict
"""

import os
import json
import time
from openai import OpenAI
from rag import retrieve

# For tool calling requirement
from data_fetcher import fetch_btc_hourly_markets

# Always use OpenAI (required for tool calling in Agent 2)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"

def _llm(system: str, user: str, temperature: float = 0.3, json_mode: bool = False, max_retries: int = 3) -> str:
    import openai
    kwargs = {
        "model": MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ]
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
        
    for attempt in range(max_retries):
        try:
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content.strip()
        except openai.RateLimitError as e:
            if attempt < max_retries - 1:
                print(f"  [LLM] Rate limit hit. Retrying in 22s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(22)
            else:
                raise e
        except Exception as e:
            raise e
            
    return ""

def _parse_json(raw: str):
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)


# ══════════════════════════════════════════════════════════════════════════════
# AGENT 1: COLLECTOR
# Calls the data fetcher tool to get raw BTC hourly data
# ══════════════════════════════════════════════════════════════════════════════

def run_collector() -> dict:
    """
    Agent 1: Uses a Tool Call to fetch exact BTC hourly market data.
    """
    print("\n[Agent 1: Collector] Calling fetch_btc_hourly_markets tool...")
    t0 = time.time()
    
    # Tool Call Execution
    poly_data, kalshi_data, error = fetch_btc_hourly_markets()
    
    t1 = time.time()
    result = {
        "polymarket": poly_data,
        "kalshi": kalshi_data,
        "fetch_error": error,
        "qc": {"time_sec": round(t1 - t0, 2), "success": error == ""}
    }
    print(f"  ✅ Tool executed in {result['qc']['time_sec']}s")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# AGENT 2: QUANT STRATEGIST
# LLM with Tool Calling — uses calculate_arbitrage tool for exact math
# ══════════════════════════════════════════════════════════════════════════════

QUANT_SYSTEM = """You are an expert Quantitative Arbitrage Strategist for cross-exchange prediction market trading.

You will receive market data from Polymarket and Kalshi for Bitcoin hourly contracts.

Polymarket's market resolves relative to the 1-hour candle's OPENING price on Binance.
Kalshi's markets have fixed absolute price strikes.

You have access to a `calculate_arbitrage` tool that does exact arithmetic for you.
Call this tool with the Polymarket and Kalshi data to get precise cost calculations.

After receiving the tool result, provide your analysis as valid JSON:
{
  "matched": true,
  "strike": <kalshi_strike_from_tool>,
  "polymarket_prices": {"up": <float>, "down": <float>},
  "kalshi_prices": {"yes": <float>, "no": <float>},
  "arbitrage_found": <bool from tool>,
  "buy_legs": [
     {"platform": "polymarket", "side": "<from tool>", "price": <float>},
     {"platform": "kalshi", "side": "<from tool>", "price": <float>}
  ],
  "total_cost": <float from tool>,
  "guaranteed_profit": <float from tool>,
  "reasoning": "2-3 sentence explanation of WHY this pair is optimal and whether the spread persists."
}

CRITICAL: Use the EXACT numbers returned by the calculate_arbitrage tool. Do NOT recalculate.
"""

# Tool definition for OpenAI function calling
ARBITRAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "calculate_arbitrage",
        "description": "Calculate the optimal cross-exchange arbitrage between Polymarket and Kalshi BTC hourly markets. Iterates all Kalshi strikes and finds the pair with the lowest total cost. Returns exact arithmetic — no rounding errors.",
        "parameters": {
            "type": "object",
            "properties": {
                "poly_strike": {
                    "type": "number",
                    "description": "Polymarket strike price (Binance 1h candle open)"
                },
                "poly_up": {
                    "type": "number",
                    "description": "Polymarket Up (Yes) ask price"
                },
                "poly_down": {
                    "type": "number",
                    "description": "Polymarket Down (No) ask price"
                },
                "kalshi_strikes": {
                    "type": "array",
                    "description": "Array of Kalshi strike objects with strike, yes_price, no_price",
                    "items": {
                        "type": "object",
                        "properties": {
                            "strike": {"type": "number"},
                            "yes_price": {"type": "number"},
                            "no_price": {"type": "number"}
                        }
                    }
                }
            },
            "required": ["poly_strike", "poly_up", "poly_down", "kalshi_strikes"]
        }
    }
}


def _execute_calculate_arbitrage(poly_strike: float, poly_up: float, poly_down: float, kalshi_strikes: list) -> dict:
    """Deterministic arbitrage calculator — invoked as a tool by the LLM."""
    best = None
    for km in kalshi_strikes:
        k_strike = km.get("strike", 0)
        k_yes = km.get("yes_price", 0)
        k_no = km.get("no_price", 0)

        if k_strike == 0:
            continue

        if poly_strike > k_strike:
            cost = poly_down + k_yes
            poly_side, kalshi_side = "down", "yes"
            poly_price, kalshi_price = poly_down, k_yes
        elif poly_strike < k_strike:
            cost = poly_up + k_no
            poly_side, kalshi_side = "up", "no"
            poly_price, kalshi_price = poly_up, k_no
        else:
            cost1, cost2 = poly_down + k_yes, poly_up + k_no
            if cost1 <= cost2:
                cost = cost1
                poly_side, kalshi_side = "down", "yes"
                poly_price, kalshi_price = poly_down, k_yes
            else:
                cost = cost2
                poly_side, kalshi_side = "up", "no"
                poly_price, kalshi_price = poly_up, k_no

        if best is None or cost < best["total_cost"]:
            best = {
                "kalshi_strike": k_strike,
                "total_cost": round(cost, 4),
                "guaranteed_profit": round(1.0 - cost, 4),
                "arbitrage_found": cost < 1.0,
                "poly_side": poly_side,
                "poly_price": round(poly_price, 4),
                "kalshi_side": kalshi_side,
                "kalshi_price": round(kalshi_price, 4),
                "kalshi_yes": k_yes,
                "kalshi_no": k_no,
            }

    if not best:
        return {"error": "No valid strikes", "arbitrage_found": False}
    return best


def run_quant_strategist(collector_output: dict) -> dict:
    """Agent 2: LLM with tool calling for exact arbitrage math."""
    print("\n[Agent 2: Quant Strategist] LLM with calculate_arbitrage tool...")

    if collector_output.get("fetch_error"):
        print("  ⚠ Skipping Agent 2 due to Agent 1 fetch error.")
        return {"matched": False, "error": collector_output["fetch_error"]}

    poly = collector_output.get("polymarket")
    kalshi = collector_output.get("kalshi")

    if not poly or not kalshi:
        return {"matched": False, "error": "Missing platform data"}

    poly_strike = poly.get("strike")
    poly_up = poly.get("up_price", 0)
    poly_down = poly.get("down_price", 0)
    kalshi_markets = kalshi.get("markets", [])

    if not poly_strike or not kalshi_markets:
        return {"matched": False, "error": "Missing strike or Kalshi markets"}

    # Pre-filter to 15 closest strikes to keep context manageable
    kalshi_filtered = sorted(kalshi_markets, key=lambda m: abs(m.get("strike", 0) - poly_strike))[:15]

    t0 = time.time()

    user_msg = f"""Here is the live market data. Use the calculate_arbitrage tool to find the optimal pair.

Polymarket: strike=${poly_strike:,.2f}, up=${poly_up:.3f}, down=${poly_down:.3f}
Kalshi strikes (15 closest): {json.dumps([{"strike": m["strike"], "yes_price": m.get("yes_price",0), "no_price": m.get("no_price",0)} for m in kalshi_filtered])}

Call the tool now, then analyze the result."""

    import openai
    try:
        # Step 1: LLM decides to call the tool
        messages = [
            {"role": "system", "content": QUANT_SYSTEM},
            {"role": "user", "content": user_msg}
        ]

        for attempt in range(3):
            try:
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=[ARBITRAGE_TOOL],
                    tool_choice={"type": "function", "function": {"name": "calculate_arbitrage"}},
                    temperature=0.1
                )
                break
            except openai.RateLimitError:
                if attempt < 2:
                    print(f"  [LLM] Rate limit hit. Retrying in 22s... (Attempt {attempt+1}/3)")
                    time.sleep(22)
                else:
                    raise

        msg = resp.choices[0].message

        # Step 2: Execute the tool with the LLM's arguments
        tool_result = None
        if msg.tool_calls:
            tc = msg.tool_calls[0]
            args = json.loads(tc.function.arguments)
            print(f"  🔧 Tool called: calculate_arbitrage(poly_strike={args.get('poly_strike')}, ...)")

            tool_result = _execute_calculate_arbitrage(
                poly_strike=args.get("poly_strike", poly_strike),
                poly_up=args.get("poly_up", poly_up),
                poly_down=args.get("poly_down", poly_down),
                kalshi_strikes=args.get("kalshi_strikes", kalshi_filtered)
            )
            print(f"  ✅ Tool result: cost=${tool_result.get('total_cost', '?')}, arb={tool_result.get('arbitrage_found', '?')}")

            # Step 3: Feed tool result back to LLM for reasoning
            messages.append(msg.model_dump())
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(tool_result)
            })

            for attempt in range(3):
                try:
                    resp2 = client.chat.completions.create(
                        model=MODEL,
                        messages=messages,
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    break
                except openai.RateLimitError:
                    if attempt < 2:
                        print(f"  [LLM] Rate limit hit. Retrying in 22s... (Attempt {attempt+1}/3)")
                        time.sleep(22)
                    else:
                        raise

            raw = resp2.choices[0].message.content.strip()
            parsed = _parse_json(raw)
        else:
            # LLM didn't call tool — fallback to direct calculation
            print("  ⚠ LLM skipped tool call. Running calculate_arbitrage directly.")
            tool_result = _execute_calculate_arbitrage(poly_strike, poly_up, poly_down, kalshi_filtered)
            parsed = {}

        t1 = time.time()

        # ─── Enforce correct values from the tool (override any LLM hallucination) ───
        if tool_result and "error" not in tool_result:
            parsed["matched"] = True
            parsed["strike"] = tool_result["kalshi_strike"]
            parsed["polymarket_prices"] = {"up": poly_up, "down": poly_down}
            parsed["kalshi_prices"] = {"yes": tool_result["kalshi_yes"], "no": tool_result["kalshi_no"]}
            parsed["arbitrage_found"] = tool_result["arbitrage_found"]
            parsed["buy_legs"] = [
                {"platform": "polymarket", "side": tool_result["poly_side"], "price": tool_result["poly_price"]},
                {"platform": "kalshi", "side": tool_result["kalshi_side"], "price": tool_result["kalshi_price"]}
            ]
            parsed["total_cost"] = tool_result["total_cost"]
            parsed["guaranteed_profit"] = tool_result["guaranteed_profit"]
        else:
            parsed.setdefault("matched", False)

        parsed.setdefault("reasoning", "")
        parsed["qc"] = {"time_sec": round(t1 - t0, 2), "success": True}
        print(f"  ✅ Best pair: Kalshi ${parsed.get('strike', 0):,.0f} | Cost: ${parsed.get('total_cost', 0):.4f} | Arb: {parsed.get('arbitrage_found')}")
        return parsed

    except Exception as e:
        print(f"  ⚠ Agent 2 Error: {e}")
        # Ultimate fallback: run tool directly without LLM
        tool_result = _execute_calculate_arbitrage(poly_strike, poly_up, poly_down, kalshi_filtered)
        t1 = time.time()
        if tool_result and "error" not in tool_result:
            return {
                "matched": True,
                "strike": tool_result["kalshi_strike"],
                "polymarket_prices": {"up": poly_up, "down": poly_down},
                "kalshi_prices": {"yes": tool_result["kalshi_yes"], "no": tool_result["kalshi_no"]},
                "arbitrage_found": tool_result["arbitrage_found"],
                "buy_legs": [
                    {"platform": "polymarket", "side": tool_result["poly_side"], "price": tool_result["poly_price"]},
                    {"platform": "kalshi", "side": tool_result["kalshi_side"], "price": tool_result["kalshi_price"]}
                ],
                "total_cost": tool_result["total_cost"],
                "guaranteed_profit": tool_result["guaranteed_profit"],
                "reasoning": f"Direct calculation (LLM error: {e})",
                "qc": {"time_sec": round(t1 - t0, 2), "success": True}
            }
        return {"matched": False, "error": str(e), "qc": {"time_sec": round(time.time() - t0, 2), "success": False}}


# ══════════════════════════════════════════════════════════════════════════════
# AGENT 3: RISK MANAGER
# Uses RAG to evaluate the Quant's proposed trade against academic principles
# ══════════════════════════════════════════════════════════════════════════════

RISK_SYSTEM = """
You are a Risk Management Agent for a prediction market trading firm.
You evaluate proposed arbitrage strategies against academic research.

You will receive:
1. The Quant Strategist's proposed trade (JSON) — the numbers (total_cost, guaranteed_profit) have been computed by a deterministic calculation tool and are VERIFIED CORRECT. Do NOT question the arithmetic.
2. Academic Context retrieved via RAG (Wolfers & Zitzewitz 2006).

Your job:
- If `arbitrage_found` is true AND `guaranteed_profit` > 0.02 (2 cents): Recommend EXECUTE, but note fee drag (~3-7% on Kalshi) and latency risk.
- If `arbitrage_found` is true BUT `guaranteed_profit` <= 0.02: Recommend MONITOR — the edge is real but too thin after fees.
- If `arbitrage_found` is false: Recommend MONITOR or REJECT depending on how far from breakeven.
- Apply the favorite-longshot bias from academic context only to extreme-probability contracts (< 0.10 or > 0.90).

Return ONLY valid JSON in this exact format:
{
  "final_decision": "EXECUTE|REJECT|MONITOR",
  "risk_assessment": "1-2 sentences explaining your decision based on the RAG context and fee analysis.",
  "academic_citation": "Quote or reference the specific academic principle driving your decision.",
  "ui_summary": "A clean, concise 2-sentence summary of the current market state for the user dashboard."
}
"""

def run_risk_manager(quant_output: dict) -> dict:
    print("\n[Agent 3: Risk Manager] Retrieving academic context via RAG...")
    t0 = time.time()
    
    # RAG Execution
    rag_context = retrieve(
        "prediction market arbitrage fees spread exploitable favorite longshot bias latency",
        top_n=3
    )
    
    user_msg = f"""
Academic Context (RAG):
{rag_context}

Proposed Strategy from Quant Agent:
{json.dumps(quant_output, indent=2)}

Evaluate the strategy and return your final decision.
"""
    try:
        raw = _llm(RISK_SYSTEM, user_msg, temperature=0.3, json_mode=True)
        t1 = time.time()
        parsed = _parse_json(raw)
        parsed["qc"] = {"time_sec": round(t1 - t0, 2), "success": True}
        print(f"  ✅ Risk verdict: {parsed.get('final_decision')}")
        return parsed
    except Exception as e:
        print(f"  ⚠ Agent 3 Error: {e}")
        return {"final_decision": "ERROR", "error": str(e), "qc": {"time_sec": round(time.time() - t0, 2), "success": False}}


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline(progress_callback=None) -> dict:
    """Runs Agent 1 → Agent 2 → Agent 3 sequentially for BTC Hourly Arbitrage."""
    results = {"collector": None, "quant": None, "risk": None, "error": None}
    total = 3

    try:
        t_start = time.time()
        if progress_callback: progress_callback(1, total, "🔍 Agent 1: Collecting exact BTC hourly markets...")
        results["collector"] = run_collector()

        if progress_callback: progress_callback(2, total, "📊 Agent 2: Quant analyzing strikes and calculating spreads...")
        results["quant"] = run_quant_strategist(results["collector"])

        if progress_callback: progress_callback(3, total, "⚖️ Agent 3: Risk Manager reviewing against academic RAG context...")
        results["risk"] = run_risk_manager(results["quant"])
        
        t_end = time.time()
        
        # Aggregate QC
        c_qc = results["collector"].get("qc", {})
        q_qc = results["quant"].get("qc", {})
        r_qc = results["risk"].get("qc", {})
        
        results["qc_metrics"] = {
            "total_time_sec": round(t_end - t_start, 2),
            "collector_success": c_qc.get("success", False),
            "quant_success": q_qc.get("success", False),
            "risk_success": r_qc.get("success", False)
        }

    except Exception as e:
        results["error"] = str(e)
        print(f"[Pipeline Error] {e}")

    return results

if __name__ == "__main__":
    print("Testing BTC Pipeline...")
    res = run_pipeline()
    print("\nFINAL PIPELINE RESULT:")
    print(json.dumps(res, indent=2))
