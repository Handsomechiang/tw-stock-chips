import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time

from fetchers.twse import fetch_institutional, fetch_market_volume
from fetchers.taifex import fetch_pcr
from sheets_helper import get_sheet, ensure_headers, append_or_update


def get_trading_dates(start_date: str, end_date: str = None):
    """產生日期區間（簡單版，之後可再優化排除假日）"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.now()

    dates = []
    current = start
    while current <= end:
        # 簡單排除週末
        if current.weekday() < 5:
            dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


def process_date(date_str: str):
    """處理單一日期"""
    yyyymmdd = date_str.replace("-", "")
    print(f"\n處理 {date_str} ...")

    inst = fetch_institutional(yyyymmdd)
    volume = fetch_market_volume(yyyymmdd)

    # PCR 一次抓一段期間比較有效率，這裡先簡化
    pcr_df = fetch_pcr(
        start_date=date_str.replace("-", "/"),
        end_date=date_str.replace("-", "/")
    )

    pcr_value = ""
    if pcr_df is not None and not pcr_df.empty:
        # 取未平倉比率
        try:
            pcr_value = round(float(pcr_df.iloc[0, 6]), 1)  # 買賣權未平倉量比率%
        except:
            pcr_value = ""

    row = {
        "日期": date_str,
        "成交量": volume if volume else "",
        "外資": inst.get("外資", "") if inst else "",
        "投信": inst.get("投信", "") if inst else "",
        "自營": inst.get("自營", "") if inst else "",
        "外資大小": "",          # 之後補
        "前五大交易人留倉": "",  # 之後補
        "前十大交易人留倉": "",  # 之後補
        "選PCR": pcr_value,
        "外(選)": "",
        "韭菜指數": "",
        "未平倉口數": ""
    }
    return row


def main():
    print("開始執行台股籌碼更新...")

    sheet = get_sheet()
    ensure_headers(sheet)

    # 從 2026-10-07 開始補到今天
    start_date = "2026-10-07"
    dates = get_trading_dates(start_date)

    for d in dates:
        try:
            row = process_date(d)
            if row["外資"] != "" or row["成交量"] != "":
                append_or_update(sheet, row)
            time.sleep(1.5)  # 避免請求太快
        except Exception as e:
            print(f"處理 {d} 發生錯誤: {e}")

    print("\n全部完成！")


if __name__ == "__main__":
    main()
