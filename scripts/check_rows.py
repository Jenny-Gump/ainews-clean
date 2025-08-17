#!/usr/bin/env python3
"""Проверка строк таблицы"""

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Путь к файлу с ключами
KEY_FILE = '/Users/skynet/Desktop/AI DEV/ainews-clean/ai-news-parser-439008-6e13c4d5f906.json'

# ID таблицы
SPREADSHEET_ID = '1s-A1X5UQIYMDnJQjqhIySnrMUxp299lGtegHqOVft2k'

# Авторизация
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
credentials = service_account.Credentials.from_service_account_file(KEY_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

# Читаем строки 110-125
result = service.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID,
    range='llmstat!A110:D125'
).execute()

values = result.get('values', [])
print(f"Получено строк: {len(values)}\n")

for i, row in enumerate(values):
    row_num = 110 + i
    if len(row) >= 3:
        company = row[0] if len(row) > 0 else ''
        link = row[1] if len(row) > 1 else ''
        model = row[2] if len(row) > 2 else ''
        model_link = row[3] if len(row) > 3 else ''
        print(f"Строка {row_num}:")
        print(f"  Компания: {company}")
        print(f"  Модель: {model}")
        print(f"  Ссылка на модель: {model_link}")
        print()