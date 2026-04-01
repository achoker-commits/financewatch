import requests
import yfinance as yf

def calculate_rsi(prices, period=14):
    """Calcule le RSI (Relative Strength Index) sur une liste de prix."""
    if len(prices) < period + 1:
        return None
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)

def interpret_rsi(rsi):
    """Interprète le RSI pour un débutant."""
    if rsi is None:
        return "Données insuffisantes", "neutral"
    if rsi >= 70:
        return f"RSI {rsi} — Suracheté (action peut-être trop chère, correction possible)", "danger"
    if rsi >= 60:
        return f"RSI {rsi} — Tendance haussière forte", "warning"
    if rsi >= 40:
        return f"RSI {rsi} — Zone neutre, pas de signal clair", "neutral"
    if rsi >= 30:
        return f"RSI {rsi} — Tendance baissière", "warning"
    return f"RSI {rsi} — Survendu (action peut-être pas chère, rebond possible)", "success"

def get_technical_indicators(symbol):
    """Retourne RSI + moyennes mobiles pour un symbole."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="60d")
        if hist.empty or len(hist) < 20:
            return None

        closes = [round(p, 2) for p in hist['Close'].tolist()]
        current = closes[-1]

        rsi = calculate_rsi(closes)
        rsi_text, rsi_status = interpret_rsi(rsi)

        sma20 = round(sum(closes[-20:]) / 20, 2)
        sma50 = round(sum(closes[-50:]) / 50, 2) if len(closes) >= 50 else None

        if current > sma20:
            trend = "Au-dessus de la moyenne 20j — tendance haussière court terme"
            trend_status = "success"
        else:
            trend = "En-dessous de la moyenne 20j — tendance baissière court terme"
            trend_status = "danger"

        return {
            "symbol": symbol,
            "current": current,
            "rsi": rsi,
            "rsi_text": rsi_text,
            "rsi_status": rsi_status,
            "sma20": sma20,
            "sma50": sma50,
            "trend": trend,
            "trend_status": trend_status,
        }
    except Exception as e:
        return None

def get_fear_and_greed():
    """Récupère le Fear & Greed Index de CNN."""
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        score = data.get("fear_and_greed", {}).get("score", 50)
        rating = data.get("fear_and_greed", {}).get("rating", "Neutral")
        score = round(float(score), 1)

        if score <= 25:
            emoji = "😱"
            conseil = "Peur extrême — historiquement bon moment pour acheter (mais risqué)"
            color = "#ef4444"
        elif score <= 45:
            emoji = "😰"
            conseil = "Peur — les marchés sont nerveux, sois prudent"
            color = "#f97316"
        elif score <= 55:
            emoji = "😐"
            conseil = "Neutre — pas de signal particulier"
            color = "#eab308"
        elif score <= 75:
            emoji = "😊"
            conseil = "Avidité — les marchés sont optimistes"
            color = "#84cc16"
        else:
            emoji = "🤑"
            conseil = "Avidité extrême — attention, bulle possible"
            color = "#22c55e"

        return {
            "score": score,
            "rating": rating,
            "emoji": emoji,
            "conseil": conseil,
            "color": color
        }
    except Exception:
        return {
            "score": 50,
            "rating": "Neutral",
            "emoji": "😐",
            "conseil": "Données indisponibles",
            "color": "#eab308"
        }
