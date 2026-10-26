import pandas as pd
def sector_performance(data):
    """data maps sector name to normalized historical OHLCV DataFrame."""
    rows=[]
    for sector,df in data.items():
        if df is None or len(df)<2: continue
        rows.append({"Sector":sector,"Return %":(df.Close.iloc[-1]/df.Close.iloc[0]-1)*100,
                     "Volatility %":df.Close.pct_change().std()*(252**.5)*100})
    return pd.DataFrame(rows).sort_values("Return %",ascending=False) if rows else pd.DataFrame(columns=["Sector","Return %","Volatility %"])
