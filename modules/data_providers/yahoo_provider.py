from datetime import datetime, timezone
import pandas as pd
from .base_provider import BaseProvider, ProviderError

class YahooProvider(BaseProvider):
    name = "Yahoo Finance"
    def _ticker(self, symbol):
        try:
            import yfinance as yf
        except ImportError as e:
            raise ProviderError("Install yfinance to use Yahoo Finance.") from e
        return yf.Ticker(symbol), yf
    def get_quote(self, symbol):
        ticker, yf = self._ticker(symbol)
        try:
            info = ticker.fast_info
            hist = ticker.history(period="5d", interval="1d", auto_adjust=False)
            if hist.empty: raise ProviderError(f"No quote/history available for {symbol}.")
            last = hist.iloc[-1]
            prev = hist.iloc[-2]["Close"] if len(hist) > 1 else info.get("previous_close", last["Close"])
            ts = hist.index[-1]
            return {"symbol":symbol.upper(),"name":symbol.upper(),"price":float(last["Close"]),
                "change":float(last["Close"]-prev) if pd.notna(prev) else None,
                "change_percent":float((last["Close"]-prev)/prev*100) if prev else None,
                "open":float(last["Open"]),"high":float(last["High"]),"low":float(last["Low"]),
                "previous_close":float(prev) if pd.notna(prev) else None,
                "volume":int(last["Volume"]) if pd.notna(last["Volume"]) else None,
                "currency":info.get("currency","") or "Unknown","exchange":info.get("exchange","") or "Unknown",
                "market_timestamp":str(ts),"retrieved_at":datetime.now(timezone.utc).isoformat(),
                "freshness":"LATEST AVAILABLE QUOTE","provider":self.name}
        except ProviderError: raise
        except Exception as e: raise ProviderError(f"Yahoo Finance quote failed: {e}") from e
    def get_history(self, symbol, period="1y", interval="1d", start=None, end=None):
        ticker, yf = self._ticker(symbol)
        try:
            kw={"interval":interval,"auto_adjust":False}
            if start: kw["start"]=start
            if end: kw["end"]=end
            if not start: kw["period"]=period
            return self.normalize_history(ticker.history(**kw))
        except Exception as e: raise ProviderError(f"Yahoo Finance history failed: {e}") from e
    def search_symbols(self, query):
        try:
            import yfinance as yf
            result=yf.Search(query, max_results=8)
            return [{"symbol":x.get("symbol",""),"name":x.get("shortname") or x.get("longname") or x.get("symbol","")} for x in result.quotes]
        except Exception: return super().search_symbols(query)
