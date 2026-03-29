# ============================================================
# config.py — Revolut UK Crypto Signal Bot 2 Configuration
# ============================================================

# ------- Telegram Setup ------------------------------------
TELEGRAM_BOT_TOKEN = "8617534944:AAGhDCGlndaH3qE7NHBJ2s1-6w5XOq_rcR4"
TELEGRAM_CHAT_ID   = "8645569215"

# ------- Scan Interval ------------------------------------
SCAN_INTERVAL_SECONDS = 300   # 5 minutes between full scans

# ------- Cheap Revolut UK Coins to Monitor (Batch 2) ------
# No overlap with Bot 1
COINS = {
    "zrx":                        "ZRX",
    "1inch":                      "1INCH",
    "axie-infinity":              "AXS",
    "balancer":                   "BAL",
    "band-protocol":              "BAND",
    "biconomy":                   "BICO",
    "compound-governance-token":  "COMP",
    "cosmos":                     "ATOM",
    "curve-dao-token":            "CRV",
    "ethereum-classic":           "ETC",
    "fetch-ai":                   "FET",
    "filecoin":                   "FIL",
    "immutable-x":                "IMX",
    "kyber-network-crystal":      "KNC",
    "livepeer":                   "LPT",
    "mask-network":               "MASK",
    "matic-network":              "MATIC",
    "origin-protocol":            "OGN",
    "perpetual-protocol":         "PERP",
    "polkadot":                   "DOT",
    "radicle":                    "RAD",
    "republic-protocol":          "REN",
    "spell-token":                "SPELL",
    "stepn":                      "GMT",
    "sushi":                      "SUSHI",
    "havven":                     "SNX",
    "uniswap":                    "UNI",
    "apecoin":                    "APE",
    "uma":                        "UMA",
}

# ------- Signal Thresholds --------------------------------
RSI_OVERSOLD    = 30
RSI_OVERBOUGHT  = 70

ALERT_COOLDOWN_SECONDS = 3600   # 1 hour

# ------- CoinGecko API ------------------------------------
COINGECKO_API_KEY     = "CG-srBknQUrDV3RQ5WrNgEQ1d82"
COINGECKO_VS_CURRENCY = "gbp"

# ------- Risk Disclaimer ----------------------------------
SHOW_DISCLAIMER = True
