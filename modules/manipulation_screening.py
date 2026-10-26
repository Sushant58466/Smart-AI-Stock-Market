from modules.analytics import volume_anomalies, add_indicators
def screen_market_movements(df):
    d=volume_anomalies(df); d=add_indicators(d)
    d["Daily Return %"]=d["Close"].pct_change()*100
    d["Unusual price move"]=d["Daily Return %"].abs()>d["Daily Return %"].rolling(60).std()*2.5
    d["Unusual volatility"]=d["Volatility 20D"]>d["Volatility 20D"].rolling(60).quantile(.9)
    d["Screen flag"]=d.get("Anomaly",False) | d["Unusual price move"].fillna(False) | d["Unusual volatility"].fillna(False)
    return d
