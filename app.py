from flask import Flask, render_template, jsonify, request, session, redirect
from apscheduler.schedulers.background import BackgroundScheduler
from watcher import check_all_symbols, get_stock_price
from mentor_bot import start_bot
from mentor_chat import poser_question, reset_conversation
from reports import envoyer_rapport_matinal, verifier_alertes_prix
from educator import get_lecon_du_jour
from indicators import get_technical_indicators, get_fear_and_greed
from portfolio import get_portfolio_with_prices
from database import save_alert, get_alerts, add_position, remove_position
from config import WATCHLIST, CHECK_INTERVAL_MINUTES, APP_PASSWORD
import yfinance as yf
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fw-secret-2024-choker")

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

latest_alerts = []
prix_precedents = {}
_cache = {}

def cached(key, fn, ttl=300):
    """Cache un résultat pendant ttl secondes."""
    import time
    now = time.time()
    if key in _cache and now - _cache[key]['ts'] < ttl:
        return _cache[key]['val']
    val = fn()
    _cache[key] = {'val': val, 'ts': now}
    return val

def fetch_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        if len(hist) >= 2:
            current = round(hist['Close'].iloc[-1], 2)
            previous = round(hist['Close'].iloc[-2], 2)
            change = round(((current - previous) / previous) * 100, 2)
            return symbol, {"price": current, "change": change}
        elif len(hist) == 1:
            return symbol, {"price": round(hist['Close'].iloc[-1], 2), "change": 0}
    except Exception:
        pass
    return symbol, {"price": "N/A", "change": 0}

def get_all_prices():
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as ex:
        results = ex.map(fetch_price, WATCHLIST)
    return dict(results)

def scheduled_check():
    global latest_alerts, prix_precedents
    results = check_all_symbols()
    if results:
        latest_alerts = results[:20]
        for r in results:
            a = r.get("analysis", {})
            save_alert(
                r["symbol"], r["headline"],
                a.get("sentiment"), a.get("conseil"),
                a.get("confiance"), a.get("raison"),
                r.get("price")
            )
    prix_actuels_raw = get_all_prices()
    prix_actuels = {s: v["price"] for s, v in prix_actuels_raw.items() if v["price"] != "N/A"}
    if prix_precedents:
        verifier_alertes_prix(prix_precedents, prix_actuels)
    prix_precedents = prix_actuels

scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_check, 'interval', minutes=CHECK_INTERVAL_MINUTES)
scheduler.add_job(envoyer_rapport_matinal, 'cron', hour=9, minute=0)
scheduler.start()
start_bot()

# ── PAGES ──────────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == APP_PASSWORD:
            session['logged_in'] = True
            return redirect('/')
        return render_template('login.html', error="Mot de passe incorrect")
    return render_template('login.html', error=None)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', watchlist=WATCHLIST)

# ── API MARCHÉS ────────────────────────────────────────────

@app.route('/api/prices')
def api_prices():
    return jsonify(cached('prices', get_all_prices, ttl=60))

@app.route('/api/chart/<symbol>')
def api_chart(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="30d")
        data = [
            {"date": str(idx.date()), "price": round(row['Close'], 2)}
            for idx, row in hist.iterrows()
        ]
        return jsonify(data)
    except Exception:
        return jsonify([])

@app.route('/api/indicators/<symbol>')
def api_indicators(symbol):
    data = cached('ind_' + symbol, lambda: get_technical_indicators(symbol), ttl=300)
    return jsonify(data or {})

@app.route('/api/fear-greed')
def api_fear_greed():
    return jsonify(cached('fear_greed', get_fear_and_greed, ttl=600))

# ── API ANALYSES ───────────────────────────────────────────

@app.route('/api/alerts')
def api_alerts():
    return jsonify(latest_alerts)

@app.route('/api/alerts/history')
def api_alerts_history():
    return jsonify(get_alerts(limit=50))

@app.route('/api/check-now')
def check_now():
    global latest_alerts
    results = check_all_symbols()
    if results:
        latest_alerts = results[:20]
        for r in results:
            a = r.get("analysis", {})
            save_alert(
                r["symbol"], r["headline"],
                a.get("sentiment"), a.get("conseil"),
                a.get("confiance"), a.get("raison"),
                r.get("price")
            )
    return jsonify({"status": "ok", "count": len(results)})

# ── API MENTOR ─────────────────────────────────────────────

@app.route('/api/mentor', methods=['POST'])
def api_mentor():
    data = request.get_json()
    question = (data.get('question') or '').strip()
    if not question:
        return jsonify({"error": "Question vide"}), 400
    reponse = poser_question(question)
    return jsonify({"reponse": reponse})

@app.route('/api/mentor/reset', methods=['POST'])
def api_mentor_reset():
    reset_conversation()
    return jsonify({"status": "ok"})

# ── API ÉDUCATION ──────────────────────────────────────────

@app.route('/api/lecon')
def api_lecon():
    def _get():
        concept, lecon = get_lecon_du_jour()
        return {"concept": concept, "lecon": lecon}
    return jsonify(cached('lecon', _get, ttl=3600))

# ── API PORTFOLIO ──────────────────────────────────────────

@app.route('/api/portfolio')
def api_portfolio():
    return jsonify(get_portfolio_with_prices())

@app.route('/api/portfolio/add', methods=['POST'])
def api_portfolio_add():
    data = request.get_json()
    symbol = (data.get('symbol') or '').strip().upper()
    try:
        quantity = float(data.get('quantity', 0))
        buy_price = float(data.get('buy_price', 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Valeurs invalides"}), 400
    if not symbol or quantity <= 0 or buy_price <= 0:
        return jsonify({"error": "Données manquantes ou invalides"}), 400
    add_position(symbol, quantity, buy_price)
    return jsonify({"status": "ok"})

@app.route('/api/portfolio/remove', methods=['POST'])
def api_portfolio_remove():
    data = request.get_json()
    symbol = (data.get('symbol') or '').strip().upper()
    if not symbol:
        return jsonify({"error": "Symbole manquant"}), 400
    remove_position(symbol)
    return jsonify({"status": "ok"})

# ── API RAPPORTS ───────────────────────────────────────────

@app.route('/api/rapport-maintenant')
def rapport_maintenant():
    envoyer_rapport_matinal()
    return jsonify({"status": "ok"})

def warm_cache():
    """Précalcule le cache au démarrage pour un chargement instantané."""
    import time
    time.sleep(2)
    try:
        cached('prices', get_all_prices, ttl=60)
        cached('fear_greed', get_fear_and_greed, ttl=600)
        def _get_lecon():
            concept, lecon = get_lecon_du_jour()
            return {"concept": concept, "lecon": lecon}
        cached('lecon', _get_lecon, ttl=3600)
        scheduled_check()
        print("Cache précalculé — app prête !")
    except Exception as e:
        print(f"Erreur warm cache: {e}")

if __name__ == '__main__':
    import threading
    print("FinanceWatch AI v3 — Edition Complète")
    print("Dashboard : http://localhost:5000")
    threading.Thread(target=warm_cache, daemon=True).start()
    app.run(debug=False, host='0.0.0.0', port=5000)
