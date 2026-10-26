import unittest
from modules.data_providers.yahoo_provider import YahooProvider
from modules.data_providers.twelve_data_provider import TwelveDataProvider
from modules.data_providers.alpha_vantage_provider import AlphaVantageProvider
from modules.data_providers.finnhub_provider import FinnhubProvider
class ProviderTests(unittest.TestCase):
    def test_providers_import_and_status(self):
        for p in (YahooProvider(),TwelveDataProvider(),AlphaVantageProvider(),FinnhubProvider()):
            self.assertTrue(p.name)
    def test_missing_credentials_reported(self):
        for p in (TwelveDataProvider(),AlphaVantageProvider(),FinnhubProvider()):
            if not p.key:
                with self.assertRaises(Exception): p.get_quote("AAPL")
if __name__=="__main__": unittest.main()
