import yfinance as yf
from database import get_portfolio, add_position, remove_position

def get_portfolio_with_prices():
    """Retourne le portfolio avec les prix actuels et le P&L."""
    positions = get_portfolio()
    if not positions:
        return []

    result = []
    total_invested = 0
    total_current = 0

    for pos in positions:
        symbol = pos["symbol"]
        quantity = pos["quantity"]
        buy_price = pos["buy_price"]
        invested = round(quantity * buy_price, 2)

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            current_price = round(hist['Close'].iloc[-1], 2) if not hist.empty else buy_price
        except Exception:
            current_price = buy_price

        current_value = round(quantity * current_price, 2)
        pnl = round(current_value - invested, 2)
        pnl_pct = round(((current_value - invested) / invested) * 100, 2) if invested > 0 else 0

        total_invested += invested
        total_current += current_value

        result.append({
            "symbol": symbol,
            "quantity": quantity,
            "buy_price": buy_price,
            "current_price": current_price,
            "invested": invested,
            "current_value": current_value,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        })

    total_pnl = round(total_current - total_invested, 2)
    total_pnl_pct = round(((total_current - total_invested) / total_invested) * 100, 2) if total_invested > 0 else 0

    return {
        "positions": result,
        "total_invested": round(total_invested, 2),
        "total_current": round(total_current, 2),
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
    }
