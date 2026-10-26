def answer_question(question, symbol, df, quote=None):
    q=question.lower()
    if df is None or df.empty: return "No verified market data is loaded. Select a stock and load data first."
    last=df.iloc[-1]; first=df.iloc[0]
    if any(x in q for x in ("trend","direction","performance","return")):
        pct=(last.Close/first.Close-1)*100
        return f"{symbol} changed {pct:.2f}% over the loaded history ({first.Datetime.date()} to {last.Datetime.date()}). This is a historical observation, not a forecast."
    if "volume" in q:
        return f"The latest loaded volume is {last.Volume:,.0f}." if last.Volume==last.Volume else "Volume is unavailable in the loaded dataset."
    if "high" in q: return f"Latest loaded high: {last.High:.2f}."
    if "low" in q: return f"Latest loaded low: {last.Low:.2f}."
    if "price" in q or "close" in q: return f"Latest loaded close: {last.Close:.2f} on {last.Datetime.date()}."
    return f"I can explain {symbol}'s loaded historical trend, close, high/low, and volume. Ask about price, trend, return, high, low, or volume. This is a rule-based assistant grounded in loaded data."
