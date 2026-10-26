import numpy as np, pandas as pd
def demo_history(symbol="DEMO", days=260):
    """Deterministic, explicitly labelled demonstration data; never used as an automatic fallback."""
    rng=np.random.default_rng(abs(hash(symbol))%(2**32))
    dates=pd.bdate_range(end=pd.Timestamp.today().normalize(),periods=days)
    close=100*np.exp(np.cumsum(rng.normal(.0004,.015,days)))
    open_=close*(1+rng.normal(0,.004,days))
    high=np.maximum(open_,close)*(1+rng.uniform(0,.012,days))
    low=np.minimum(open_,close)*(1-rng.uniform(0,.012,days))
    return pd.DataFrame({"Datetime":dates,"Open":open_,"High":high,"Low":low,"Close":close,"Volume":rng.integers(100000,2000000,days)})
