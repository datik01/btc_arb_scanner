"""
data_fetcher.py
Fetches live BTC hourly market data from Kalshi and Polymarket.
"""

import os
import requests
import datetime
import pytz
from typing import Optional, Dict, Any, Tuple

POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"
POLYMARKET_CLOB_URL = "https://clob.polymarket.com/book"
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"

def get_target_times() -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Returns the target times for Polymarket and Kalshi.
    
    IMPORTANT: The platforms name the SAME candle differently:
    - Polymarket names by the candle OPEN:  "11PM" = candle opens at 11PM
    - Kalshi names by the candle CLOSE:     "12AM" = candle closes at midnight
    Both refer to the 11PM→midnight candle.
    
    So Kalshi target = Polymarket target + 1 hour.
    """
    now = datetime.datetime.now(pytz.utc)
    poly_target = now.replace(minute=0, second=0, microsecond=0)    # open hour
    kalshi_target = poly_target + datetime.timedelta(hours=1)        # close hour
    return poly_target, kalshi_target

def get_poly_btc_slug(target_time: datetime.datetime) -> str:
    """Generate Polymarket slug for hourly BTC market."""
    et_tz = pytz.timezone('US/Eastern')
    if target_time.tzinfo is None:
        target_time = pytz.utc.localize(target_time).astimezone(et_tz)
    else:
        target_time = target_time.astimezone(et_tz)

    month = target_time.strftime("%B").lower()
    day = target_time.day
    year = target_time.year
    hour_int = int(target_time.strftime("%I"))
    am_pm = target_time.strftime("%p").lower()
    
    return f"bitcoin-up-or-down-{month}-{day}-{year}-{hour_int}{am_pm}-et"

def get_kalshi_btc_ticker(target_time: datetime.datetime) -> str:
    """Generate Kalshi event ticker for hourly BTC market."""
    et_tz = pytz.timezone('US/Eastern')
    if target_time.tzinfo is None:
        target_time = pytz.utc.localize(target_time).astimezone(et_tz)
    else:
        target_time = target_time.astimezone(et_tz)

    year = target_time.strftime("%y")
    month = target_time.strftime("%b").upper()
    day = target_time.strftime("%d")
    hour = target_time.strftime("%H")
    
    return f"KXBTCD-{year}{month}{day}{hour}"

def get_poly_clob_price(token_id: str) -> Optional[float]:
    """Fetch best ask price from Polymarket CLOB."""
    try:
        r = requests.get(POLYMARKET_CLOB_URL, params={"token_id": token_id})
        r.raise_for_status()
        data = r.json()
        asks = data.get('asks', [])
        if asks:
            best_ask = min(float(a['price']) for a in asks)
            return best_ask if best_ask > 0 else 0.0
        return 0.0
    except Exception:
        return None

def get_binance_open_price(target_time_utc: datetime.datetime) -> Optional[float]:
    """Fetch the opening price of the 1h Binance candle for the target time."""
    try:
        timestamp_ms = int(target_time_utc.timestamp() * 1000)
        params = {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "startTime": timestamp_ms,
            "limit": 1
        }
        r = requests.get("https://api.binance.us/api/v3/klines", params=params)
        r.raise_for_status()
        data = r.json()
        if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            return float(data[0][1])
    except Exception as e:
        print(f"Error fetching Binance open price: {e}")
    return None

def fetch_polymarket_btc(target_time: datetime.datetime) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Fetch Polymarket hourly BTC data."""
    slug = get_poly_btc_slug(target_time)
    try:
        r = requests.get(POLYMARKET_API_URL, params={"slug": slug})
        r.raise_for_status()
        data = r.json()
        if not data:
            return None, "Event not found"

        event = data[0]
        markets = event.get("markets", [])
        if not markets:
            return None, "Markets not found"

        market = markets[0]
        clob_token_ids = eval(market.get("clobTokenIds", "[]"))
        outcomes = eval(market.get("outcomes", "[]"))
        title = market.get("question", "")

        # For Polymarket Up/Down, the strike is the candle's open price
        strike = get_binance_open_price(target_time)

        if len(clob_token_ids) != 2:
            return None, "Unexpected number of tokens"

        prices = {}
        for outcome, token_id in zip(outcomes, clob_token_ids):
            price = get_poly_clob_price(token_id)
            prices[outcome] = price if price is not None else 0.0

        return {
            "platform": "polymarket",
            "slug": slug,
            "title": title,
            "strike": strike,
            "up_price": prices.get("Yes", prices.get("Up", 0.0)),
            "down_price": prices.get("No", prices.get("Down", 0.0))
        }, None
    except Exception as e:
        return None, str(e)

def fetch_kalshi_btc(target_time: datetime.datetime) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Fetch Kalshi hourly BTC data."""
    event_ticker = get_kalshi_btc_ticker(target_time)
    try:
        r = requests.get(f"{KALSHI_BASE}/events/{event_ticker}")
        r.raise_for_status()
        data = r.json()
        
        # We need the market specifically
        r_mkts = requests.get(f"{KALSHI_BASE}/markets", params={"event_ticker": event_ticker})
        r_mkts.raise_for_status()
        mkts_data = r_mkts.json().get("markets", [])
        
        if not mkts_data:
            return None, "No active markets found for event"
            
        # For BTC daily/hourly, there might be multiple strikes. We want the one closest to current price, 
        # or we just return the list of markets and let the agent calculate against Polymarket's strike.
        import re
        kalshi_markets = []
        for m in mkts_data:
            # Extract strike from subtitle (e.g. "$69,500 or above")
            strike = 0.0
            if "strike" in m and m["strike"]:
                strike = float(m["strike"])
            else:
                sub = m.get("subtitle", "")
                match = re.search(r'\$[\d,]+', sub)
                if match:
                    strike = float(match.group(0).replace('$', '').replace(',', ''))
                    
            kalshi_markets.append({
                "strike": strike,
                "yes_price": float(m.get("yes_ask_dollars", 0) or m.get("yes_ask", 0) / 100),
                "no_price": float(m.get("no_ask_dollars", 0) or m.get("no_ask", 0) / 100),
                "title": m.get("title", ""),
                "ticker": m.get("ticker", "")
            })
            
        return {
            "platform": "kalshi",
            "event_ticker": event_ticker,
            "markets": kalshi_markets
        }, None
    except Exception as e:
        return None, str(e)

def fetch_btc_hourly_markets() -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], str]:
    """Fetch matching BTC hourly markets from both platforms."""
    poly_target, kalshi_target = get_target_times()
    
    poly_data, poly_err = fetch_polymarket_btc(poly_target)
    kalshi_data, kalshi_err = fetch_kalshi_btc(kalshi_target)
    
    err_msg = ""
    if poly_err: err_msg += f"Poly Error: {poly_err}. "
    if kalshi_err: err_msg += f"Kalshi Error: {kalshi_err}. "
    
    return poly_data, kalshi_data, err_msg.strip()

if __name__ == "__main__":
    print("Testing BTC Hourly Fetch...")
    p, k, e = fetch_btc_hourly_markets()
    if e:
        print("ERRORS:", e)
    if p:
        print("POLYMARKET:", p)
    if k:
        print("KALSHI MKTS:", len(k.get("markets", [])))
