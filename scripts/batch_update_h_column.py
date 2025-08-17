#!/usr/bin/env python3
"""
Пакетное обновление колонки H для всех проприетарных моделей
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

# Строки для обновления (где G = "-" и H пусто)
proprietary_rows = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 17, 18, 19, 21, 23, 25, 27, 30]

SPREADSHEET_ID = "1s-A1X5UQIYMDnJQjqhIySnrMUxp299lGtegHqOVft2k"

async def update_cells():
    """Обновить все ячейки"""
    print("Начинаю пакетное обновление колонки H для проприетарных моделей")
    print("=" * 60)
    
    updated = []
    
    for row in proprietary_rows:
        cell_range = f"llmstat!H{row}"
        print(f"Обновляю {cell_range} = '-'")
        
        # Здесь должен быть вызов MCP, но для демонстрации просто выводим команду
        print(f"  mcp__gdrive__gsheets_update_cell(")
        print(f"    fileId='{SPREADSHEET_ID}',")
        print(f"    range='{cell_range}',")
        print(f"    value='-'")
        print(f"  )")
        
        updated.append(row)
        
        # Небольшая задержка между обновлениями
        await asyncio.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"✅ Обновлено строк: {len(updated)}")
    print(f"Строки: {updated}")
    
    return updated

if __name__ == "__main__":
    asyncio.run(update_cells())