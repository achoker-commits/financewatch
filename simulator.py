"""
Simulateur d'investissement — FinanceWatch AI
"Si j'avais investi X€ dans AAPL il y a N ans, j'aurais combien aujourd'hui ?"
"""

import yfinance as yf
from datetime import datetime, timedelta
import math


def simulate_investment(symbol: str, amount: float, years: int) -> dict:
    """
    Simule un investissement passé et compare vs S&P500 et inflation.

    Returns dict with:
      - symbol, amount, years
      - final_value: valeur actuelle de l'investissement
      - gain: gain ou perte en $
      - gain_pct: rendement en %
      - sp500_value: ce qu'aurait donné le S&P500 sur la même période
      - inflation_value: valeur ajustée à l'inflation (2%/an)
      - chart_data: points mensuels pour le graphique
      - verdict: phrase résumée
    """
    try:
        end = datetime.today()
        start = end - timedelta(days=years * 365)

        # Données de l'action
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))

        if hist.empty or len(hist) < 10:
            return {"error": f"Données insuffisantes pour {symbol}"}

        price_start = float(hist['Close'].iloc[0])
        price_end = float(hist['Close'].iloc[-1])

        if price_start <= 0:
            return {"error": "Prix de départ invalide"}

        shares = amount / price_start
        final_value = round(shares * price_end, 2)
        gain = round(final_value - amount, 2)
        gain_pct = round(((price_end - price_start) / price_start) * 100, 2)

        # S&P500 (SPY) sur la même période
        spy = yf.Ticker("SPY")
        spy_hist = spy.history(start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"))
        sp500_value = amount
        if not spy_hist.empty:
            spy_start = float(spy_hist['Close'].iloc[0])
            spy_end = float(spy_hist['Close'].iloc[-1])
            if spy_start > 0:
                sp500_value = round(amount * (spy_end / spy_start), 2)

        # Inflation simulée à 2%/an
        inflation_value = round(amount * math.pow(1.02, years), 2)

        # Points mensuels pour graphique (rééchantillonner)
        monthly = hist['Close'].resample('ME').last()
        chart_data = []
        for date, price in monthly.items():
            val = round(shares * float(price), 2)
            chart_data.append({"date": str(date.date()), "value": val})

        # Verdict
        if gain_pct > 100:
            verdict = f"Excellent ! Tu aurais plus que doublé ta mise sur {symbol}."
        elif gain_pct > 20:
            verdict = f"Très bon investissement — {symbol} t'aurait bien rapporté."
        elif gain_pct > 0:
            verdict = f"Investissement positif mais modeste sur {symbol}."
        elif gain_pct > -20:
            verdict = f"Légère perte sur {symbol}. Le marché a été difficile."
        else:
            verdict = f"Perte significative sur {symbol} sur cette période."

        # Comparaison vs S&P500
        if final_value > sp500_value:
            verdict += f" Tu aurais battu le S&P500 (+${round(final_value - sp500_value, 2)})."
        else:
            verdict += f" Le S&P500 t'aurait mieux servi (+${round(sp500_value - final_value, 2)} de plus)."

        return {
            "symbol": symbol,
            "amount": amount,
            "years": years,
            "price_start": round(price_start, 2),
            "price_end": round(price_end, 2),
            "shares": round(shares, 4),
            "final_value": final_value,
            "gain": gain,
            "gain_pct": gain_pct,
            "sp500_value": sp500_value,
            "inflation_value": inflation_value,
            "chart_data": chart_data,
            "verdict": verdict,
        }

    except Exception as e:
        return {"error": str(e)}
