import unittest
import pandas as pd
from modules.data_providers.base_provider import BaseProvider, ProviderError
class NormalizeTests(unittest.TestCase):
    def test_normalize_ohlcv(self):
        df=pd.DataFrame({"Open":[1],"High":[2],"Low":[.5],"Close":[1.5],"Volume":[100]},index=pd.to_datetime(["2024-01-01"]))
        out=BaseProvider.normalize_history(df)
        self.assertEqual(list(out.columns),["Datetime","Open","High","Low","Close","Volume"])
        self.assertEqual(len(out),1)
    def test_empty_rejected(self):
        with self.assertRaises(ProviderError): BaseProvider.normalize_history(pd.DataFrame())
if __name__=="__main__": unittest.main()
