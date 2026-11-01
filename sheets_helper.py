# Google Sheets 寫入輔助
def ensure_headers(sheet):
  headers = [
      "日期",
      "成交量(億)",
      "外資(億)",
      "投信(億)",
      "自營(億)",
      "外資大小",
      "前五大交易人留倉",
      "前十大交易人留倉",
      "選PCR",
      "外(選)",
      "非菜指數",
      "未平倉口數",
  ]
  current = sheet.row_values(1)
  if not current:
    sheet.append_row(headers)
  else:
    # 檢查並更新表頭
    sheet.update(range_name="A1:L1", values=[headers])
