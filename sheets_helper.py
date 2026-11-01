# Google Sheets 寫入輔助
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet():
    """連線並取得 Google 試算表物件"""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    # 支援本地或 GitHub Actions 環境變數/檔案
    creds_file = 'credentials.json'
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    
    # 開啟您的 Google 試算表（請確認名稱正確）
    sheet = client.open("台股每日籌碼自動化").sheet1
    return sheet

def ensure_headers(sheet):
    """確保第一列有正確的表頭與單位"""
    headers = [
        "日期", "成交量(億)", "外資(億)", "投信(億)", "自營(億)", 
        "外資大小", "前五大交易人留倉", "前十大交易人留倉", 
        "選PCR", "外(選)", "非菜指數", "未平倉口數"
    ]
    current = sheet.row_values(1)
    if not current:
        sheet.append_row(headers)
    else:
        sheet.update(range_name="A1:L1", values=[headers])

def append_or_update(sheet, row_data):
    """將資料新增至試算表（若該日期已存在則更新，否則附加在最下方）"""
    # row_data 是一個包含 12 個欄位值的串列 (List)
    date_val = row_data[0]
    all_records = sheet.get_all_values()
    
    # 檢查該日期是否已經存在於試算表中（假設日期在第 1 欄，index 為 0）
    row_index = None
    for idx, row in enumerate(all_records[1:], start=2): # 從第二列開始找
        if row and row[0] == date_val:
            row_index = idx
            break
            
    if row_index:
        # 如果已經存在，更新該行
        sheet.update(range_name=f"A{row_index}:L{row_index}", values=[row_data])
        print(f"更新已有日期的資料: {date_val}")
    else:
        # 如果不存在，附加到最下方
        sheet.append_row(row_data)
        print(f"新增今日資料: {date_val}")
