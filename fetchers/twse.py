# TWSE（證交所）資料抓取
import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (tw-stock-chips daily updater)"}
_volume_cache = {}


def _to_roc(date_str):
  """'20261105' → '115/11/05'"""
  return f"{int(date_str[:4]) - 1911}/{date_str[4:6]}/{date_str[6:]}"


def fetch_institutional(date_str):
  """三大法人買賣超（億元），date_str 格式 '20261105'；查無資料回傳 None"""
  r = requests.get("https://www.twse.com.tw/rwd/zh/fund/BFI82U",
                   params={"response": "json", "dayDate": date_str, "type": "day"},
                   headers=HEADERS, timeout=30)
  data = r.json()
  if data.get("stat") != "OK" or not data.get("data"):
    return None
  result = {}
  for row in data["data"]:
    name = row[0]
    net = float(str(row[3]).replace(",", "")) / 1e8
    if name.startswith("外資及陸資"):
      result["外資"] = round(net, 2)
    elif name == "投信":
      result["投信"] = round(net, 2)
    elif name.startswith("自營商(自行買賣)"):
      result["自營_自行"] = net
    elif name.startswith("自營商(避險)"):
      result["自營_避險"] = net
  result["自營"] = round(result.pop("自營_自行", 0) + result.pop("自營_避險", 0), 2)
  return result


def fetch_market_volume(date_str):
  """大盤成交金額（億元）。用每月大盤統計 FMTQIK，同一個月份只抓一次。"""
  month = date_str[:6]
  if month not in _volume_cache:
    r = requests.get("https://www.twse.com.tw/rwd/zh/afterTrading/FMTQIK",
                     params={"response": "json", "date": month + "01"},
                     headers=HEADERS, timeout=30)
    data = r.json()
    _volume_cache[month] = {row[0]: row for row in data.get("data", [])} if data.get("stat") == "OK" else {}
  row = _volume_cache[month].get(_to_roc(date_str))
  if not row:
    return None
  return round(float(row[2].replace(",", "")) / 1e8, 1)  # 成交金額（元）→ 億
