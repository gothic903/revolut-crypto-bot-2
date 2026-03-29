# ============================================================
# config.py — Revolut UK Crypto Signal Bot 2 Configuration
# ============================================================

# ------- Telegram Setup ------------------------------------
TELEGRAM_BOT_TOKEN = "8617534944:AAGhDCGlndaH3qE7NHBJ2s1-6w5XOq_rcR4"
TELEGRAM_CHAT_ID   = "8645569215"

# ------- Scan Interval ------------------------------------
SCAN_INTERVAL_SECONDS = 60    # 1 minute between full scans

# ------- Coins to Monitor (Binance symbols) ---------------
COINS = {
    "ZRXUSDT":   "ZRX",
    "1INCHUSDT": "1INCH",
    "AXSUSDT":   "AXS",
    "BALUSDT":   "BAL",
    "BANDUSDT":  "BAND",
    "BICOUSDT":  "BICO",
    "COMPUSDT":  "COMP",
    "ATOMUSDT":  "ATOM",
    "CRVUSDT":   "CRV",
    "ETCUSDT":   "ETC",
    "FETUSDT":   "FET",
    "FILUSDT":   "FIL",
    "IMXUSDT":   "IMX",
    "KNCUSDT":   "KNC",
    "LPTUSDT":   "LPT",
    "MASKUSDT":  "MASK",
    "MATICUSDT": "MATIC",
    "OGNUSDT":   "OGN",
    "PERPUSDT":  "PERP",
    "DOTUSDT":   "DOT",
    "RADUSDT":   "RAD",
    "RENUSDT":   "REN",
    "SPELLUSDT": "SPELL",
    "GMTUSDT":   "GMT",
    "SUSHIUSDT": "SUSHI",
    "SNXUSDT":   "SNX",
    "UNIUSDT":   "UNI",
    "APEUSDT":   "APE",
    "UMAUSDT":   "UMA",
}

# ------- Signal Thresholds --------------------------------
RSI_OVERSOLD    = 30
RSI_OVERBOUGHT  = 70

ALERT_COOLDOWN_SECONDS = 3600   # 1 hour

# ------- Risk Disclaimer ----------------------------------
SHOW_DISCLAIMER = True
