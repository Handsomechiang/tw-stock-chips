# TAIFEX 資料抓取
from io import StringIO
import pandas as pd
import requests


def fetch_pcr(start_date: str, end_date: str):
  """抓取台指選擇權 Put/Call Ratio 日期格式：'2026/10/27'"""
  url = 'https://www.taifex.com.tw/cht/3/pcRatioDown'
  payload = {'queryStartDate': start_date, 'queryEndDate': end_date}
  try:
    r = requests.post(url, data=payload, timeout=30)
    try:
      text = r.content.decode('big5')
    except:
      text = r.text
    df = pd.read_csv(StringIO(text))
    return df
  except Exception as e:
    print(f'抓取 PCR 失敗: {e}')
    return None


def fetch_taifex_institutional_futures(date_str: str):
  """抓取期貨三大法人未平倉口數 (對應欄位: 外資大小)

  date_str 格式: '2026/10/29'
  """
  url = 'https://www.taifex.com.tw/cht/3/futInstiPositionDown'
  payload = {'queryDate': date_str}
  try:
    r = requests.post(url, data=payload, timeout=30)
    try:
      text = r.content.decode('big5')
    except:
      text = r.text
    df = pd.read_csv(StringIO(text))
    # 尋找外資的未平倉淨口數 (多方口數 - 空方口數)
    # 通常欄位包含 '身份別', '台指期', '多空別' 等
    for _, row in df.iterrows():
      if '外資' in str(row.iloc[0]):  # 身份別
        # 假設欄位有未平倉淨口數，或由 多方未平倉契約金額/口數 減去 空方
        # 這裡以期交所標準欄位為主：通常最後幾欄或特定欄位為未平倉淨口數
        # 為了相容，嘗試尋找淨口數欄位
        pass
    # 簡化回傳範例結構，實際可依期交所 CSV 欄位調整
    return df
  except Exception as e:
    print(f'抓取期貨三大法人失敗 {date_str}: {e}')
    return None


def fetch_top_traders_and_oi(date_str: str):
  """抓取前五大、前十大交易人留倉與台指期總未平倉量 (OI)

  date_str 格式: '2026/10/29'
  """
  # 期交所大額交易人買賣超及未平倉統計網址
  url = 'https://www.taifex.com.tw/cht/3/largeTraderFutQry'  # 或對應的 CSV 下載網址
  # 實際應用中，也可以從每日市場行情總表抓取未平倉總口數
  market_url = 'https://www.taifex.com.tw/cht/2/dailyMarketReport'
  # 這裡提供結構框架，建議使用期交所提供的 CSV 下載介面
  return {
      "前五大交易人留倉": 0,
      "前十大交易人留倉": 0,
      "未平倉口數": 0,
      "外(選)": 0,
  }
