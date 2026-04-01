"""
Générateur de plan d'investissement personnalisé via Claude AI — FinanceWatch AI
"""

import anthropic
from config import ANTHROPIC_API_KEY


def generate_investment_plan(budget: float, risk: str, goal: str, horizon: str) -> dict:
    """
    Génère un plan d'investissement personnalisé avec Claude AI.

    Args:
        budget: budget mensuel en €/$ (ex: 100)
        risk: tolérance au risque — "faible", "modéré", "élevé"
        goal: objectif — "court_terme", "long_terme", "retraite", "epargne"
        horizon: horizon d'investissement — "1an", "5ans", "10ans", "20ans"

    Returns dict with:
        - allocation: liste [{label, pct, exemples, couleur}]
        - conseil: texte du plan
        - montant_par_categorie: dict {label: montant mensuel}
        - resume: phrase d'accroche
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    horizon_label = {
        "1an": "1 an", "5ans": "5 ans", "10ans": "10 ans", "20ans": "20 ans+"
    }.get(horizon, horizon)

    goal_label = {
        "court_terme": "gains à court terme",
        "long_terme": "croissance à long terme",
        "retraite": "préparer la retraite",
        "epargne": "préserver mon capital"
    }.get(goal, goal)

    risk_label = {
        "faible": "faible (je veux sécuriser mon argent)",
        "modéré": "modéré (j'accepte quelques fluctuations)",
        "élevé": "élevé (je veux maximiser les gains)"
    }.get(risk, risk)

    prompt = f"""Tu es un conseiller financier expert. Génère un plan d'investissement personnalisé en JSON strict.

Profil investisseur :
- Budget mensuel : {budget}€
- Tolérance au risque : {risk_label}
- Objectif : {goal_label}
- Horizon : {horizon_label}

Réponds UNIQUEMENT avec ce JSON (pas de texte avant/après) :
{{
  "resume": "phrase d'accroche accrocheuse en 1-2 phrases",
  "conseil": "conseil détaillé de 3-4 phrases expliquant la stratégie et pourquoi elle convient à ce profil",
  "allocation": [
    {{"label": "ETF Monde", "pct": 40, "exemples": "SPY, VOO, QQQ", "couleur": "#6366f1"}},
    {{"label": "Actions Tech", "pct": 25, "exemples": "AAPL, MSFT, NVDA", "couleur": "#22c55e"}},
    {{"label": "Crypto", "pct": 15, "exemples": "BTC, ETH", "couleur": "#f59e0b"}},
    {{"label": "Obligations/Cash", "pct": 20, "exemples": "TLT, HYG", "couleur": "#64748b"}}
  ]
}}

Les pourcentages doivent sommer à 100. Adapte les catégories et % au profil. Maximum 5 catégories."""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        text = message.content[0].text.strip()
        # Extraire le JSON si entouré de ```
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)

        # Calculer montant par catégorie
        montants = {}
        for item in data.get("allocation", []):
            montants[item["label"]] = round(budget * item["pct"] / 100, 2)
        data["montant_par_categorie"] = montants
        data["budget"] = budget

        return data

    except Exception as e:
        return {"error": str(e)}
