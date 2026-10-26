from datetime import datetime, timezone, timedelta
import requests, pandas as pd
from config.settings import API_KEYS
from .base_provider import BaseProvider, ProviderError

class FinnhubProvider(BaseProvider):
    name="Finnhub"; base="https://finnhub.io/api/v1"
    def __init__(self): self.key=API_KEYS[self.name]
    def _get(self,endpoint,params):
        if not self.key: raise ProviderError("Finnhub API key is missing. Add FINNHUB_API_KEY to .env.")
        try: r=requests.get(f"{self.base}/{endpoint}",params={**params,"token":self.key},timeout=12); r.raise_for_status(); d=r.json()
        except requests.RequestException as e: raise ProviderError(f"Finnhub request failed: {e}") from e
        if isinstance(d,dict) and d.get("error"): raise ProviderError(d["error"])
        return d
    def get_quote(self,symbol):
        d=self._get("quote",{"symbol":symbol})
        if not d.get("c"): raise ProviderError("Finnhub quote unavailable for this symbol or subscription.")
        price=float(d["c"]); prev=float(d.get("pc") or price)
        return {"symbol":symbol,"name":symbol,"price":price,"change":float(d.get("d") or price-prev),
            "change_percent":float(d.get("dp") or 0),"open":float(d.get("o") or 0),"high":float(d.get("h") or 0),
            "low":float(d.get("l") or 0),"previous_close":prev,"volume":None,"currency":"Unknown","exchange":"Unknown",
            "market_timestamp":datetime.fromtimestamp(d["t"],timezone.utc).isoformat() if d.get("t") else "Unknown",
            "retrieved_at":datetime.now(timezone.utc).isoformat(),"freshness":"LATEST AVAILABLE QUOTE","provider":self.name}
    def get_history(self,symbol,period="1y",interval="1d",start=None,end=None):
        end_dt=datetime.now(timezone.utc); start_dt=end_dt-timedelta(days=365 if period=="1y" else 30)
        if start: start_dt=pd.Timestamp(start,tz="UTC").to_pydatetime()
        if end: end_dt=pd.Timestamp(end,tz="UTC").to_pydatetime()
        resolution={"1m":"1","5m":"5","15m":"15","30m":"30","60m":"60","1h":"60","1d":"D","1wk":"W","1mo":"M"}.get(interval,"D")
        d=self._get("stock/candle",{"symbol":symbol,"resolution":resolution,"from":int(start_dt.timestamp()),"to":int(end_dt.timestamp())})
        if d.get("s")!="ok": raise ProviderError(f"Finnhub candles unavailable: {d.get('s','unknown status')}.")
        return self.normalize_history(pd.DataFrame({"Datetime":pd.to_datetime(d["t"],unit="s",utc=True).tz_localize(None),"Open":d["o"],"High":d["h"],"Low":d["l"],"Close":d["c"],"Volume":d["v"]}))
