# TWSE 資料抓取
import requests
from datetime import datetime

def fetch_institutional(date_str: str):
    """
    抓取三大法人買賣超
    date_str 格式：'20261029'
    回傳單位：億元
    """
    url = "https://www.twse.com.tw/rwd/zh/fund/BFI82U"
    params = {
        "response": "json",
        "dayDate": date_str,
        "type": "day"
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        if data.get("stat") != "OK":
            return None

        result = {}
        for row in data["data"]:
            name = row[0]
            net = float(str(row[3]).replace(",", "")) / 1e8  # 轉成億
            if "外資及陸資" in name:
                result["外資"] = round(net, 1)
            elif "投信" in name:
                result["投信"] = round(net, 1)
            elif "自營商(自行買賣)" in name:
                result["自營_自行"] = round(net, 1)
            elif "自營商(避險)" in name:
                result["自營_避險"] = round(net, 1)

        result["自營"] = round(result.get("自營_自行", 0) + result.get("自營_避險", 0), 1)
        return result
    except Exception as e:
        print(f"抓取三大法人失敗 {date_str}: {e}")
        return None


def fetch_market_volume(date_str: str):
    """
    抓取大盤成交金額（億）
    """
    url = "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
    params = {
        "response": "json",
        "date": date_str,
        "type": "ALL"
    }
    try:
        r = requests.get(url, params=params, timeout=30)
        data = r.json()
        if data.get("stat") != "OK":
            return None

        # 尋找成交金額
        for table in data.get("tables", []):
            if "成交金額" in str(table.get("title", "")) or "市場成交資訊" in str(table.get("title", "")):
                for row in table.get("data", []):
                    if len(row) >= 2 and "成交金額" in str(row[0]):
                        value = float(str(row[1]).replace(",", "")) / 1e8
                        return round(value, 1)
        return None
    except Exception as e:
        print(f"抓取成交量失敗 {date_str}: {e}")
        return None
