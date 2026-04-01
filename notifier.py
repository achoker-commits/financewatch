import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram(message):
    """Envoie une alerte Telegram."""
    if TELEGRAM_BOT_TOKEN == "TON_TOKEN_TELEGRAM":
        print(f"[TELEGRAM NON CONFIGURÉ] {message}")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erreur Telegram: {e}")

def format_alert(symbol, news, analysis):
    """Formate le message d'alerte."""
    emoji_sentiment = {"HAUSSIER": "📈", "BAISSIER": "📉", "NEUTRE": "➡️"}
    emoji_conseil = {"ACHETER": "🟢", "VENDRE": "🔴", "ATTENDRE": "🟡"}
    emoji_urgence = {"HAUTE": "🚨", "MOYENNE": "⚠️", "FAIBLE": "ℹ️"}

    sentiment = analysis.get("sentiment", "NEUTRE")
    conseil = analysis.get("conseil", "ATTENDRE")
    urgence = analysis.get("urgence", "FAIBLE")

    return f"""
{emoji_urgence[urgence]} <b>ALERTE FINANCEWATCH — {symbol}</b>

📰 <b>News:</b> {news['headline']}

{emoji_sentiment[sentiment]} <b>Sentiment:</b> {sentiment}
{emoji_conseil[conseil]} <b>Conseil:</b> {conseil}
⭐ <b>Confiance:</b> {analysis.get('confiance', '?')}/10

💬 {analysis.get('raison', '')}

🕐 {news.get('datetime', '')}
"""
