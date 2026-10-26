from datetime import datetime, timezone
from modules.data_providers.yahoo_provider import YahooProvider
from modules.data_providers.twelve_data_provider import TwelveDataProvider
from modules.data_providers.alpha_vantage_provider import AlphaVantageProvider
from modules.data_providers.finnhub_provider import FinnhubProvider
from modules.data_providers.base_provider import ProviderError
from config.settings import ENABLE_PROVIDER_FAILOVER, API_KEYS

class MarketDataService:
    def __init__(self):
        self.providers={p.name:p for p in [YahooProvider(),TwelveDataProvider(),AlphaVantageProvider(),FinnhubProvider()]}
        self.last_errors={}
    def configured(self, name):
        return name=="Yahoo Finance" or bool(API_KEYS.get(name))
    def provider_status(self):
        return [{"provider":n,"configured":self.configured(n),"status":"ready" if self.configured(n) else "API key missing"} for n in self.providers]
    def _order(self, selected):
        order=[selected] if selected in self.providers else []
        if selected=="Automatic provider selection" or (ENABLE_PROVIDER_FAILOVER and selected in self.providers):
            order += [n for n in self.providers if n not in order]
        return order
    def get_quote(self,symbol,provider="Automatic provider selection"):
        errors=[]
        for name in self._order(provider):
            if not self.configured(name):
                errors.append(f"{name}: API key missing"); continue
            try:
                data=self.providers[name].get_quote(symbol)
                if not data or not isinstance(data.get("price"),(float,int)) or data["price"]<=0: raise ProviderError("Invalid quote response.")
                data["provider"]=name
                data["fallback_used"]=bool(errors and name != provider)
                return data
            except Exception as e:
                errors.append(f"{name}: {e}"); self.last_errors[name]=str(e)
                if provider!="Automatic provider selection" and not ENABLE_PROVIDER_FAILOVER: break
        raise ProviderError("All compatible quote providers failed. " + " | ".join(errors))
    def get_history(self,symbol,provider="Automatic provider selection",period="1y",interval="1d",start=None,end=None):
        errors=[]
        for name in self._order(provider):
            if not self.configured(name):
                errors.append(f"{name}: API key missing"); continue
            try:
                df=self.providers[name].get_history(symbol,period,interval,start,end)
                if df is None or df.empty: raise ProviderError("No historical data returned.")
                return df,name,errors
            except Exception as e:
                errors.append(f"{name}: {e}"); self.last_errors[name]=str(e)
                if provider!="Automatic provider selection" and not ENABLE_PROVIDER_FAILOVER: break
        raise ProviderError("All compatible history providers failed. " + " | ".join(errors))
    def compare_quotes(self,symbol):
        result=[]
        for name in self.providers:
            row={"provider":name,"symbol":symbol,"status":"not checked"}
            if not self.configured(name): row.update(status="API key missing")
            else:
                try: row.update(self.providers[name].get_quote(symbol)); row["status"]="success"
                except Exception as e: row["status"]="error"; row["error"]=str(e)
            result.append(row)
        return result
