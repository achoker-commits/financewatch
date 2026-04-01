import requests
import xml.etree.ElementTree as ET
from datetime import datetime

HEADERS = {"User-Agent": "FinanceWatch/1.0 (educational tool)"}

def get_google_news(symbol, company_name):
    """Récupère les news Google RSS pour une action."""
    news = []
    queries = [f"{company_name} stock", f"{symbol} bourse"]

    for query in queries:
        try:
            url = f"https://news.google.com/rss/search?q={query}&hl=fr&gl=FR&ceid=FR:fr"
            r = requests.get(url, headers=HEADERS, timeout=10)
            root = ET.fromstring(r.content)

            for item in root.findall('.//item')[:3]:
                title = item.findtext('title', '')
                pub_date = item.findtext('pubDate', '')
                news.append({
                    'headline': title,
                    'summary': title,
                    'source': 'Google News',
                    'datetime': pub_date
                })
        except Exception:
            pass

    return news

def get_reddit_sentiment(symbol):
    """Récupère le sentiment Reddit sur une action."""
    try:
        url = f"https://www.reddit.com/r/investing/search.json?q={symbol}&sort=new&limit=5"
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        posts = data.get('data', {}).get('children', [])

        results = []
        for post in posts:
            p = post.get('data', {})
            results.append({
                'headline': p.get('title', ''),
                'summary': p.get('selftext', '')[:200],
                'source': 'Reddit r/investing',
                'score': p.get('score', 0),
                'datetime': datetime.fromtimestamp(p.get('created_utc', 0)).strftime('%d/%m/%Y %H:%M')
            })
        return results
    except Exception:
        return []

COMPANY_NAMES = {
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "AMZN": "Amazon",
    "MSFT": "Microsoft",
    "BTC-USD": "Bitcoin",
    "NVDA": "Nvidia",
    "GOOGL": "Google",
    "META": "Meta Facebook",
    "LVMH": "LVMH",
    "TTE": "TotalEnergies",
}
