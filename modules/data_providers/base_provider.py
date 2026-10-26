from abc import ABC, abstractmethod
from datetime import datetime, timezone
import pandas as pd

class ProviderError(RuntimeError):
    pass

class BaseProvider(ABC):
    name = "Base"
    def status(self):
        return {"provider": self.name, "status": "configured"}
    @abstractmethod
    def get_quote(self, symbol): ...
    @abstractmethod
    def get_history(self, symbol, period="1y", interval="1d", start=None, end=None): ...
    def search_symbols(self, query):
        return [{"symbol": query.upper(), "name": query.upper()}] if query else []
    @staticmethod
    def normalize_history(df):
        if df is None or len(df) == 0:
            raise ProviderError("Provider returned no historical observations.")
        df = df.copy()
        df.columns = [str(c).strip().title() for c in df.columns]
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [str(c[-1]).title() for c in df.columns]
        aliases = {"Datetime":"Datetime", "Date":"Datetime", "Timestamp":"Datetime",
                   "Adj Close":"Adj Close", "Open":"Open", "High":"High", "Low":"Low",
                   "Close":"Close", "Volume":"Volume"}
        rename = {c: aliases[c] for c in df.columns if c in aliases}
        df = df.rename(columns=rename)
        if "Datetime" not in df.columns:
            idx = df.index
            df["Datetime"] = pd.to_datetime(idx, utc=True, errors="coerce").tz_localize(None) if getattr(idx, "tz", None) else pd.to_datetime(idx, errors="coerce")
        else:
            df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce", utc=True).dt.tz_localize(None)
        required = ["Open","High","Low","Close"]
        missing = [c for c in required if c not in df.columns]
        if missing: raise ProviderError("Missing OHLC columns: " + ", ".join(missing))
        if "Volume" not in df.columns: df["Volume"] = pd.NA
        for c in required + ["Volume"]:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = df.dropna(subset=["Datetime","Open","High","Low","Close"]).sort_values("Datetime")
        df = df.drop_duplicates("Datetime", keep="last")
        if df.empty: raise ProviderError("No valid OHLC observations were returned.")
        return df[["Datetime","Open","High","Low","Close","Volume"]].reset_index(drop=True)
