from flask import Flask, render_template, jsonify, request, session, redirect, Response
from apscheduler.schedulers.background import BackgroundScheduler
from watcher import check_all_symbols, get_stock_price
from mentor_bot import start_bot
from mentor_chat import poser_question, reset_conversation
from reports import envoyer_rapport_matinal, verifier_alertes_prix
from educator import get_lecon_du_jour
from indicators import get_technical_indicators, get_fear_and_greed
from portfolio import get_portfolio_with_prices
from database import (save_alert, get_alerts, add_position, remove_position,
                      save_custom_alert, get_custom_alerts, delete_custom_alert,
                      get_untriggered_alerts, mark_alert_triggered,
                      save_investment_plan, get_latest_investment_plan)
from config import WATCHLIST, WATCHLIST_CATEGORIES, CHECK_INTERVAL_MINUTES, APP_PASSWORD
from simulator import simulate_investment
from investment_plan import generate_investment_plan
import yfinance as yf
import os
import csv
import io

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

    # Vérifier les alertes custom
    for alert in get_untriggered_alerts():
        sym = alert["symbol"]
        prix = prix_actuels.get(sym)
        if prix is None:
            _, pd = fetch_price(sym)
            prix = pd.get("price")
        if prix and prix != "N/A":
            cond = alert["condition"]
            target = alert["target_price"]
            if (cond == "above" and prix >= target) or (cond == "below" and prix <= target):
                mark_alert_triggered(alert["id"])
                try:
                    from notifier import send_telegram
                    emoji = "🚀" if cond == "above" else "📉"
                    send_telegram(f"{emoji} Alerte prix : {sym} est à ${prix} "
                                  f"({'au-dessus' if cond == 'above' else 'en-dessous'} de ${target})")
                except Exception:
                    pass

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
    period = request.args.get('period', '30d')
    allowed = ['7d', '30d', '90d', '1y', '2y', '5y']
    if period not in allowed:
        period = '30d'
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
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
@login_required
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
@login_required
def rapport_maintenant():
    envoyer_rapport_matinal()
    return jsonify({"status": "ok"})

# ── API WATCHLIST ÉTENDUE ──────────────────────────────────

@app.route('/api/categories')
def api_categories():
    return jsonify(list(WATCHLIST_CATEGORIES.keys()))

@app.route('/api/prices/category/<category>')
@login_required
def api_prices_category(category):
    symbols = WATCHLIST_CATEGORIES.get(category, [])
    if not symbols:
        return jsonify({})
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = ex.map(fetch_price, symbols)
    return jsonify(dict(results))

@app.route('/api/search')
@login_required
def api_search():
    q = request.args.get('q', '').strip().upper()
    if len(q) < 1:
        return jsonify([])
    matches = []
    for cat, symbols in WATCHLIST_CATEGORIES.items():
        for s in symbols:
            if q in s:
                matches.append({"symbol": s, "category": cat})
    return jsonify(matches[:10])

# ── API DÉCOUVRIR (Top gainers/losers) ─────────────────────

@app.route('/api/decouvrir')
@login_required
def api_decouvrir():
    def _compute():
        all_symbols = []
        for syms in WATCHLIST_CATEGORIES.values():
            all_symbols.extend(syms)
        all_symbols = list(set(all_symbols))

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=10) as ex:
            results = list(ex.map(fetch_price, all_symbols))

        valid = [(s, d) for s, d in results if d["price"] != "N/A" and d["change"] != 0]
        valid.sort(key=lambda x: x[1]["change"], reverse=True)
        gainers = [{"symbol": s, **d} for s, d in valid[:5]]
        losers = [{"symbol": s, **d} for s, d in valid[-5:]]
        return {"gainers": gainers, "losers": losers}

    return jsonify(cached('decouvrir', _compute, ttl=300))

# ── API COMPARATEUR ────────────────────────────────────────

@app.route('/api/compare')
@login_required
def api_compare():
    s1 = request.args.get('s1', '').upper()
    s2 = request.args.get('s2', '').upper()
    period = request.args.get('period', '30d')
    if not s1 or not s2:
        return jsonify({"error": "Deux symboles requis"})
    try:
        t1 = yf.Ticker(s1)
        t2 = yf.Ticker(s2)
        h1 = t1.history(period=period)
        h2 = t2.history(period=period)
        if h1.empty or h2.empty:
            return jsonify({"error": "Données introuvables"})

        def normalize(hist):
            first = float(hist['Close'].iloc[0])
            return [
                {"date": str(idx.date()), "pct": round(((float(row['Close']) - first) / first) * 100, 2)}
                for idx, row in hist.iterrows()
            ]

        return jsonify({
            "s1": {"symbol": s1, "data": normalize(h1)},
            "s2": {"symbol": s2, "data": normalize(h2)},
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# ── API SCREENER ───────────────────────────────────────────

@app.route('/api/screener')
@login_required
def api_screener():
    rsi_max = float(request.args.get('rsi_max', 100))
    rsi_min = float(request.args.get('rsi_min', 0))
    change_min = float(request.args.get('change_min', -999))

    all_symbols = []
    for syms in WATCHLIST_CATEGORIES.values():
        all_symbols.extend(syms[:5])  # Max 5 par catégorie pour la vitesse
    all_symbols = list(set(all_symbols))

    results = []
    for sym in all_symbols[:30]:
        try:
            ind = get_technical_indicators(sym)
            price_data = fetch_price(sym)
            change = price_data[1].get("change", 0)
            price = price_data[1].get("price", "N/A")
            if not ind or not ind.get("rsi"):
                continue
            rsi = ind["rsi"]
            if rsi_min <= rsi <= rsi_max and change >= change_min:
                results.append({
                    "symbol": sym,
                    "price": price,
                    "change": change,
                    "rsi": rsi,
                    "trend": ind.get("trend_status", ""),
                })
        except Exception:
            continue

    results.sort(key=lambda x: x["rsi"])
    return jsonify(results)

# ── API SIMULATEUR ─────────────────────────────────────────

@app.route('/api/simulate', methods=['POST'])
@login_required
def api_simulate():
    data = request.get_json()
    symbol = (data.get('symbol') or '').strip().upper()
    try:
        amount = float(data.get('amount', 0))
        years = int(data.get('years', 1))
    except (ValueError, TypeError):
        return jsonify({"error": "Valeurs invalides"}), 400
    if not symbol or amount <= 0 or years <= 0:
        return jsonify({"error": "Données manquantes"}), 400
    result = simulate_investment(symbol, amount, years)
    return jsonify(result)

# ── API PLAN D'INVESTISSEMENT ──────────────────────────────

@app.route('/api/plan', methods=['POST'])
@login_required
def api_plan():
    data = request.get_json()
    try:
        budget = float(data.get('budget', 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Budget invalide"}), 400
    risk = data.get('risk', 'modéré')
    goal = data.get('goal', 'long_terme')
    horizon = data.get('horizon', '5ans')
    if budget <= 0:
        return jsonify({"error": "Budget invalide"}), 400
    plan = generate_investment_plan(budget, risk, goal, horizon)
    if "error" not in plan:
        save_investment_plan(budget, risk, goal, horizon, plan)
    return jsonify(plan)

@app.route('/api/plan/latest')
@login_required
def api_plan_latest():
    plan = get_latest_investment_plan()
    return jsonify(plan or {})

# ── API ALERTES CUSTOM ─────────────────────────────────────

@app.route('/api/custom-alerts', methods=['GET'])
@login_required
def api_get_custom_alerts():
    return jsonify(get_custom_alerts())

@app.route('/api/custom-alerts', methods=['POST'])
@login_required
def api_create_custom_alert():
    data = request.get_json()
    symbol = (data.get('symbol') or '').strip().upper()
    condition = data.get('condition', 'above')
    try:
        target_price = float(data.get('target_price', 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Prix invalide"}), 400
    if not symbol or target_price <= 0:
        return jsonify({"error": "Données manquantes"}), 400
    save_custom_alert(symbol, condition, target_price)
    return jsonify({"status": "ok"})

@app.route('/api/custom-alerts/<int:alert_id>', methods=['DELETE'])
@login_required
def api_delete_custom_alert(alert_id):
    delete_custom_alert(alert_id)
    return jsonify({"status": "ok"})

# ── API PUSH NOTIFICATIONS ────────────────────────────────

# Stockage en mémoire des subscriptions push (persiste tant que le serveur tourne)
_push_subscriptions = []

@app.route('/api/push/subscribe', methods=['POST'])
@login_required
def api_push_subscribe():
    data = request.get_json()
    sub = data.get('subscription')
    if not sub:
        return jsonify({"error": "Subscription manquante"}), 400
    # Évite les doublons (basé sur l'endpoint)
    endpoint = sub.get('endpoint', '')
    _push_subscriptions[:] = [s for s in _push_subscriptions if s.get('endpoint') != endpoint]
    _push_subscriptions.append(sub)
    return jsonify({"status": "ok", "count": len(_push_subscriptions)})

@app.route('/api/push/vapid-key')
def api_push_vapid_key():
    """Retourne la clé publique VAPID pour la souscription côté client."""
    key = os.environ.get("VAPID_PUBLIC_KEY", "")
    return jsonify({"key": key, "enabled": bool(key)})

# ── API EXPORT PORTFOLIO CSV ───────────────────────────────

@app.route('/api/portfolio/export')
@login_required
def api_portfolio_export():
    data = get_portfolio_with_prices()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Symbole", "Quantité", "Prix achat", "Prix actuel", "Valeur", "PnL $", "PnL %"])
    for p in data.get("positions", []):
        writer.writerow([
            p["symbol"], p["quantity"], p["buy_price"],
            p["current_price"],
            round(p["quantity"] * p["current_price"], 2),
            p["pnl"], p["pnl_pct"]
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=portfolio.csv"}
    )

def warm_cache():
    """Précalcule le cache au démarrage pour un chargement instantané."""
    import time
    time.sleep(2)
    for name, fn in [
        ("prices",     lambda: cached('prices', get_all_prices, ttl=60)),
        ("fear_greed", lambda: cached('fear_greed', get_fear_and_greed, ttl=600)),
        ("lecon",      lambda: cached('lecon', lambda: dict(zip(("concept", "lecon"), get_lecon_du_jour())), ttl=3600)),
        ("alertes",    scheduled_check),
    ]:
        try:
            fn()
        except Exception as e:
            print(f"Warm cache [{name}] ignoré: {e}")
    print("FinanceWatch AI v4 — prêt !")

if __name__ == '__main__':
    import threading
    print("FinanceWatch AI v4 — Edition Complète")
    print("Dashboard : http://localhost:5000")
    threading.Thread(target=warm_cache, daemon=True).start()
    app.run(debug=False, host='0.0.0.0', port=5000)
