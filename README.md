# Smart Stock AI — Integrated Intelligent Stock Market Analysis Platform

A student-friendly Streamlit application for stock quotes, historical exploration, technical indicators, baseline prediction, anomaly screening, news-text sentiment, portfolio risk, provider comparison, and a data-grounded rule-based chatbot.

## Important data notes
- Yahoo Finance via `yfinance` is an unofficial source. Its availability and quote freshness are not guaranteed.
- Twelve Data, Alpha Vantage, and Finnhub require API keys for protected endpoints; free tiers and exchange permissions vary.
- Periodic refresh is not streaming real-time data. The UI labels provider data as latest available unless its source explicitly supports a stronger claim.
- Delivery percentages are not estimated from ordinary volume. No live news feed is fabricated; sentiment analysis accepts user-provided headlines/text.
- Predictions are estimates and not investment advice. Reported metrics are calculated on a chronological holdout set, not a claim of profitability.
- Demonstration data is available only by explicitly selecting Demonstration mode and is labelled.

## Requirements
Python 3.10+ recommended. Windows, Linux, and macOS supported.

## Windows PowerShell setup
```powershell
cd smart_stock_ai_project
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```
If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process Bypass` in that terminal, then activate again.

## Linux/macOS setup
```bash
cd smart_stock_ai_project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## API configuration
Edit `.env` and set any keys you have:
- `TWELVE_DATA_API_KEY` — register at the official Twelve Data site.
- `ALPHA_VANTAGE_API_KEY` — register at the official Alpha Vantage site.
- `FINNHUB_API_KEY` — register at the official Finnhub site.
Yahoo Finance requires no key but is unofficial. Never put real credentials into source control or share your `.env`.

## How to use
1. Launch the app and enter a ticker such as `RELIANCE.NS`, `TCS.NS`, `INFY.NS`, `AAPL`, `MSFT`, or `NVDA`.
2. Choose a provider or Automatic provider selection. Missing API keys are skipped.
3. Select the date range and interval for historical analysis, then use the chart/table and CSV export.
4. Use AI Predictions for a baseline Random Forest model, Volume Anomalies for statistical outliers, News & Sentiment for text you paste, Explainable AI for feature importance, and Portfolio Risk to manage holdings.
5. Add tickers to the persistent SQLite watchlist.

## Pages
Overview, Live Market, Historical Analysis, AI Predictions, Volume Anomalies, News & Sentiment, Explainable AI, Portfolio Risk, Market Anomalies, Stock AI Chatbot, Sector Rotation, Provider Comparison, and Settings.

## Troubleshooting
- **No data:** check ticker syntax, internet access, market coverage, date range, and provider permissions.
- **Rate limit:** wait before retrying; avoid repeated manual refreshes. Use another provider if configured.
- **Missing key:** add it to `.env`, restart the app, and ensure there are no surrounding quotes/spaces.
- **Install error:** use Python 3.10–3.12 if a dependency has not yet published a wheel for your Python version.
- **Yahoo Finance failures:** the unofficial endpoint can change or be unavailable.

## Tests
Run `python -m unittest discover -s tests -v`. Tests use deterministic data and mocked/local calculations; they do not prove live API availability.
