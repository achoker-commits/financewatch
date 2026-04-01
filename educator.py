import anthropic
from config import ANTHROPIC_API_KEY
from datetime import datetime

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

LECONS = [
    ("Action (stock)", "Une action c'est quoi ?"),
    ("Diversification", "Pourquoi ne pas mettre tous ses œufs dans le même panier ?"),
    ("Dividende", "Comment gagner de l'argent sans vendre ses actions ?"),
    ("Indice boursier", "C'est quoi le CAC 40, le S&P 500 ?"),
    ("Bull market / Bear market", "Marché haussier vs baissier — comment les reconnaître ?"),
    ("Capitalisation boursière", "Pourquoi Apple vaut plus que ton pays ?"),
    ("Volume de trading", "Pourquoi le nombre de transactions est important ?"),
    ("Analyse technique", "Lire un graphique comme un pro"),
    ("Analyse fondamentale", "Évaluer la vraie valeur d'une entreprise"),
    ("PER (Price Earnings Ratio)", "L'indicateur que tous les pros regardent"),
    ("Stop-loss", "Comment limiter ses pertes automatiquement ?"),
    ("ETF", "Investir dans 500 entreprises en une seule fois"),
    ("Inflation", "Pourquoi ton argent perd de la valeur chaque année ?"),
    ("Taux d'intérêt", "Comment la banque centrale influence la bourse ?"),
    ("Short selling", "Comment gagner quand une action chute ?"),
]

def get_lecon_du_jour():
    """Retourne la leçon financière du jour adaptée à un débutant de 18 ans."""
    jour = datetime.now().timetuple().tm_yday % len(LECONS)
    concept, question = LECONS[jour]

    prompt = f"""Tu es un mentor financier bienveillant qui explique la finance à un jeune de 18 ans sans expérience.

Explique le concept : "{concept}"
En répondant à la question : "{question}"

Règles :
- Langage simple, zéro jargon non expliqué
- Une analogie de la vie quotidienne obligatoire
- Maximum 150 mots
- Termine par UN conseil concret pour un débutant avec peu d'argent
- Utilise des emojis pour rendre ça vivant"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return concept, response.content[0].text

def repondre_question(question):
    """Répond à une question financière de façon simple pour un débutant."""
    prompt = f"""Tu es FinanceWatch AI, un mentor financier pour un jeune de 18 ans sans expérience.

Question : "{question}"

Réponds de façon :
- Simple et claire (pas de jargon)
- Honnête (dis si c'est risqué)
- Encourageante mais réaliste
- Avec un exemple concret si possible
- Maximum 200 mots
- Rappelle toujours que tu n'es pas un conseiller financier officiel"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
