from datetime import datetime, timezone
import requests, pandas as pd
from config.settings import API_KEYS
from .base_provider import BaseProvider, ProviderError

class TwelveDataProvider(BaseProvider):
    name = "Twelve Data"
    base = "https://api.twelvedata.com"
    def __init__(self): self.key=API_KEYS[self.name]
    def _get(self, endpoint, params):
        if not self.key: raise ProviderError("Twelve Data API key is missing. Add TWELVE_DATA_API_KEY to .env.")
        params={**params,"apikey":self.key}
        try: r=requests.get(f"{self.base}/{endpoint}",params=params,timeout=12); r.raise_for_status(); data=r.json()
        except requests.RequestException as e: raise ProviderError(f"Twelve Data request failed: {e}") from e
        if data.get("status")=="error" or data.get("code"): raise ProviderError(data.get("message","Twelve Data API error or rate limit."))
        return data
    def get_quote(self,symbol):
        d=self._get("quote",{"symbol":symbol})
        try:
            price=float(d["close"]); prev=float(d["previous_close"])
            return {"symbol":d.get("symbol",symbol),"name":d.get("name",symbol),"price":price,"change":float(d.get("change",price-prev)),
            "change_percent":float(d.get("percent_change",0)),"open":float(d["open"]),"high":float(d["high"]),"low":float(d["low"]),
            "previous_close":prev,"volume":int(float(d.get("volume",0))),"currency":d.get("currency","Unknown"),
            "exchange":d.get("exchange","Unknown"),"market_timestamp":d.get("datetime","Unknown"),
            "retrieved_at":datetime.now(timezone.utc).isoformat(),"freshness":"LATEST AVAILABLE QUOTE","provider":self.name}
        except (KeyError,ValueError,TypeError) as e: raise ProviderError(f"Unexpected Twelve Data quote format: {e}") from e
    def get_history(self,symbol,period="1y",interval="1d",start=None,end=None):
        mapping={"1m":"1min","5m":"5min","15m":"15min","30m":"30min","60m":"1h","1h":"1h","1d":"1day","1wk":"1week","1mo":"1month"}
        p={"symbol":symbol,"interval":mapping.get(interval,interval),"outputsize":5000}
        if start: p["start_date"]=start
        if end: p["end_date"]=end
        d=self._get("time_series",p)
        values=d.get("values")
        if not values: raise ProviderError("Twelve Data returned no historical values.")
        df=pd.DataFrame(values).rename(columns={"datetime":"Datetime","open":"Open","high":"High","low":"Low","close":"Close","volume":"Volume"})
        return self.normalize_history(df)
    def search_symbols(self,query):
        d=self._get("symbol_search",{"symbol":query})
        return [{"symbol":x.get("symbol",""),"name":x.get("instrument_name","")} for x in d.get("data",[])]
