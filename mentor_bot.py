import requests
import threading
from educator import repondre_question
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

last_update_id = 0

def send_telegram(message, parse_mode="HTML"):
    """Envoie un message Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": parse_mode}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erreur Telegram: {e}")

def get_updates():
    """Récupère les messages envoyés au bot."""
    global last_update_id
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    try:
        r = requests.get(url, params={"offset": last_update_id + 1, "timeout": 10}, timeout=15)
        return r.json().get("result", [])
    except Exception:
        return []

def handle_message(text):
    """Traite un message entrant et répond."""
    text = text.strip().lower()

    if text in ["/start", "bonjour", "salut", "hello"]:
        return """👋 <b>Bienvenue sur FinanceWatch AI !</b>

Je suis ton mentor financier personnel. Je suis là pour t'apprendre la finance et t'aider à prendre de meilleures décisions.

<b>Ce que tu peux me demander :</b>
• /lecon → Leçon du jour
• /prix → Prix de tes actions
• /analyse → Dernières analyses
• /risque → Score de risque global
• Ou pose-moi n'importe quelle question !

Ex: <i>"C'est quoi un ETF ?"</i> ou <i>"Est-ce que Tesla est risqué ?"</i>"""

    if text in ["/lecon", "lecon", "leçon"]:
        from educator import get_lecon_du_jour
        concept, lecon = get_lecon_du_jour()
        return f"🎓 <b>Leçon du jour : {concept}</b>\n\n{lecon}"

    if text in ["/prix", "prix", "cours"]:
        from watcher import get_stock_price
        from config import WATCHLIST
        msg = "📊 <b>Prix actuels :</b>\n\n"
        for symbol in WATCHLIST:
            price = get_stock_price(symbol)
            msg += f"• <b>{symbol}</b> : ${price}\n" if price else f"• <b>{symbol}</b> : N/A\n"
        return msg

    if text in ["/analyse", "analyse", "news"]:
        return "🔍 Analyse en cours... Clique sur <b>Vérifier maintenant</b> dans le dashboard."

    if text in ["/risque", "risque"]:
        return """⚠️ <b>Score de risque de ta watchlist :</b>

📈 AAPL — Risque faible (entreprise stable)
⚡ TSLA — Risque élevé (très volatile)
📦 AMZN — Risque moyen (solide mais cher)
💻 MSFT — Risque faible (dividendes stables)
₿ BTC-USD — Risque très élevé (crypto = spéculatif)

💡 <b>Conseil débutant :</b> Commence par les actions à risque faible. Ne mets jamais plus de 10% de ton argent dans une seule action."""

    if text in ["/aide", "/help", "aide", "help"]:
        return """📖 <b>Commandes disponibles :</b>

/lecon → Leçon financière du jour
/prix → Prix de tes actions en temps réel
/analyse → Lancer une analyse des news
/risque → Score de risque de ta watchlist
/aide → Cette aide

💬 Ou pose-moi n'importe quelle question sur la finance !"""

    # Question libre → Claude répond
    reponse = repondre_question(text)
    return f"🤖 <b>FinanceWatch AI :</b>\n\n{reponse}\n\n<i>⚠️ Ceci est une information éducative, pas un conseil financier officiel.</i>"

def listen_messages():
    """Écoute les messages Telegram en boucle."""
    global last_update_id
    print("Bot Telegram en écoute...")

    while True:
        updates = get_updates()
        for update in updates:
            last_update_id = update["update_id"]
            message = update.get("message", {})
            text = message.get("text", "")
            if text:
                print(f"  Message reçu: {text}")
                response = handle_message(text)
                send_telegram(response)

def start_bot():
    """Démarre le bot dans un thread séparé."""
    thread = threading.Thread(target=listen_messages, daemon=True)
    thread.start()
