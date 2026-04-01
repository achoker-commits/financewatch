import anthropic
from config import ANTHROPIC_API_KEY, WATCHLIST
from database import save_mentor_message, get_mentor_history, clear_mentor_history

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Tu es FinanceWatch AI, le mentor financier personnel de Choker, 18 ans, Charleroi (Belgique).
Il débute complètement en finance, a peu d'argent, et utilise l'app Bux pour investir.

Ton rôle :
- Être son mentor de confiance, pas un robot
- Expliquer SIMPLEMENT, comme à un ami de 18 ans
- Être honnête sur les risques (jamais mentir pour rassurer)
- Encourager sans promettre des gains
- Utiliser des exemples concrets de la vie quotidienne (pizzeria, voiture, etc.)
- Parfois utiliser des emojis pour rendre ça vivant
- Te souvenir des questions précédentes dans la conversation

Actions qu'il surveille : """ + ", ".join(WATCHLIST) + """

Règles absolues :
- JAMAIS promettre des gains garantis
- JAMAIS conseiller d'investir de l'argent qu'il ne peut pas se permettre de perdre
- TOUJOURS expliquer les risques
- Rappeler que tu n'es pas un conseiller financier officiel quand c'est important
- Réponses courtes et claires (max 250 mots sauf question complexe)
- Tutoiement OBLIGATOIRE — tu parles à un ami"""

def poser_question(question):
    """Pose une question au mentor avec mémoire persistante entre sessions."""
    save_mentor_message("user", question)
    history = get_mentor_history(limit=16)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=history
    )

    answer = response.content[0].text
    save_mentor_message("assistant", answer)
    return answer

def reset_conversation():
    """Remet la conversation à zéro."""
    clear_mentor_history()
