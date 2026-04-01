import sqlite3
from datetime import datetime

DB_PATH = "financewatch.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            headline TEXT,
            sentiment TEXT,
            conseil TEXT,
            confiance INTEGER,
            raison TEXT,
            price REAL,
            source TEXT DEFAULT 'Finnhub',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            quantity REAL NOT NULL,
            buy_price REAL NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS mentor_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            recorded_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

def save_alert(symbol, headline, sentiment, conseil, confiance, raison, price, source="Finnhub"):
    conn = get_conn()
    conn.execute("""
        INSERT INTO alerts (symbol, headline, sentiment, conseil, confiance, raison, price, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (symbol, headline, sentiment, conseil, confiance, raison, price, source))
    conn.commit()
    conn.close()

def get_alerts(limit=50):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_alerts_by_symbol(symbol, limit=20):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM alerts WHERE symbol=? ORDER BY created_at DESC LIMIT ?", (symbol, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_mentor_accuracy():
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM alerts WHERE conseil != 'ATTENDRE'").fetchone()[0]
    conn.close()
    return total

def add_position(symbol, quantity, buy_price):
    conn = get_conn()
    conn.execute("""
        INSERT INTO portfolio (symbol, quantity, buy_price)
        VALUES (?, ?, ?)
        ON CONFLICT(symbol) DO UPDATE SET quantity=excluded.quantity, buy_price=excluded.buy_price
    """, (symbol.upper(), quantity, buy_price))
    conn.commit()
    conn.close()

def remove_position(symbol):
    conn = get_conn()
    conn.execute("DELETE FROM portfolio WHERE symbol=?", (symbol.upper(),))
    conn.commit()
    conn.close()

def get_portfolio():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM portfolio ORDER BY symbol").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_mentor_message(role, content):
    conn = get_conn()
    conn.execute("INSERT INTO mentor_memory (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

def get_mentor_history(limit=20):
    conn = get_conn()
    rows = conn.execute("SELECT role, content FROM mentor_memory ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

def clear_mentor_history():
    conn = get_conn()
    conn.execute("DELETE FROM mentor_memory")
    conn.commit()
    conn.close()

def save_price(symbol, price):
    conn = get_conn()
    conn.execute("INSERT INTO price_history (symbol, price) VALUES (?, ?)", (symbol, price))
    conn.commit()
    conn.close()

init_db()
