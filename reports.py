from mentor_bot import send_telegram
from watcher import get_stock_price, get_latest_news
from analyzer import analyze_news
from educator import get_lecon_du_jour
from config import WATCHLIST
import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def envoyer_rapport_matinal():
    """Envoie un rapport complet chaque matin à 9h."""
    print("Envoi du rapport matinal...")

    prix_msg = ""
    for symbol in WATCHLIST:
        price = get_stock_price(symbol)
        prix_msg += f"• <b>{symbol}</b> : ${price}\n" if price else ""

    concept, lecon = get_lecon_du_jour()

    message = f"""🌅 <b>BONJOUR — Rapport FinanceWatch AI</b>

📊 <b>Prix d'ouverture :</b>
{prix_msg}
━━━━━━━━━━━━━━━━━━━━━

🎓 <b>Leçon du jour : {concept}</b>
{lecon[:300]}...

━━━━━━━━━━━━━━━━━━━━━

💡 <b>Conseil du jour :</b>
La bourse c'est un marathon, pas un sprint. Les meilleurs investisseurs du monde (Warren Buffett, Peter Lynch) ont une chose en commun : la patience.

Bonne journée ! 💪
<i>Tape /analyse pour voir les dernières news.</i>"""

    send_telegram(message)

def verifier_alertes_prix(prix_precedents, prix_actuels):
    """Envoie une alerte si un prix varie de plus de 3%."""
    for symbol in WATCHLIST:
        if symbol not in prix_precedents or symbol not in prix_actuels:
            continue

        ancien = prix_precedents[symbol]
        nouveau = prix_actuels[symbol]

        if ancien and nouveau and ancien > 0:
            variation = ((nouveau - ancien) / ancien) * 100

            if abs(variation) >= 3:
                direction = "📈 HAUSSE" if variation > 0 else "📉 BAISSE"
                signe = "+" if variation > 0 else ""

                message = f"""🚨 <b>ALERTE PRIX — {symbol}</b>

{direction} de <b>{signe}{variation:.1f}%</b>

Prix précédent : ${ancien}
Prix actuel : ${nouveau}

💬 <i>Tape /analyse pour voir pourquoi.</i>"""

                send_telegram(message)
                print(f"Alerte envoyée: {symbol} {signe}{variation:.1f}%")
