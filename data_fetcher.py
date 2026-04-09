import yfinance as yf
import pandas as pd

def fetch_and_calculate_nav():
    start_date = "2023-01-01"
    end_date = "2024-04-01" 

    print("正在獲取 MSTR 與 BTC 的歷史數據...")
    
    # 1. 抓取 MSTR 與 BTC 的歷史股價/幣價
    mstr_data = yf.download("MSTR", start=start_date, end=end_date)
    btc_data = yf.download("BTC-USD", start=start_date, end=end_date)

    # 確保取得的是一維 Series (解決新版 yfinance 回傳結構問題)
    mstr_series = mstr_data["Close"].squeeze()
    btc_series = btc_data["Close"].squeeze()

    # 重新命名 Series 以便合併後作為欄位名稱
    mstr_series.name = "MSTR_Price"
    btc_series.name = "BTC_Price"

    # 使用 pd.concat 根據日期對齊合併，並移除沒有交集的日期 (例如週末)
    df = pd.concat([mstr_series, btc_series], axis=1, sort=False).dropna()

    # 2. 計算 Premium to NAV (簡化版)
    # 假設 MSTR 的流通股數約為 17,000,000 股
    mstr_shares_outstanding = 17000000 
    
    # 假設 MSTR 持有約 214,246 顆比特幣
    mstr_btc_holdings = 214246

    # 計算每日市值 (Market Cap) 與持有 BTC 價值
    df["MSTR_Market_Cap"] = df["MSTR_Price"] * mstr_shares_outstanding
    df["BTC_Holdings_Value"] = df["BTC_Price"] * mstr_btc_holdings

    # 計算溢價比例 (Premium to NAV)
    df["Premium_to_NAV"] = df["MSTR_Market_Cap"] / df["BTC_Holdings_Value"]

    return df

if __name__ == "__main__":
    nav_df = fetch_and_calculate_nav()
    print("\n資料處理完成！前五筆數據如下：")
    print(nav_df.head())