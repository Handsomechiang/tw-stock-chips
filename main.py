import sys
import time
from datetime import datetime, timedelta

from fetchers.taifex import fetch_pcr, fetch_top_traders_and_oi
from fetchers.twse import fetch_institutional, fetch_market_volume
from sheets_helper import append_or_update, ensure_headers, get_sheet

# 每次執行回補最近幾天（已存在的日期會更新，不會重複新增）
LOOKBACK_DAYS = 10


def get_trading_dates(start_date: str, end_date: str = None):
  start = datetime.strptime(start_date, "%Y-%m-%d")
  end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()
  dates = []
  current = start
  while current <= end:
    if current.weekday() < 5:  # 排除週末
      dates.append(current.strftime("%Y-%m-%d"))
    current += timedelta(days=1)
  return dates


def process_date(date_str: str):
  yyyymmdd = date_str.replace("-", "")
  slash_date = date_str.replace("-", "/")
  print(f"\n處理 {date_str} ...")

  inst = fetch_institutional(yyyymmdd)
  volume = fetch_market_volume(yyyymmdd)

  # 抓取 PCR
  pcr_df = fetch_pcr(start_date=slash_date, end_date=slash_date)
  pcr_value = ""
  if pcr_df is not None and not pcr_df.empty:
    try:
      pcr_value = round(float(pcr_df.iloc[0, 6]), 1)
    except Exception:
      pcr_value = ""

  # 抓取期權籌碼（前十大、未平倉等）
  taifex_data = fetch_top_traders_and_oi(slash_date)

  # 非菜指數（範例公式：可依您的定義調整）
  foreign_size = taifex_data.get("外資大小", 0)
  total_oi = taifex_data.get("未平倉口數", 0)
  cabbage_index = ""
  if total_oi > 0:
    cabbage_index = f"{round((total_oi - abs(foreign_size)) / total_oi * 100, 2)}%"

  return {
      "日期": date_str,
      "成交量(億)": volume if volume else "",
      "外資(億)": inst.get("外資", "") if inst else "",
      "投信(億)": inst.get("投信", "") if inst else "",
      "自營(億)": inst.get("自營", "") if inst else "",
      "外資大小": taifex_data.get("外資大小", ""),
      "前五大交易人留倉": taifex_data.get("前五大交易人留倉", ""),
      "前十大交易人留倉": taifex_data.get("前十大交易人留倉", ""),
      "選PCR": pcr_value,
      "外(選)": taifex_data.get("外(選)", ""),
      "非菜指數": cabbage_index,
      "未平倉口數": total_oi,
  }


def main():
  print("開始執行台股籌碼更新...")
  sheet = get_sheet()
  ensure_headers(sheet)

  start_date = (datetime.now() - timedelta(days=LOOKBACK_DAYS)).strftime("%Y-%m-%d")
  dates = get_trading_dates(start_date)

  written, errors = 0, 0
  for d in dates:
    try:
      row = process_date(d)
      if row["外資(億)"] != "" or row["成交量(億)"] != "":
        append_or_update(sheet, row)
        written += 1
      else:
        print(f"{d} 無交易資料（假日或尚未公布），略過")
      time.sleep(1.5)
    except Exception as e:
      errors += 1
      print(f"處理 {d} 發生錯誤: {e}")

  print(f"\n完成：寫入 {written} 天，錯誤 {errors} 天")
  # 全部失敗時讓 GitHub Actions 顯示紅色，才知道要處理
  if written == 0 and errors > 0:
    sys.exit(1)


if __name__ == "__main__":
  main()
