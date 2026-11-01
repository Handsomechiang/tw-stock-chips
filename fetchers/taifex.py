# TAIFEX 資料抓取
import requests
import pandas as pd
from io import StringIO

def fetch_pcr(start_date: str, end_date: str):
    """
    抓取台指選擇權 Put/Call Ratio
    日期格式：'2026/10/27'
    """
    url = "https://www.taifex.com.tw/cht/3/pcRatioDown"
    payload = {
        "queryStartDate": start_date,
        "queryEndDate": end_date
    }
    try:
        r = requests.post(url, data=payload, timeout=30)
        # 嘗試不同編碼
        try:
            text = r.content.decode("big5")
        except:
            text = r.text

        df = pd.read_csv(StringIO(text))
        return df
    except Exception as e:
        print(f"抓取 PCR 失敗: {e}")
        return None
