# Google Sheets 寫入輔助
import json
import os

import gspread

# 試算表欄位順序（第一列表頭）
HEADERS = [
    "日期", "成交量(億)", "外資(億)", "投信(億)", "自營(億)",
    "外資大小", "前五大交易人留倉", "前十大交易人留倉",
    "選PCR", "外(選)", "非菜指數", "未平倉口數",
]

SHEET_NAME = "台股每日籌碼自動化"


def get_sheet():
    """連線並取得 Google 試算表物件。

    憑證來源（依序）：
    1. 環境變數 GOOGLE_CREDENTIALS（GitHub Actions：把服務帳號 JSON 全文存成 Secret）
    2. 本機檔案 credentials.json（在自己電腦上執行時）
    """
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    if creds_json:
        client = gspread.service_account_from_dict(json.loads(creds_json))
    elif os.path.exists("credentials.json"):
        client = gspread.service_account(filename="credentials.json")
    else:
        raise RuntimeError("找不到 Google 憑證：請設定 GOOGLE_CREDENTIALS Secret 或放置 credentials.json")

    # 有設定 SPREADSHEET_ID 就用 ID 開啟（較可靠），否則用名稱
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if spreadsheet_id:
        return client.open_by_key(spreadsheet_id).sheet1
    return client.open(SHEET_NAME).sheet1


def ensure_headers(sheet):
    """確保第一列有正確的表頭"""
    current = sheet.row_values(1)
    if current != HEADERS:
        sheet.update(range_name="A1:L1", values=[HEADERS])


def append_or_update(sheet, row):
    """新增或更新一列資料。row 為 dict（鍵名同 HEADERS）或已排好順序的 list。"""
    row_data = [row.get(h, "") for h in HEADERS] if isinstance(row, dict) else list(row)
    date_val = row_data[0]
    dates = sheet.col_values(1)  # 只讀日期欄，比讀整張表快

    if date_val in dates[1:]:
        row_index = dates.index(date_val, 1) + 1
        sheet.update(range_name=f"A{row_index}:L{row_index}", values=[row_data])
        print(f"更新已有日期的資料: {date_val}")
    else:
        sheet.append_row(row_data, value_input_option="USER_ENTERED")
        print(f"新增資料: {date_val}")
