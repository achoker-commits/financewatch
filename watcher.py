import finnhub
import yfinance as yf
from datetime import datetime, timedelta
from config import FINNHUB_API_KEY, WATCHLIST, CHECK_INTERVAL_MINUTES, ALERT_THRESHOLD
from analyzer import analyze_news
from notifier import send_telegram, format_alert

finnhub_client = finnhub.Client(api_key=FINNHUB_API_KEY)

# Garde en mémoire les news déjà traitées
seen_news = set()

def get_stock_price(symbol):
    """Récupère le prix actuel d'une action."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            return round(price, 2)
    except Exception:
        pass
    return None

def get_latest_news(symbol):
    """Récupère les dernières news Finnhub pour un symbole."""
    try:
        # Finnhub ne supporte pas BTC-USD, adapter le symbole
        finnhub_symbol = symbol.replace("-USD", "")
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(hours=CHECK_INTERVAL_MINUTES / 60 + 1)).strftime("%Y-%m-%d")

        news = finnhub_client.company_news(finnhub_symbol, _from=from_date, to=to_date)
        return news[:5] if news else []
    except Exception as e:
        print(f"Erreur news {symbol}: {e}")
        return []

def check_all_symbols():
    """Vérifie toutes les actions de la watchlist."""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Vérification des news...")
    alerts = []

    for symbol in WATCHLIST:
        news_list = get_latest_news(symbol)
        price = get_stock_price(symbol)

        for news in news_list:
            news_id = str(news.get('id', news.get('datetime', '')))
            if news_id in seen_news:
                continue

            seen_news.add(news_id)
            headline = news.get('headline', '')
            summary = news.get('summary', headline)

            if not headline:
                continue

            print(f"  Analyse: [{symbol}] {headline[:60]}...")
            analysis = analyze_news(symbol, headline, summary)

            news['datetime'] = datetime.fromtimestamp(
                news.get('datetime', 0)
            ).strftime('%d/%m/%Y %H:%M') if news.get('datetime') else 'N/A'

            if price:
                news['price'] = price

            if analysis.get('confiance', 0) >= ALERT_THRESHOLD:
                message = format_alert(symbol, news, analysis)
                send_telegram(message)
                print(f"  ALERTE ENVOYÉE: {symbol} — {analysis['conseil']} (confiance: {analysis['confiance']}/10)")

            alerts.append({
                "symbol": symbol,
                "price": price,
                "headline": headline,
                "analysis": analysis,
                "datetime": news['datetime']
            })

    return alerts
