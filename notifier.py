import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN:
        print(f"[TELEGRAM NON CONFIGURE] {message}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Erreur Telegram: {e}")

def format_alert(symbol, news, analysis):
    e_s = {"HAUSSIER": "📈", "BAISSIER": "📉", "NEUTRE": "➡️"}
    e_c = {"ACHETER": "🟢", "VENDRE": "🔴", "ATTENDRE": "🟡"}
    e_u = {"HAUTE": "🚨", "MOYENNE": "⚠️", "FAIBLE": "ℹ️"}
    s = analysis.get('sentiment', 'NEUTRE')
    c = analysis.get('conseil', 'ATTENDRE')
    u = analysis.get('urgence', 'FAIBLE')
    return f"{e_u[u]} <b>ALERTE FINANCEWATCH — {symbol}</b>\n\n📰 <b>News:</b> {news['headline']}\n\n{e_s[s]} <b>Sentiment:</b> {s}\n{e_c[c]} <b>Conseil:</b> {c}\n⭐ <b>Confiance:</b> {analysis.get('confiance','?')}/10\n\n💬 {analysis.get('raison','')}\n\n🕐 {news.get('datetime','')}"
