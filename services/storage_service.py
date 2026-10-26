import sqlite3, json
from pathlib import Path
from datetime import datetime, timezone
DB_PATH=Path(__file__).resolve().parents[1]/"smart_stock_ai.db"
def _connect():
    conn=sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS watchlist (symbol TEXT PRIMARY KEY, added_at TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS holdings (symbol TEXT PRIMARY KEY, quantity REAL, purchase_price REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS analysis_history (id INTEGER PRIMARY KEY, symbol TEXT, kind TEXT, created_at TEXT, details TEXT)")
    conn.commit()
    return conn
def get_watchlist():
    with _connect() as c: return [r[0] for r in c.execute("SELECT symbol FROM watchlist ORDER BY symbol")]
def add_watchlist(symbol):
    with _connect() as c: c.execute("INSERT OR IGNORE INTO watchlist VALUES (?,?)",(symbol.upper(),datetime.now(timezone.utc).isoformat()))
def remove_watchlist(symbol):
    with _connect() as c: c.execute("DELETE FROM watchlist WHERE symbol=?",(symbol.upper(),))
def get_holdings():
    with _connect() as c: return [{"symbol":r[0],"quantity":r[1],"purchase_price":r[2]} for r in c.execute("SELECT symbol,quantity,purchase_price FROM holdings")]
def save_holding(symbol,quantity,purchase_price):
    with _connect() as c: c.execute("INSERT OR REPLACE INTO holdings VALUES (?,?,?)",(symbol.upper(),float(quantity),float(purchase_price)))
def remove_holding(symbol):
    with _connect() as c: c.execute("DELETE FROM holdings WHERE symbol=?",(symbol.upper(),))
def save_analysis(symbol,kind,details):
    with _connect() as c: c.execute("INSERT INTO analysis_history(symbol,kind,created_at,details) VALUES (?,?,?,?)",(symbol,kind,datetime.now(timezone.utc).isoformat(),json.dumps(details,default=str)))
