# TAIFEX（期交所）資料抓取
# 所有下載介面都回傳 Big5 編碼的 CSV，日期格式 'YYYY/MM/DD'
import csv
from io import StringIO

import requests

BASE = "https://www.taifex.com.tw/cht/3"
HEADERS = {"User-Agent": "Mozilla/5.0 (tw-stock-chips daily updater)"}


def _post_csv(path, payload):
  """POST 到期交所下載介面，回傳 list[dict]；查無資料回傳 []"""
  r = requests.post(f"{BASE}/{path}", data=payload, headers=HEADERS, timeout=30)
  r.raise_for_status()
  text = r.content.decode("big5", errors="replace")
  lines = [l for l in text.splitlines() if l.strip()]
  if len(lines) < 2 or "," not in lines[0]:
    return []  # 假日或尚未公布時會回傳 HTML 或只有表頭
  reader = csv.reader(StringIO("\n".join(lines)))
  header = [h.strip() for h in next(reader)]
  rows = []
  for rec in reader:
    rec = [c.strip() for c in rec]
    rows.append(dict(zip(header, rec)))  # 結尾多出的空欄會被自動忽略
  return rows


def _num(s):
  try:
    return float(str(s).replace(",", ""))
  except (TypeError, ValueError):
    return None


def fetch_pcr(date_str):
  """選擇權 Put/Call 未平倉量比率(%)"""
  rows = _post_csv("pcRatioDown", {"queryStartDate": date_str, "queryEndDate": date_str})
  for r in rows:
    if r.get("日期") == date_str:
      return _num(r.get("買賣權未平倉量比率%"))
  return None


def fetch_futures_institutional(date_str):
  """期貨三大法人未平倉（依契約）。回傳 {(商品名稱, 身份別): {'多': 口數, '空': 口數, '淨': 口數}}"""
  rows = _post_csv("futContractsDateDown",
                   {"queryStartDate": date_str, "queryEndDate": date_str, "commodityId": ""})
  out = {}
  for r in rows:
    if r.get("日期") != date_str:
      continue
    out[(r["商品名稱"], r["身份別"])] = {
        "多": _num(r.get("多方未平倉口數")) or 0,
        "空": _num(r.get("空方未平倉口數")) or 0,
        "淨": _num(r.get("多空未平倉口數淨額")) or 0,
    }
  return out


def fetch_options_foreign_net(date_str):
  """外資臺指選擇權未平倉契約金額淨額：CALL 淨額 − PUT 淨額（億元）"""
  rows = _post_csv("callsAndPutsDateDown",
                   {"queryStartDate": date_str, "queryEndDate": date_str, "commodityId": "TXO"})
  call = put = None
  for r in rows:
    if r.get("日期") != date_str or "外資" not in r.get("身份別", ""):
      continue
    v = _num(r.get("未平倉契約金額買賣淨額(千元)"))
    if r.get("買賣權別") == "CALL":
      call = v
    elif r.get("買賣權別") == "PUT":
      put = v
  if call is None or put is None:
    return None
  return round((call - put) / 1e5, 2)  # 千元 → 億元


def fetch_large_traders(date_str):
  """臺股期貨（TX+MTX/4+TMF/20）大額交易人，所有月份合計、全部交易人。
  回傳前五大／前十大淨留倉（買方−賣方）與全市場未沖銷部位數。"""
  rows = _post_csv("largeTraderFutDown", {"queryStartDate": date_str, "queryEndDate": date_str})
  for r in rows:
    if (r.get("日期") == date_str and r.get("商品(契約)") == "TX"
        and r.get("到期月份(週別)") == "999999" and r.get("交易人類別") == "0"):
      b5, s5 = _num(r["前五大交易人買方"]), _num(r["前五大交易人賣方"])
      b10, s10 = _num(r["前十大交易人買方"]), _num(r["前十大交易人賣方"])
      return {
          "前五大交易人留倉": int(b5 - s5),
          "前十大交易人留倉": int(b10 - s10),
          "未平倉口數": int(_num(r["全市場未沖銷部位數"])),
      }
  return None


def fetch_mtx_open_interest(date_str):
  """小型臺指期貨全市場未平倉口數（一般交易時段，各月份單式合約加總，排除價差）"""
  r = requests.post("https://www.taifex.com.tw/cht/3/futDataDown",
                    data={"down_type": "1", "commodity_id": "MTX", "commodity_id2": "",
                          "queryStartDate": date_str, "queryEndDate": date_str},
                    headers=HEADERS, timeout=30)
  r.raise_for_status()
  text = r.content.decode("big5", errors="replace")
  total, found = 0, False
  for rec in csv.reader(StringIO(text)):
    rec = [c.strip() for c in rec]
    if len(rec) < 18 or rec[0] != date_str or rec[1] != "MTX":
      continue
    if "/" in rec[2] or rec[17] != "一般":  # 排除價差合約與盤後時段
      continue
    oi = _num(rec[11])  # 未沖銷契約數
    if oi is not None:
      total += oi
      found = True
  return int(total) if found else None


def fetch_taifex_chips(date_str):
  """彙整期交所籌碼欄位；查無資料的欄位回傳空字串"""
  result = {"外資大小": "", "前五大交易人留倉": "", "前十大交易人留倉": "",
            "外(選)": "", "非菜指數": "", "未平倉口數": "", "選PCR": ""}

  inst = fetch_futures_institutional(date_str)
  if inst:
    fx = lambda name: inst.get((name, "外資及陸資"), {}).get("淨", 0)
    # 外資大小：外資臺指期淨未平倉，換算成大台口數（TX + MTX/4 + TMF/20）
    result["外資大小"] = round(fx("臺股期貨") + fx("小型臺指期貨") / 4 + fx("微型臺指期貨") / 20)

    # 非菜指數（小台散戶多空比）：散戶淨部位 ÷ 小台全市場未平倉
    # 散戶 = 全市場 − 三大法人；散戶淨部位 = 法人空單 − 法人多單
    mtx_oi = fetch_mtx_open_interest(date_str)
    if mtx_oi:
      inst_long = sum(v["多"] for (p, _), v in inst.items() if p == "小型臺指期貨")
      inst_short = sum(v["空"] for (p, _), v in inst.items() if p == "小型臺指期貨")
      result["非菜指數"] = f"{round((inst_short - inst_long) / mtx_oi * 100, 2)}%"

  lt = fetch_large_traders(date_str)
  if lt:
    result.update(lt)

  opt = fetch_options_foreign_net(date_str)
  if opt is not None:
    result["外(選)"] = opt

  pcr = fetch_pcr(date_str)
  if pcr is not None:
    result["選PCR"] = pcr

  return result
