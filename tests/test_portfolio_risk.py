import unittest
from modules.analytics import performance_metrics
from services.data_service import demo_history
class PortfolioRiskTests(unittest.TestCase):
    def test_risk_metrics_are_finite(self):
        result=performance_metrics(demo_history("RISK",120))
        for key in ("Total return","Annualized volatility","Maximum drawdown","Historical VaR 95%","Historical CVaR 95%"):
            self.assertIn(key,result)
            self.assertTrue(abs(result[key])<10000)
if __name__=="__main__": unittest.main()
