import anthropic, json
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def analyze_news(symbol, news_headline, news_summary):
    prompt = f"""Tu es un analyste financier expert. Analyse cette news concernant l'action {symbol}.

NEWS: {news_headline}
RESUME: {news_summary}

Reponds UNIQUEMENT en JSON:
{{"sentiment": "HAUSSIER" ou "BAISSIER" ou "NEUTRE", "confiance": 1-10, "conseil": "ACHETER" ou "VENDRE" ou "ATTENDRE", "raison": "1-2 phrases", "urgence": "HAUTE" ou "MOYENNE" ou "FAIBLE"}}"""
    response = client.messages.create(model="claude-sonnet-4-6", max_tokens=300, messages=[{"role": "user", "content": prompt}])
    try:
        text = response.content[0].text.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        return json.loads(text)
    except Exception:
        return {"sentiment": "NEUTRE", "confiance": 5, "conseil": "ATTENDRE", "raison": "Impossible d'analyser.", "urgence": "FAIBLE"}
