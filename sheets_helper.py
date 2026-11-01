# Google Sheets 寫入輔助
import gspread
from google.oauth2.service_account import Credentials
import json
import os

def get_sheet():
    """取得 Google Sheet 工作表"""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")

    if not creds_json or not spreadsheet_id:
        raise ValueError("缺少 GOOGLE_CREDENTIALS 或 SPREADSHEET_ID 環境變數")

    info = json.loads(creds_json)
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(spreadsheet_id)
    return sh.sheet1


def ensure_headers(sheet):
    """確保第一列有正確表頭"""
    headers = [
        "日期", "成交量", "外資", "投信", "自營",
        "外資大小", "前五大交易人留倉", "前十大交易人留倉",
        "選PCR", "外(選)", "韭菜指數", "未平倉口數"
    ]
    existing = sheet.row_values(1)
    if existing != headers:
        sheet.clear()
        sheet.append_row(headers)
        print("已設定表頭")


def append_or_update(sheet, row_data: dict):
    """新增或更新一列資料"""
    headers = [
        "日期", "成交量", "外資", "投信", "自營",
        "外資大小", "前五大交易人留倉", "前十大交易人留倉",
        "選PCR", "外(選)", "韭菜指數", "未平倉口數"
    ]
    values = [row_data.get(h, "") for h in headers]

    # 取得現有日期
    all_dates = sheet.col_values(1)[1:]  # 跳過表頭

    if row_data["日期"] in all_dates:
        idx = all_dates.index(row_data["日期"]) + 2  # 第1列是表頭
        sheet.update(f"A{idx}", [values])
        print(f"已更新 {row_data['日期']}")
    else:
        sheet.append_row(values)
        print(f"已新增 {row_data['日期']}")
