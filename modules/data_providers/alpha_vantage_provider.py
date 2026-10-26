from datetime import datetime, timezone
import requests, pandas as pd
from config.settings import API_KEYS
from .base_provider import BaseProvider, ProviderError

class AlphaVantageProvider(BaseProvider):
    name="Alpha Vantage"; base="https://www.alphavantage.co/query"
    def __init__(self): self.key=API_KEYS[self.name]
    def _get(self,params):
        if not self.key: raise ProviderError("Alpha Vantage API key is missing. Add ALPHA_VANTAGE_API_KEY to .env.")
        try: r=requests.get(self.base,params={**params,"apikey":self.key},timeout=12); r.raise_for_status(); d=r.json()
        except requests.RequestException as e: raise ProviderError(f"Alpha Vantage request failed: {e}") from e
        msg=d.get("Note") or d.get("Information") or d.get("Error Message")
        if msg: raise ProviderError(str(msg))
        return d
    def get_quote(self,symbol):
        d=self._get({"function":"GLOBAL_QUOTE","symbol":symbol}).get("Global Quote",{})
        if not d: raise ProviderError("Alpha Vantage returned no quote (symbol, API quota, or entitlement issue).")
        try:
            price=float(d["05. price"]); prev=float(d["08. previous close"])
            return {"symbol":d.get("01. symbol",symbol),"name":symbol,"price":price,"change":float(d.get("09. change",price-prev)),
            "change_percent":float(str(d.get("10. change percent","0%")).replace("%","")),"open":float(d["02. open"]),
            "high":float(d["03. high"]),"low":float(d["04. low"]),"previous_close":prev,
            "volume":int(d.get("06. volume",0)),"currency":"Unknown","exchange":"Unknown","market_timestamp":d.get("07. latest trading day","Unknown"),
            "retrieved_at":datetime.now(timezone.utc).isoformat(),"freshness":"LATEST AVAILABLE QUOTE","provider":self.name}
        except (KeyError,ValueError) as e: raise ProviderError(f"Unexpected Alpha Vantage quote format: {e}") from e
    def get_history(self,symbol,period="1y",interval="1d",start=None,end=None):
        if interval in ("1m","5m","15m","30m","60m","1h"):
            d=self._get({"function":"TIME_SERIES_INTRADAY","symbol":symbol,"interval":"60min" if interval=="1h" else interval,"outputsize":"full"})
        else:
            fn={"1wk":"TIME_SERIES_WEEKLY_ADJUSTED","1mo":"TIME_SERIES_MONTHLY_ADJUSTED"}.get(interval,"TIME_SERIES_DAILY_ADJUSTED")
            d=self._get({"function":fn,"symbol":symbol,"outputsize":"full"})
        series=next((v for k,v in d.items() if "Time Series" in k),None)
        if not series: raise ProviderError("Alpha Vantage returned no time series.")
        rows=[]
        for dt,v in series.items():
            rows.append({"Datetime":dt,"Open":v.get("1. open"),"High":v.get("2. high"),"Low":v.get("3. low"),"Close":v.get("4. close"),"Volume":v.get("6. volume",v.get("5. volume"))})
        df=self.normalize_history(pd.DataFrame(rows))
        if start: df=df[df.Datetime>=pd.Timestamp(start)]
        if end: df=df[df.Datetime<=pd.Timestamp(end)]
        return df
