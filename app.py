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
st.title("Robo-Advisor: DAT.co (MSTR) 監控平台")
st.markdown("""
監控 MicroStrategy (MSTR) 的估值：
""")

# 載入資料
csv_filename = "MSTR_20250408-20260408_1day.csv"
df = load_and_process_data(csv_filename)

if df is not None:
    # 建立側邊欄設定
    # st.sidebar.header("設定")
    # st.sidebar.info("圖表目前固定顯示 Premium to Equity NAV 與 m_nav 以供對比。")
    
    # 繪製圖表
    st.subheader("MSTR 溢價率對比走勢")
    
    # 建立主折線圖 (Premium to NAV Rigorous)
    fig = px.line(
        df, 
        x="Date", 
        y="Premium_to_NAV_Rigorous", 
        title="MicroStrategy Premium to Equity NAV and m_nav",
        labels={"Premium_to_NAV_Rigorous": "溢價比例", "Date": "日期"}
    )
    
    # 指定主折線的名字為 "Premium to Equity NAV" 並顯示在圖例
    fig.update_traces(name="Premium to Equity NAV", showlegend=True)
    
    # 固定添加 m_nav 折線，不設開關
    fig.add_scatter(
        x=df["Date"], 
        y=df["m_nav"], 
        name="m_nav", 
        line=dict(dash='dot'),
        mode='lines'
    )

    # 添加基準線
    fig.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="NAV 基準線 (1.0)")
    
    # 更新圖例佈局確保易於閱讀
    fig.update_layout(legend_title_text='數據指標')
    
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
    display_cols = ["Date", "close", "market_cap", "btc_holdings", "btc_nav", "debt", "pref", "equity_nav", "Premium_to_NAV_Rigorous", "m_nav"]
    st.dataframe(df[display_cols].sort_values(by="Date", ascending=False))