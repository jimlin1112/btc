import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 設定網頁標題與排版
st.set_page_config(page_title="DAT.co 進階指標追蹤", layout="wide")

@st.cache_data(ttl=3600)
def fetch_and_calculate_nav():
    # 1. 設定時間範圍
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # 2. 抓取 MSTR 與 BTC 價格資料
    mstr_data = yf.download("MSTR", start=start_date, end=end_date)
    btc_data = yf.download("BTC-USD", start=start_date, end=end_date)

    if mstr_data.empty or btc_data.empty:
        return pd.DataFrame()

    mstr_series = mstr_data["Close"].squeeze()
    btc_series = btc_data["Close"].squeeze()
    
    mstr_series.name = "MSTR_Price"
    btc_series.name = "BTC_Price"

    # 合併價格基礎資料表
    df = pd.concat([mstr_series, btc_series], axis=1).dropna()
    df.index = pd.to_datetime(df.index)

    # 3. 取得最新流通股數 (Shares Outstanding)
    try:
        mstr_ticker = yf.Ticker("MSTR")
        # 嘗試從 yfinance 抓取最新股數，若失敗則使用預設估計值
        shares_outstanding = mstr_ticker.info.get('sharesOutstanding', 17000000)
    except:
        shares_outstanding = 17000000

    # 4. 階梯式資料合併 (Step-function Merge)
    # 定義 MSTR 歷史持幣里程碑 (根據公開新聞稿整理之近似數據)
    holdings_milestones = [
        {'Date': '2023-01-01', 'BTC_Holdings': 132500},
        {'Date': '2023-04-05', 'BTC_Holdings': 140000},
        {'Date': '2023-06-28', 'BTC_Holdings': 152333},
        {'Date': '2023-08-01', 'BTC_Holdings': 152800},
        {'Date': '2023-11-30', 'BTC_Holdings': 174530},
        {'Date': '2023-12-27', 'BTC_Holdings': 189150},
        {'Date': '2024-02-26', 'BTC_Holdings': 193000},
        {'Date': '2024-03-11', 'BTC_Holdings': 205000},
        {'Date': '2024-03-19', 'BTC_Holdings': 214246},
    ]
    
    holdings_df = pd.DataFrame(holdings_milestones)
    holdings_df['Date'] = pd.to_datetime(holdings_df['Date'])
    holdings_df.set_index('Date', inplace=True)

    # 將持幣里程碑合併至每日價格資料表中
    df = df.join(holdings_df, how='left')
    
    # 使用 Forward Fill (ffill) 達成階梯式效果
    # 邏輯：在下一次公告購買前，持幣量維持上一次公告的數值
    df['BTC_Holdings'] = df['BTC_Holdings'].ffill()
    # 處理資料起始點之前的空值 (向後填充)
    df['BTC_Holdings'] = df['BTC_Holdings'].bfill()

    # 5. 指標運算
    df["MSTR_Market_Cap"] = df["MSTR_Price"] * shares_outstanding
    df["BTC_Holdings_Value"] = df["BTC_Price"] * df["BTC_Holdings"]
    df["Premium_to_NAV"] = df["MSTR_Market_Cap"] / df["BTC_Holdings_Value"]

    df = df.reset_index()
    if "Date" not in df.columns and "index" in df.columns:
        df = df.rename(columns={"index": "Date"})
        
    return df

# --- 網頁 UI 介面 ---
st.title("Robo-Advisor: DAT.co (MSTR) 進階監控平台")
st.markdown("""
這是一個針對 MicroStrategy (MSTR) 設計的 **Premium to NAV (資產淨值溢價)** 監控儀表板。
**技術亮點：** 採用「階梯式資料合併」演算法，動態重構歷史持幣量，而非使用固定數值，大幅提升歷史溢價計算的準確性。
""")

# 載入並運算資料
with st.spinner("正在執行階梯式資料合併與指標運算..."):
    df = fetch_and_calculate_nav()

if not df.empty:
    # 繪製 Premium to NAV 折線圖
    st.subheader("MSTR Premium to NAV 歷史走勢 (動態持倉修正)")
    fig_premium = px.line(
        df, 
        x="Date", 
        y="Premium_to_NAV", 
        title="MicroStrategy Premium to NAV (Adjusted for Step-Function Holdings)",
        labels={"Premium_to_NAV": "溢價比例", "Date": "日期"}
    )
    fig_premium.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="NAV 基準線 (1.0)")
    st.plotly_chart(fig_premium, use_container_width=True)

    # 繪製持幣量變化圖 (視覺化說明階梯式效果)
    st.subheader("MSTR 比特幣持倉量增長趨勢")
    fig_holdings = px.area(
        df,
        x="Date",
        y="BTC_Holdings",
        title="Historical BTC Holdings (Step-Function Visualization)",
        labels={"BTC_Holdings": "持幣數量", "Date": "日期"}
    )
    st.plotly_chart(fig_holdings, use_container_width=True)

    # 顯示數據表格
    st.subheader("運算原始數據 (前 20 筆)")
    st.dataframe(df.sort_values(by="Date", ascending=False).head(20))
else:
    st.error("無法取得市場數據，請檢查 Yahoo Finance 連線狀態。")