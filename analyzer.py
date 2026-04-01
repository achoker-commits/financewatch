import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def analyze_news(symbol, news_headline, news_summary):
    """Analyse une news avec Claude AI et retourne un conseil d'investissement."""

    prompt = f"""Tu es un analyste financier expert. Analyse cette news concernant l'action {symbol} et donne un conseil précis.

NEWS: {news_headline}
RÉSUMÉ: {news_summary}

Réponds UNIQUEMENT en JSON avec ce format exact:
{{
  "sentiment": "HAUSSIER" ou "BAISSIER" ou "NEUTRE",
  "confiance": <nombre entre 1 et 10>,
  "conseil": "ACHETER" ou "VENDRE" ou "ATTENDRE",
  "raison": "<explication courte en 1-2 phrases>",
  "urgence": "HAUTE" ou "MOYENNE" ou "FAIBLE"
}}

Sois précis et factuel. Base-toi uniquement sur la news fournie."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    try:
        text = response.content[0].text.strip()
        # Extraire le JSON si entouré de backticks
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        return json.loads(text)
    except Exception:
        return {
            "sentiment": "NEUTRE",
            "confiance": 5,
            "conseil": "ATTENDRE",
            "raison": "Impossible d'analyser cette news.",
            "urgence": "FAIBLE"
        }
