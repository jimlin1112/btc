import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 設定網頁標題與排版
st.set_page_config(page_title="DAT.co 高級指標追蹤", layout="wide")

@st.cache_data(ttl=3600)
def load_and_process_data(file_path):
    try:
        # 讀取 CSV 檔案
        df = pd.read_csv(file_path)
        
        # 標準化日期格式
        df["Date"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None).dt.normalize()
        
        # 1. 動態計算流通股數 (反映 ATM 增資稀釋狀況)
        # 公式：市值 / 收盤價
        df["implied_shares"] = df["market_cap"] / df["close"]
        
        # 2. 嚴謹的資產淨值 (Equity NAV) 計算
        # 考慮了資產負債表上的債務 (debt) 與優先股 (pref)
        # 公式：比特幣持倉價值 - 總債務 - 優先股
        df["equity_nav"] = df["btc_nav"] - df["debt"] - df["pref"]
        
        # 3. 計算嚴謹溢價率 (Rigorous Premium to NAV)
        # 公式：市值 / 股東權益淨值
        df["Premium_to_NAV_Rigorous"] = df["market_cap"] / df["equity_nav"]
        
        # 排序日期
        df = df.sort_values(by="Date")
        
        return df
    except FileNotFoundError:
        st.error(f"找不到檔案: {file_path}")
        return None

# 網頁 UI 區塊
st.title("Robo-Advisor: DAT.co (MSTR) 專業監控平台")
st.markdown("""
本儀表板採用更嚴謹的財務模型監控 MicroStrategy (MSTR) 的估值：
* **動態股本**：追蹤每日流通股數變化。
* **權益淨值 (Equity NAV)**：扣除公司債務與優先股後的真實比特幣價值。
""")

# 載入資料
csv_filename = "MSTR_20250408-20260408_1day.csv"
df = load_and_process_data(csv_filename)

if df is not None:
    # 建立側邊欄過濾器
    st.sidebar.header("設定")
    show_raw_nav = st.sidebar.checkbox("顯示原始 m_nav (CSV 預設)", value=True)
    
    # 繪製折線圖
    st.subheader("MSTR 嚴謹溢價率走勢 (Premium to Equity NAV)")
    
    # 準備繪圖資料
    fig = px.line(
        df, 
        x="Date", 
        y="Premium_to_NAV_Rigorous", 
        title="MicroStrategy Premium to Equity NAV (Adjusted for Debt & Preferred Stock)",
        labels={"Premium_to_NAV_Rigorous": "嚴謹溢價比例", "Date": "日期"}
    )
    
    if show_raw_nav:
        fig.add_scatter(x=df["Date"], y=df["m_nav"], name="CSV 預設 m_nav", line=dict(dash='dot'))

    fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="NAV 基準線 (1.0)")
    st.plotly_chart(fig, use_container_width=True)

    # 顯示關鍵數據指標
    col1, col2, col3, col4 = st.columns(4)
    latest = df.iloc[-1]
    col1.metric("最新收盤價", f"${latest['close']:,.2f}")
    col2.metric("比特幣持有量", f"{latest['btc_holdings']:,} BTC")
    col3.metric("總債務 (Debt)", f"${latest['debt']/1e9:.2f}B")
    col4.metric("嚴謹溢價率", f"{latest['Premium_to_NAV_Rigorous']:.2f}x")

    # 顯示數據表
    st.subheader("詳細財務數據")
    display_cols = ["Date", "close", "market_cap", "btc_holdings", "btc_nav", "debt", "pref", "equity_nav", "Premium_to_NAV_Rigorous"]
    st.dataframe(df[display_cols].sort_values(by="Date", ascending=False))