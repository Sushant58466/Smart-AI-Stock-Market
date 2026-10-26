import unittest
from services.data_service import demo_history
from modules.analytics import add_indicators, performance_metrics, volume_anomalies, trend_prediction
class AnalyticsTests(unittest.TestCase):
    def test_indicators_and_metrics(self):
        df=demo_history("TEST",150)
        out=add_indicators(df)
        self.assertIn("RSI",out); self.assertIn("Drawdown",out)
        m=performance_metrics(df); self.assertIn("Historical VaR 95%",m)
    def test_volume_anomalies(self):
        out=volume_anomalies(demo_history("VOL",100))
        self.assertIn("Anomaly",out)
    def test_prediction_returns_evaluation(self):
        out=trend_prediction(demo_history("PRED",180))
        self.assertTrue("error" in out or ("mae" in out and "rmse" in out))
if __name__=="__main__": unittest.main()
