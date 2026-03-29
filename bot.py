#!/usr/bin/env python3
"""
Revolut UK Crypto Signal Bot
Monitors cheap cryptos on CoinGecko and sends Telegram alerts
when technical indicators suggest buy or sell opportunities.
"""

import time
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from config import (
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    SCAN_INTERVAL_SECONDS, COINS,
    RSI_OVERSOLD, RSI_OVERBOUGHT,
    ALERT_COOLDOWN_SECONDS, COINGECKO_VS_CURRENCY,
    SHOW_DISCLAIMER,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Tracks last alert time per (coin_id, direction)
alert_history: dict[tuple, float] = {}


# ── Telegram ──────────────────────────────────────────────

def send_telegram(message: str) -> None:
    """Send a message to the configured Telegram chat."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        log.error("Telegram send failed: %s", e)


# ── CoinGecko data ────────────────────────────────────────

def fetch_ohlc(coin_id: str, days: int = 7) -> pd.DataFrame | None:
    """
    Fetch OHLC candle data from CoinGecko free API.
    Retries up to 3 times on rate-limit (429) with increasing backoff.
    """
    url = (
        f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
        f"?vs_currency={COINGECKO_VS_CURRENCY}&days={days}"
    )
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 429:
                wait = 60 * (attempt + 1)
                log.warning("Rate limited on %s — waiting %ds before retry…", coin_id, wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return None
            df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close"])
            df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
            df = df.sort_values("time").reset_index(drop=True)
            return df
        except Exception as e:
            log.warning("OHLC fetch failed for %s: %s", coin_id, e)
            return None
    log.warning("Giving up on %s after 3 rate-limit retries", coin_id)
    return None


def fetch_current_price(coin_ids: list[str]) -> dict[str, float]:
    """Fetch current prices for a batch of coins in one API call."""
    ids_param = ",".join(coin_ids)
    url = (
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={ids_param}&vs_currencies={COINGECKO_VS_CURRENCY}"
        f"&include_24hr_change=true&include_24hr_vol=true"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log.warning("Price fetch failed: %s", e)
        return {}


# ── Technical indicators ──────────────────────────────────

def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calc_bollinger(series: pd.Series, period=20, std_dev=2):
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    return upper, sma, lower


def analyse(df: pd.DataFrame) -> dict:
    """
    Run all indicators on OHLC data.
    Returns a dict with indicator values and signal scores.
    """
    close = df["close"]

    rsi = calc_rsi(close)
    macd_line, signal_line, histogram = calc_macd(close)
    bb_upper, bb_mid, bb_lower = calc_bollinger(close)

    last_rsi   = rsi.iloc[-1]
    last_macd  = macd_line.iloc[-1]
    last_sig   = signal_line.iloc[-1]
    last_hist  = histogram.iloc[-1]
    prev_hist  = histogram.iloc[-2] if len(histogram) > 1 else 0
    last_close = close.iloc[-1]
    last_upper = bb_upper.iloc[-1]
    last_lower = bb_lower.iloc[-1]
    last_mid   = bb_mid.iloc[-1]

    # Score: positive = bullish, negative = bearish
    score = 0
    reasons = []

    # RSI
    if last_rsi < RSI_OVERSOLD:
        score += 2
        reasons.append(f"RSI oversold ({last_rsi:.1f})")
    elif last_rsi > RSI_OVERBOUGHT:
        score -= 2
        reasons.append(f"RSI overbought ({last_rsi:.1f})")

    # MACD crossover
    if last_hist > 0 and prev_hist <= 0:
        score += 2
        reasons.append("MACD bullish crossover")
    elif last_hist < 0 and prev_hist >= 0:
        score -= 2
        reasons.append("MACD bearish crossover")
    elif last_hist > 0:
        score += 1
        reasons.append(f"MACD positive ({last_hist:.6f})")
    elif last_hist < 0:
        score -= 1
        reasons.append(f"MACD negative ({last_hist:.6f})")

    # Bollinger Band squeeze / breakout
    if not np.isnan(last_lower) and last_close < last_lower:
        score += 1
        reasons.append("Price below lower Bollinger Band")
    elif not np.isnan(last_upper) and last_close > last_upper:
        score -= 1
        reasons.append("Price above upper Bollinger Band")

    return {
        "rsi":       last_rsi,
        "macd":      last_macd,
        "macd_hist": last_hist,
        "bb_upper":  last_upper,
        "bb_lower":  last_lower,
        "score":     score,
        "reasons":   reasons,
    }


# ── Alert logic ───────────────────────────────────────────

def should_alert(coin_id: str, direction: str) -> bool:
    key = (coin_id, direction)
    last = alert_history.get(key, 0)
    return (time.time() - last) > ALERT_COOLDOWN_SECONDS


def record_alert(coin_id: str, direction: str) -> None:
    alert_history[(coin_id, direction)] = time.time()


def build_message(
    ticker: str,
    direction: str,
    price: float,
    change_24h: float,
    analysis: dict,
) -> str:
    emoji = "🟢" if direction == "BUY" else "🔴"
    action = "BUY opportunity" if direction == "BUY" else "SELL / take profit"
    reasons_text = "\n  • ".join(analysis["reasons"]) if analysis["reasons"] else "—"

    msg = (
        f"{emoji} <b>{ticker} — {action}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Price: <b>£{price:.6g}</b>  ({change_24h:+.2f}% 24h)\n"
        f"📊 RSI: {analysis['rsi']:.1f}  |  Score: {analysis['score']:+d}\n"
        f"📝 Signals:\n  • {reasons_text}\n"
        f"🕐 {datetime.now(timezone.utc).strftime('%H:%M UTC %d %b %Y')}\n"
    )

    if SHOW_DISCLAIMER:
        msg += "\n<i>⚠️ Not financial advice. Always DYOR.</i>"

    return msg


# ── Main scan loop ────────────────────────────────────────

def scan_all() -> None:
    coin_ids = list(COINS.keys())
    log.info("Scanning %d coins…", len(coin_ids))

    # Batch-fetch current prices
    prices = fetch_current_price(coin_ids)

    for coin_id, ticker in COINS.items():
        try:
            price_data = prices.get(coin_id, {})
            current_price = price_data.get(COINGECKO_VS_CURRENCY)
            change_24h = price_data.get(f"{COINGECKO_VS_CURRENCY}_24h_change", 0.0) or 0.0

            if current_price is None:
                log.warning("No price for %s, skipping", ticker)
                continue

            df = fetch_ohlc(coin_id, days=7)
            if df is None or len(df) < 30:
                log.warning("Insufficient OHLC data for %s, skipping", ticker)
                time.sleep(3.0)   # be gentle with free API
                continue

            analysis = analyse(df)
            score = analysis["score"]

            log.info(
                "%s: £%.6g | RSI %.1f | score %+d",
                ticker, current_price, analysis["rsi"], score,
            )

            if score >= 3 and should_alert(coin_id, "BUY"):
                msg = build_message(ticker, "BUY", current_price, change_24h, analysis)
                send_telegram(msg)
                record_alert(coin_id, "BUY")
                log.info("BUY alert sent for %s", ticker)

            elif score <= -3 and should_alert(coin_id, "SELL"):
                msg = build_message(ticker, "SELL", current_price, change_24h, analysis)
                send_telegram(msg)
                record_alert(coin_id, "SELL")
                log.info("SELL alert sent for %s", ticker)

            time.sleep(6.0)   # stay within CoinGecko free-tier rate limit

        except Exception as e:
            log.error("Error processing %s: %s", ticker, e)


def main() -> None:
    log.info("Revolut UK Crypto Signal Bot starting…")
    send_telegram(
        "🤖 <b>Revolut Crypto Bot started</b>\n"
        f"Monitoring {len(COINS)} coins every {SCAN_INTERVAL_SECONDS // 60} minutes.\n"
        "You'll be notified when strong BUY or SELL signals appear."
    )

    while True:
        try:
            scan_all()
        except KeyboardInterrupt:
            log.info("Stopped by user.")
            send_telegram("🛑 <b>Revolut Crypto Bot stopped.</b>")
            break
        except Exception as e:
            log.error("Unexpected error in scan loop: %s", e)

        log.info("Sleeping %d seconds until next scan…", SCAN_INTERVAL_SECONDS)
        time.sleep(SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
