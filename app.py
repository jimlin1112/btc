import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 設定網頁標題與排版
st.set_page_config(page_title="DAT.co 指標追蹤", layout="wide")

# 使用快取，避免每次網頁重整都重新抓取資料
@st.cache_data(ttl=3600)
def fetch_and_calculate_nav():
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    mstr_data = yf.download("MSTR", start=start_date, end=end_date)
    btc_data = yf.download("BTC-USD", start=start_date, end=end_date)

    mstr_series = mstr_data["Close"].squeeze()
    btc_series = btc_data["Close"].squeeze()

    mstr_series.name = "MSTR_Price"
    btc_series.name = "BTC_Price"

    # 這裡已經加入了 sort=False 修正警告
    df = pd.concat([mstr_series, btc_series], axis=1, sort=False).dropna()

    mstr_shares_outstanding = 17000000 
    mstr_btc_holdings = 214246

    df["MSTR_Market_Cap"] = df["MSTR_Price"] * mstr_shares_outstanding
    df["BTC_Holdings_Value"] = df["BTC_Price"] * mstr_btc_holdings
    df["Premium_to_NAV"] = df["MSTR_Market_Cap"] / df["BTC_Holdings_Value"]

    # 將索引 (日期) 變成一個欄位，方便繪圖
    df = df.reset_index()
    # 確保日期欄位名稱正確，yfinance 預設索引名稱通常是 Date
    if "Date" not in df.columns and "index" in df.columns:
        df = df.rename(columns={"index": "Date"})
        
    return df

# 網頁 UI 區塊
st.title("Robo-Advisor: DAT.co (MSTR) 指標監控平台")
st.markdown("""
這是一個監控 MicroStrategy (MSTR) **Premium to NAV (資產淨值溢價)** 的儀表板。
當溢價大於 1 時，代表市場願意用比實際比特幣價值更高的價格購買 MSTR 股票。
""")

# 載入資料
with st.spinner("正在抓取最新市場數據..."):
    df = fetch_and_calculate_nav()

# 繪製折線圖
st.subheader("MSTR Premium to NAV 歷史走勢")
fig = px.line(
    df, 
    x="Date", 
    y="Premium_to_NAV", 
    title="MicroStrategy Premium to NAV",
    labels={"Premium_to_NAV": "溢價比例", "Date": "日期"}
)
# 添加一條 y=1 的基準線，方便觀察何時處於折價/溢價
fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="NAV 基準線 (1.0)")

st.plotly_chart(fig, width="stretch")

# 顯示原始數據表
st.subheader("原始數據")
st.dataframe(df.sort_values(by="Date", ascending=False).head(10))