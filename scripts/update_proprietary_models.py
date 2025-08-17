#!/usr/bin/env python3
"""
Обновление колонки H для проприетарных моделей
"""

# Список строк где G = "-" и нужно установить H = "-"
proprietary_rows = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 17, 18, 19, 21, 23, 25, 27, 30]

print("Обновление колонки H для проприетарных моделей:")
print("=" * 50)

for row in proprietary_rows:
    print(f"mcp__gdrive__gsheets_update_cell:")
    print(f"  fileId: 1s-A1X5UQIYMDnJQjqhIySnrMUxp299lGtegHqOVft2k")
    print(f"  range: llmstat!H{row}")
    print(f"  value: -")
    print()

print(f"Всего строк для обновления: {len(proprietary_rows)}")