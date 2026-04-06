import os

FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "choker2024")

# Watchlist par défaut (dashboard principal)
WATCHLIST = ["AAPL", "TSLA", "AMZN", "MSFT", "BTC-USD", "NVDA", "GOOGL", "META"]

# Watchlist étendue par catégorie
WATCHLIST_CATEGORIES = {
    "Tech": [
        "AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "INTC",
        "TSLA", "UBER", "SNAP", "SPOT", "NFLX", "AMZN", "CRM",
        "ORCL", "ADBE", "QCOM", "MU", "AVGO", "TSM"
    ],
    "Tendance": [
        "PLTR", "RBLX", "COIN", "GME", "AMC", "RIVN", "LCID",
        "SOFI", "HOOD", "OPEN", "CLOV", "SPCE", "BBBY", "WKHS"
    ],
    "Crypto": [
        "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "ADA-USD",
        "DOGE-USD", "XRP-USD", "MATIC-USD", "DOT-USD", "AVAX-USD",
        "LINK-USD", "LTC-USD", "UNI7083-USD", "ATOM-USD"
    ],
    "ETF": [
        "SPY", "QQQ", "VTI", "ARKK", "VOO", "IWM", "DIA",
        "GLD", "SLV", "TLT", "HYG", "XLK", "XLF", "XLE"
    ],
    "Europe": [
        "LVMH.PA", "TTE.PA", "AIR.PA", "SAN.PA", "BNP.PA",
        "SAP.DE", "ASML.AS", "NESN.SW", "ROG.SW", "NOVN.SW",
        "SIE.DE", "ALV.DE", "BMW.DE", "VOW3.DE",
        "INGA.AS", "PHIA.AS", "HEIA.AS", "UNA.AS", "RDSA.AS"
    ],
    "BEL20": [
        "ABI.BR", "AGS.BR", "APAM.BR", "ARGX.BR", "COLR.BR",
        "ELI.BR", "GBLB.BR", "KBC.BR", "LOTB.BR", "PROX.BR",
        "SOLB.BR", "UCB.BR", "WDP.BR", "BPOST.BR", "BELG.BR"
    ],
    "Chine": [
        "BABA", "NIO", "XPEV", "LI", "JD", "PDD", "BIDU",
        "NTES", "TME", "IQ"
    ],
}

CHECK_INTERVAL_MINUTES = 15
ALERT_THRESHOLD = 7
