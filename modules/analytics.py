import numpy as np, pandas as pd
def add_indicators(df):
    d=df.copy()
    c=d["Close"]
    d["SMA 20"]=c.rolling(20).mean(); d["SMA 50"]=c.rolling(50).mean()
    d["EMA 20"]=c.ewm(span=20,adjust=False).mean()
    delta=c.diff(); gain=delta.clip(lower=0).rolling(14).mean(); loss=-delta.clip(upper=0).rolling(14).mean()
    rs=gain/loss.replace(0,np.nan); d["RSI"]=100-(100/(1+rs))
    ema12=c.ewm(span=12,adjust=False).mean(); ema26=c.ewm(span=26,adjust=False).mean()
    d["MACD"]=ema12-ema26; d["MACD Signal"]=d["MACD"].ewm(span=9,adjust=False).mean()
    mid=c.rolling(20).mean(); std=c.rolling(20).std()
    d["BB Upper"]=mid+2*std; d["BB Lower"]=mid-2*std
    d["Daily Return"]=c.pct_change(); d["Cumulative Return"]=(1+d["Daily Return"].fillna(0)).cumprod()-1
    d["Volatility 20D"]=d["Daily Return"].rolling(20).std()*np.sqrt(252)
    peak=c.cummax(); d["Drawdown"]=c/peak-1
    return d
def performance_metrics(df):
    d=add_indicators(df); r=d["Daily Return"].dropna()
    if r.empty: return {}
    return {"Total return":float((df.Close.iloc[-1]/df.Close.iloc[0]-1)*100),
      "Annualized volatility":float(r.std()*np.sqrt(252)*100),
      "Maximum drawdown":float(d.Drawdown.min()*100),
      "Historical VaR 95%":float(-r.quantile(.05)*100),
      "Historical CVaR 95%":float(-r[r<=r.quantile(.05)].mean()*100)}
def volume_anomalies(df):
    d=df.copy(); d["Volume mean 20"]=d.Volume.rolling(20).mean(); d["Volume std 20"]=d.Volume.rolling(20).std()
    d["Volume z-score"]=(d.Volume-d["Volume mean 20"])/d["Volume std 20"].replace(0,np.nan)
    d["Anomaly"]=d["Volume z-score"].abs()>2.5
    try:
        from sklearn.ensemble import IsolationForest
        valid=d[["Volume"]].dropna()
        if len(valid)>=30:
            model=IsolationForest(contamination=.03,random_state=42).fit(valid)
            d.loc[valid.index,"Isolation Forest anomaly"]=model.predict(valid)==-1
    except Exception: pass
    return d
def trend_prediction(df):
    """Chronological baseline: predicts next close from lagged returns; reports held-out test metrics."""
    d=add_indicators(df).dropna().copy()
    if len(d)<80: return {"error":"At least 80 usable observations are required."}
    d["Target"]=d["Close"].shift(-1); d["Lag1"]=d["Close"].pct_change(); d["Lag5"]=d["Close"].pct_change(5)
    d["SMA ratio"]=d["Close"]/d["SMA 20"]-1; d=d.dropna()
    if len(d)<60: return {"error":"Not enough observations after indicator calculation."}
    features=["Lag1","Lag5","SMA ratio","RSI","Volatility 20D"]
    split=int(len(d)*.8); train,test=d.iloc[:split],d.iloc[split:]
    from sklearn.ensemble import RandomForestRegressor
    model=RandomForestRegressor(n_estimators=120,max_depth=5,min_samples_leaf=3,random_state=42)
    model.fit(train[features],train["Target"]); pred=model.predict(test[features])
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    mae=mean_absolute_error(test["Target"],pred); rmse=np.sqrt(mean_squared_error(test["Target"],pred))
    latest=d.iloc[-1:][features]; next_est=float(model.predict(latest)[0])
    current=float(d["Close"].iloc[-1]); pct=(next_est/current-1)*100
    return {"prediction":next_est,"current":current,"change_pct":pct,"trend":"Bullish" if pct>.5 else "Bearish" if pct<-.5 else "Neutral",
      "mae":float(mae),"rmse":float(rmse),"test_rows":len(test),"test_actual":test["Target"].values,"test_predicted":pred,
      "test_dates":test["Datetime"].values,"features":features,"importance":dict(zip(features,model.feature_importances_))}
