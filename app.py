import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config.settings import APP_NAME, DEFAULT_DATA_PROVIDER, CACHE_TTL_SECONDS
from services.market_data_service import MarketDataService
from services.data_service import demo_history
from services.storage_service import get_watchlist, add_watchlist, remove_watchlist, get_holdings, save_holding, remove_holding, save_analysis
from modules.analytics import add_indicators, performance_metrics, volume_anomalies, trend_prediction
from modules.sentiment_analysis import classify_text
from modules.manipulation_screening import screen_market_movements
from modules.stock_chatbot import answer_question

st.set_page_config(page_title=APP_NAME, page_icon="📈", layout="wide", initial_sidebar_state="expanded")
css = Path(__file__).parent / "assets" / "style.css"
st.markdown(css.read_text(encoding="utf-8"), unsafe_allow_html=True)

# Consistent dark theme for Streamlit components
st.markdown("""
<style>
:root {
    color-scheme: dark;
}
.stApp {
    background-color: #0b0f19 !important;
    color: #e5e7eb !important;
}
[data-testid="stSidebar"] {
    background: #111827 !important;
    border-right: 1px solid #263244;
}
[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stApp p, .stApp label, .stApp .stMarkdown,
.stApp .stCaption, .stApp [data-testid="stCaptionContainer"] {
    color: #e5e7eb;
}
.stApp input, .stApp textarea {
    background-color: #1f2937 !important;
    color: #f9fafb !important;
    border: 1px solid #374151 !important;
}
.stApp [data-baseweb="select"] > div {
    background-color: #1f2937 !important;
    color: #f9fafb !important;
    border-color: #374151 !important;
}
[data-baseweb="popover"], [data-baseweb="menu"], [data-baseweb="listbox"] {
    background-color: #1f2937 !important;
    color: #f9fafb !important;
}
[data-baseweb="menu"] *, [data-baseweb="listbox"] * {
    color: #f9fafb !important;
}
.stApp button {
    color: #f9fafb !important;
    border-color: #374151;
}
[data-testid="stMetric"] {
    background-color: #111827 !important;
    border: 1px solid #263244 !important;
    border-radius: 12px !important;
    padding: 12px !important;
}
[data-testid="stAlert"], [data-testid="stExpander"] {
    background-color: #111827 !important;
    color: #e5e7eb !important;
    border-color: #374151 !important;
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
    color: #e5e7eb !important;
}
.stApp a { color: #60a5fa !important; }
.stApp hr { border-color: #374151 !important; }
</style>
""", unsafe_allow_html=True)

service=MarketDataService()

if "symbol" not in st.session_state: st.session_state.symbol="AAPL"
if "provider" not in st.session_state: st.session_state.provider=DEFAULT_DATA_PROVIDER
if "history_cache" not in st.session_state: st.session_state.history_cache=None
if "quote_cache" not in st.session_state: st.session_state.quote_cache=None

PAGES=["Overview","Live Market","Historical Analysis","AI Predictions","Volume Anomalies","News & Sentiment","Explainable AI","Portfolio Risk","Market Anomalies","Stock AI Chatbot","Sector Rotation","Provider Comparison","Settings"]
with st.sidebar:
    st.markdown("## 📈 Smart Stock AI")
    st.caption("Market intelligence workspace")
    page=st.radio("NAVIGATION",PAGES,label_visibility="collapsed")
    st.divider()
    symbol=st.text_input("Stock symbol",value=st.session_state.symbol,help="Examples: RELIANCE.NS, TCS.NS, AAPL, MSFT").strip().upper()
    if symbol: st.session_state.symbol=symbol
    provider_options=["Automatic provider selection"]+list(service.providers.keys())
    provider=st.selectbox("Data provider",provider_options,index=provider_options.index(st.session_state.provider) if st.session_state.provider in provider_options else 0)
    st.session_state.provider=provider
    period=st.selectbox("History range",["1mo","3mo","6mo","1y","2y","5y","max"],index=3)
    interval=st.selectbox("Interval",["1d","1wk","1mo","1h","30m","15m","5m"],index=0)
    demo=st.toggle("Demonstration mode",value=False,help="Uses clearly labelled synthetic data; never an automatic fallback.")
    if st.button("↻ Refresh data",use_container_width=True):
        st.session_state.history_cache=None; st.session_state.quote_cache=None
    refresh_interval=st.selectbox("Auto-refresh",["Off","15 seconds","30 seconds","60 seconds"],index=0)
    if refresh_interval!="Off" and st_autorefresh:
        st_autorefresh(interval=int(refresh_interval.split()[0])*1000,key="market_auto_refresh")
    elif refresh_interval!="Off" and not st_autorefresh:
        st.caption("Install streamlit-autorefresh to enable timed refresh.")
    st.divider()
    st.caption("Market data may be delayed or unavailable. Not investment advice.")

def load_history(force=False):
    key=(st.session_state.symbol,st.session_state.provider,period,interval,demo)
    if not force and st.session_state.history_cache and st.session_state.history_cache[0]==key:
        return st.session_state.history_cache[1],st.session_state.history_cache[2],st.session_state.history_cache[3]
    if demo:
        df=demo_history(st.session_state.symbol,260 if period in ("1y","2y","5y","max") else 60)
        result=(df,"Demonstration","DEMONSTRATION")
    else:
        try:
            df,actual,errors=service.get_history(st.session_state.symbol,st.session_state.provider,period,interval)
            result=(df,actual,"CACHED" if False else "HISTORICAL")
            if errors: st.warning("Provider fallback used: "+" | ".join(errors))
        except Exception as e:
            return None,None,str(e)
    st.session_state.history_cache=(key,*result)
    return result

def load_quote(force=False):
    if demo:
        df,_,_=load_history()
        if df is None: return None
        last=df.iloc[-1]; prev=df.iloc[-2]
        return {"symbol":st.session_state.symbol,"name":st.session_state.symbol,"price":float(last.Close),
            "change":float(last.Close-prev.Close),"change_percent":float((last.Close/prev.Close-1)*100),
            "open":float(last.Open),"high":float(last.High),"low":float(last.Low),"previous_close":float(prev.Close),
            "volume":int(last.Volume),"currency":"DEMO","exchange":"DEMO","market_timestamp":str(last.Datetime),
            "retrieved_at":pd.Timestamp.now(tz="UTC").isoformat(),"freshness":"DEMONSTRATION","provider":"Demonstration"}
    if not force and st.session_state.quote_cache and st.session_state.quote_cache.get("symbol")==st.session_state.symbol and st.session_state.quote_cache.get("provider")==st.session_state.provider:
        return st.session_state.quote_cache
    try:
        q=service.get_quote(st.session_state.symbol,st.session_state.provider)
        st.session_state.quote_cache=q
        if q.get("fallback_used"): st.warning(f"Fallback provider used: {q['provider']}")
        return q
    except Exception as e:
        st.info("Quote unavailable: "+str(e))
        return None

def show_header(title, subtitle=""):
    st.title(title)
    if subtitle: st.caption(subtitle)

def chart_history(df, chart_type="Line", indicators=True):
    d=add_indicators(df) if indicators else df.copy()
    fig=go.Figure()
    if chart_type=="Candlestick":
        fig.add_trace(go.Candlestick(x=d.Datetime,open=d.Open,high=d.High,low=d.Low,close=d.Close,name="Price"))
    elif chart_type=="OHLC":
        fig.add_trace(go.Ohlc(x=d.Datetime,open=d.Open,high=d.High,low=d.Low,close=d.Close,name="OHLC"))
    else: fig.add_trace(go.Scatter(x=d.Datetime,y=d.Close,mode="lines",name="Close",line=dict(width=2)))
    if indicators and chart_type=="Line":
        for col in ["SMA 20","SMA 50","BB Upper","BB Lower"]:
            if col in d: fig.add_trace(go.Scatter(x=d.Datetime,y=d[col],mode="lines",name=col,line=dict(width=1,dash="dot" if col.startswith("BB") else "solid")))
    fig.update_layout(height=470,margin=dict(l=8,r=8,t=24,b=8),hovermode="x unified",legend=dict(orientation="h",y=1.04),xaxis_title=None,yaxis_title="Price",template="plotly_dark")
    st.plotly_chart(fig,use_container_width=True)
    return d

def current_data():
    return load_history()

if page=="Overview":
    show_header("Market overview","A focused workspace for quotes, historical behaviour, and model-assisted analysis.")
    q=load_quote()
    if q:
        st.markdown(f"### {q['symbol']}  <span class='badge'>{q.get('freshness','LATEST AVAILABLE QUOTE')}</span>",unsafe_allow_html=True)
        st.caption(f"{q.get('name',q['symbol'])} · {q.get('exchange','')} · Source: {q.get('provider','')} · Market timestamp: {q.get('market_timestamp','Unknown')}")
        c=st.columns(4)
        c[0].metric("Latest price",f"{q.get('currency','')} {q['price']:,.2f}",f"{q.get('change',0):+,.2f}")
        c[1].metric("Daily change",f"{q.get('change_percent',0):+.2f}%")
        c[2].metric("Volume",f"{q['volume']:,}" if q.get("volume") is not None else "Unavailable")
        df,actual,status=load_history()
        if df is not None:
            m=performance_metrics(df)
            c[3].metric("Annualized volatility",f"{m.get('Annualized volatility',0):.2f}%")
            chart_history(df)
            st.caption(f"History source: {actual} · Data status: {status} · Latest observation: {df.Datetime.iloc[-1]}")
        else: st.warning(status)
    else:
        st.info("Enter a symbol and choose a provider. You can enable Demonstration mode to explore the interface without external market data.")
    left,right=st.columns([1.1,1])
    with left:
        st.subheader("Watchlist")
        wl=get_watchlist()
        add_symbol=st.text_input("Add symbol to watchlist",key="wl_add")
        if st.button("Add to watchlist") and add_symbol: add_watchlist(add_symbol); st.rerun()
        if wl:
            for s in wl:
                a,b=st.columns([4,1]); a.write(s)
                if b.button("Remove",key="rm"+s): remove_watchlist(s); st.rerun()
        else: st.caption("Your saved symbols will appear here.")
    with right:
        st.subheader("Quick start")
        st.markdown("1. Pick a ticker and provider in the sidebar.\n2. Review quote freshness before interpreting a price.\n3. Explore historical indicators and AI tools from navigation.\n4. Export historical observations as CSV.")

elif page=="Live Market":
    show_header("Live market","Latest available quote and periodic refresh. Periodic polling is not a streaming feed.")
    q=load_quote(force=True)
    if q:
        st.subheader(f"{q['symbol']} · {q.get('name',q['symbol'])}")
        st.markdown(f"<span class='badge'>{q.get('freshness','LATEST AVAILABLE QUOTE')}</span> <span class='badge'>Source: {q.get('provider','')}</span>",unsafe_allow_html=True)
        cols=st.columns(4)
        cols[0].metric("Price",f"{q.get('currency','')} {q['price']:,.2f}",f"{q.get('change',0):+,.2f}")
        cols[1].metric("Change",f"{q.get('change_percent',0):+.2f}%")
        cols[2].metric("Day range",f"{q.get('low',0):,.2f} – {q.get('high',0):,.2f}")
        cols[3].metric("Previous close",f"{q.get('previous_close',0):,.2f}")
        cols=st.columns(3); cols[0].write(f"**Open:** {q.get('open','Unavailable')}"); cols[1].write(f"**Volume:** {q.get('volume','Unavailable')}"); cols[2].write(f"**Currency / exchange:** {q.get('currency','Unknown')} / {q.get('exchange','Unknown')}")
        st.caption(f"Market timestamp: {q.get('market_timestamp','Unknown')} · Retrieved: {q.get('retrieved_at','Unknown')}")
        df,actual,status=load_history()
        if df is not None: chart_history(df,"Line",False)
    else: st.warning("No quote available. Check the symbol, connection, provider permissions, or API keys.")

elif page=="Historical Analysis":
    show_header("Historical analysis","Inspect validated observations, technical indicators, and downloadable data.")
    df,actual,status=load_history()
    if df is None: st.error(status)
    else:
        st.caption(f"Provider: {actual} · Status: {status} · {len(df):,} observations · latest: {df.Datetime.iloc[-1]}")
        c1,c2=st.columns([1,1]); chart_type=c1.selectbox("Chart type",["Line","Candlestick","OHLC"]); show_ind=c2.toggle("Technical overlays",True)
        d=chart_history(df,chart_type,show_ind)
        tab1,tab2,tab3=st.tabs(["Price data","Indicators","Returns & risk"])
        with tab1:
            st.dataframe(df.sort_values("Datetime",ascending=False),use_container_width=True,hide_index=True)
            st.download_button("Download CSV",df.to_csv(index=False).encode("utf-8"),file_name=f"{st.session_state.symbol}_history.csv",mime="text/csv")
        with tab2:
            ind=add_indicators(df)
            st.line_chart(ind.set_index("Datetime")[["RSI","MACD","MACD Signal"]].tail(180))
            st.dataframe(ind[["Datetime","SMA 20","SMA 50","EMA 20","RSI","MACD","MACD Signal","BB Upper","BB Lower"]].tail(100),use_container_width=True,hide_index=True)
        with tab3:
            m=performance_metrics(df); cols=st.columns(len(m))
            for col,(k,v) in zip(cols,m.items()): col.metric(k,f"{v:.2f}%")
            ind=add_indicators(df); st.plotly_chart(px.line(ind,x="Datetime",y="Cumulative Return",title="Cumulative return (loaded period)"),use_container_width=True)
            st.plotly_chart(px.line(ind,x="Datetime",y="Drawdown",title="Historical drawdown"),use_container_width=True)

elif page=="AI Predictions":
    show_header("AI predictions","A baseline Random Forest model with chronological holdout evaluation. Estimates are not guarantees.")
    df,actual,status=load_history()
    if df is not None:
        with st.spinner("Training baseline model on loaded historical data…"):
            try: result=trend_prediction(df)
            except Exception as e: result={"error":str(e)}
        if result.get("error"): st.warning(result["error"])
        else:
            c=st.columns(4); c[0].metric("Estimated next close",f"{result['prediction']:.2f}"); c[1].metric("Model direction",result["trend"]); c[2].metric("Holdout MAE",f"{result['mae']:.3f}"); c[3].metric("Holdout RMSE",f"{result['rmse']:.3f}")
            st.metric("Estimated change vs latest close",f"{result['change_pct']:+.2f}%")
            st.caption(f"Model evaluated on {result['test_rows']} chronological holdout rows. This is a baseline experiment, not evidence of trading profitability.")
            fig=go.Figure(); fig.add_trace(go.Scatter(x=result["test_dates"],y=result["test_actual"],name="Actual next close")); fig.add_trace(go.Scatter(x=result["test_dates"],y=result["test_predicted"],name="Predicted",mode="lines"))
            fig.update_layout(title="Chronological holdout: actual vs predicted",height=400,template="plotly_dark")
            st.plotly_chart(fig,use_container_width=True)
            st.bar_chart(pd.Series(result["importance"]).sort_values())
            save_analysis(st.session_state.symbol,"trend_prediction",{k:v for k,v in result.items() if k not in ("test_actual","test_predicted","test_dates")})
    else: st.error(status)

elif page=="Volume Anomalies":
    show_header("Volume anomalies","Statistical outlier screening. Ordinary volume is not delivery data.")
    df,actual,status=load_history()
    if df is not None:
        d=volume_anomalies(df)
        st.caption(f"Source: {actual}. Flags are statistical screening signals, not evidence of manipulation.")
        fig=px.scatter(d,x="Datetime",y="Volume",color=d["Anomaly"].map({True:"Flagged",False:"Typical"}),title="Volume observations and rolling outlier flags")
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(d[d["Anomaly"]].tail(100),use_container_width=True,hide_index=True)
        st.info("Delivery quantity and delivery percentage are intentionally not shown because ordinary OHLCV data does not verify them.")
    else: st.error(status)

elif page=="News & Sentiment":
    show_header("News & sentiment","Paste headlines or financial text. This transparent keyword fallback does not fetch or invent news.")
    text=st.text_area("Headline or article text",height=180,placeholder="Paste a real headline or short article here…")
    if st.button("Analyze sentiment",type="primary") and text.strip():
        r=classify_text(text)
        c=st.columns(3); c[0].metric("Sentiment",r["label"]); c[1].metric("Score",f"{r['score']:+.2f}"); c[2].metric("Method",r["method"])
        st.write("Positive terms:",", ".join(r["matched_positive"]) or "None")
        st.write("Negative terms:",", ".join(r["matched_negative"]) or "None")
        st.caption("This is a simple lexical baseline. It may miss context, sarcasm, negation, and financial nuance.")

elif page=="Explainable AI":
    show_header("Explainable AI","Feature importance from the trained baseline model; SHAP is optional and not claimed unless available.")
    df,actual,status=load_history()
    if df is not None:
        try:
            r=trend_prediction(df)
            if r.get("error"): st.warning(r["error"])
            else:
                st.subheader("Global feature importance")
                imp=pd.DataFrame({"Feature":list(r["importance"]),"Importance":list(r["importance"].values())}).sort_values("Importance")
                st.plotly_chart(px.bar(imp,x="Importance",y="Feature",orientation="h"),use_container_width=True)
                st.caption("These importances describe this fitted Random Forest, not causal drivers of market prices.")
                st.subheader("What the inputs represent")
                st.markdown("- **Lag1 / Lag5:** recent price returns.\n- **SMA ratio:** close relative to its 20-observation moving average.\n- **RSI:** momentum oscillator.\n- **Volatility 20D:** annualized rolling return variability.")
        except Exception as e: st.error(str(e))
    else: st.error(status)

elif page=="Portfolio Risk":
    show_header("Portfolio risk","Save holdings locally and estimate risk from aligned historical returns where available.")
    with st.form("holding_form"):
        a,b,c=st.columns(3); hs=a.text_input("Symbol",value=st.session_state.symbol); qty=b.number_input("Quantity",min_value=0.0,value=1.0,step=1.0); cost=c.number_input("Purchase price",min_value=0.0,value=100.0)
        submit=st.form_submit_button("Save holding")
    if submit and hs: save_holding(hs,qty,cost); st.rerun()
    holdings=get_holdings()
    if holdings:
        st.dataframe(pd.DataFrame(holdings),use_container_width=True,hide_index=True)
        for h in holdings:
            if st.button("Remove "+h["symbol"],key="holding_rm_"+h["symbol"]): remove_holding(h["symbol"]); st.rerun()
        st.subheader("Loaded-symbol risk snapshot")
        df,actual,status=load_history()
        if df is not None:
            m=performance_metrics(df); cols=st.columns(len(m))
            for col,(k,v) in zip(cols,m.items()): col.metric(k,f"{v:.2f}%")
            st.caption("These metrics describe the currently loaded symbol only. A true multi-asset portfolio estimate requires aligned return series and portfolio weights.")
    else: st.info("Add one or more holdings above to persist them in the local SQLite database.")

elif page=="Market Anomalies":
    show_header("Market anomalies","Statistical screening of unusual price moves, volume, and volatility. No allegation of misconduct is inferred.")
    df,actual,status=load_history()
    if df is not None:
        d=screen_market_movements(df)
        st.metric("Flagged observations",int(d["Screen flag"].fillna(False).sum()))
        st.plotly_chart(px.scatter(d,x="Datetime",y="Close",color=d["Screen flag"].map({True:"Flagged",False:"Typical"}),title="Screened market observations"),use_container_width=True)
        st.dataframe(d[d["Screen flag"].fillna(False)].tail(100),use_container_width=True,hide_index=True)
    else: st.error(status)

elif page=="Stock AI Chatbot":
    show_header("Stock AI chatbot","Rule-based responses grounded in the currently loaded historical data.")
    df,actual,status=load_history()
    if "chat_messages" not in st.session_state: st.session_state.chat_messages=[]
    for m in st.session_state.chat_messages:
        with st.chat_message(m["role"]): st.write(m["content"])
    question=st.chat_input("Ask about price, trend, return, high, low, or volume…")
    if question:
        st.session_state.chat_messages.append({"role":"user","content":question})
        response=answer_question(question,st.session_state.symbol,df)
        st.session_state.chat_messages.append({"role":"assistant","content":response})
        st.rerun()
    if df is None: st.warning(status)

elif page=="Sector Rotation":
    show_header("Sector rotation","Compare sector ETFs as a practical proxy. Availability depends on your chosen data provider.")
    tickers={"Technology":"XLK","Financials":"XLF","Energy":"XLE","Healthcare":"XLV","Industrials":"XLI","Consumer discretionary":"XLY","Utilities":"XLU"}
    rows=[]; errors=[]
    if st.button("Load sector comparison",type="primary"):
        with st.spinner("Fetching sector proxy histories…"):
            for sector,ticker in tickers.items():
                try:
                    d,p,errs=service.get_history(ticker,st.session_state.provider,"6mo","1d")
                    rows.append({"Sector":sector,"Proxy":ticker,"Return %":(d.Close.iloc[-1]/d.Close.iloc[0]-1)*100,"Volatility %":d.Close.pct_change().std()*np.sqrt(252)*100,"Provider":p})
                except Exception as e: errors.append(f"{sector} ({ticker}): {e}")
        if rows:
            out=pd.DataFrame(rows).sort_values("Return %",ascending=False); st.dataframe(out,use_container_width=True,hide_index=True)
            st.plotly_chart(px.bar(out,x="Sector",y="Return %",color="Return %",title="Sector ETF proxy return over loaded period"),use_container_width=True)
        if errors: st.warning("Some sector proxies were unavailable: "+" | ".join(errors))
    st.caption("These are sector ETF proxies, not a complete classification of all market sectors. Rankings are historical, not forecasts.")

elif page=="Provider Comparison":
    show_header("Provider comparison","Responses are requested independently. Compare only when symbol, currency, session, and timestamps align.")
    if st.button("Compare providers",type="primary"):
        with st.spinner("Querying configured providers…"):
            rows=service.compare_quotes(st.session_state.symbol)
        out=[]
        for r in rows:
            out.append({"Provider":r["provider"],"Symbol":r.get("symbol",st.session_state.symbol),"Latest price":r.get("price"),"Currency":r.get("currency"),"Market timestamp":r.get("market_timestamp"),"Retrieval timestamp":r.get("retrieved_at"),"Data status":r.get("freshness"),"Provider status":r["status"],"Error":r.get("error")})
        st.dataframe(pd.DataFrame(out),use_container_width=True,hide_index=True)
        st.caption("Providers may differ due to exchange coverage, quote delay, adjusted/unadjusted prices, session timing, and subscription entitlements. Unavailable is not zero.")

elif page=="Settings":
    show_header("Settings","Provider readiness, local preferences, and operating notes.")
    st.subheader("Provider status")
    st.dataframe(pd.DataFrame(service.provider_status()),use_container_width=True,hide_index=True)
    st.subheader("Environment settings")
    st.write({"Default provider":DEFAULT_DATA_PROVIDER,"Failover enabled":__import__("config.settings",fromlist=["ENABLE_PROVIDER_FAILOVER"]).ENABLE_PROVIDER_FAILOVER,"Cache TTL seconds":CACHE_TTL_SECONDS})
    st.info("API key values are never displayed. Edit the local .env file and restart Streamlit to apply credential changes.")
    st.subheader("Provider limitations")
    st.markdown("- Yahoo Finance (`yfinance`) is unofficial and can fail or return delayed/latest-available observations.\n- Twelve Data, Alpha Vantage, and Finnhub have provider-specific limits and symbol coverage.\n- Missing providers are skipped in automatic mode; no synthetic fallback is used unless Demonstration mode is explicitly enabled.")
