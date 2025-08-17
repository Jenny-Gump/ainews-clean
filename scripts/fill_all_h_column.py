#!/usr/bin/env python3
"""
Скрипт для заполнения колонки H (Active Parameters) для всех моделей в таблице llmstat
Правило: для обычных моделей active = total, для MoE моделей active < total
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

SPREADSHEET_ID = "1s-A1X5UQIYMDnJQjqhIySnrMUxp299lGtegHqOVft2k"

# Известные MoE модели (где active < total)
MOE_MODELS = {
    'Qwen3-235B-A22B-Instruct-2507': '22',  # 235B total, 22B active
    'Qwen3 30B A3B': '3',  # 30.5B total, 3B active (A3B означает Active 3B)
    'DeepSeek-V3': '37',  # 671B total, 37B active (известная MoE архитектура)
    'DeepSeek-V3 0324': '37',  # 671B total, 37B active
}

async def process_all_rows():
    """
    Обработать все строки с 31 по 179
    """
    print("Начинаю обработку строк 31-179 в таблице llmstat")
    print("=" * 60)
    
    # Для примера покажу команды для строк 31-60
    # В реальности нужно сначала прочитать данные и обработать их
    
    updates_needed = []
    
    # Пример данных из строк 31-60 (на основе того что мы видели)
    rows_data = [
        (31, 'GPT-4o', '-', 'Proprietary'),  # Проприетарная -> H = '-'
        (32, 'Llama 4 Maverick', '400', 'Open'),  # Open dense -> H = 400
        (33, 'GPT-4.5', '-', 'Proprietary'),  # Проприетарная -> H = '-'
        (34, 'Phi 4 Reasoning Plus', '14', 'Open'),  # Open dense -> H = 14
        (35, 'DeepSeek-V3 0324', '671', 'Open'),  # MoE модель -> H = 37
        (36, 'Magistral Small 2506', '24', 'Open'),  # Open dense -> H = 24
        (37, 'Claude 3.5 Sonnet', '-', 'Proprietary'),  # Проприетарная -> H = '-'
        (38, 'Llama-3.3 Nemotron Super 49B v1', '49.9', 'Open'),  # Open dense -> H = 49.9
        (39, 'GPT-4.1', '-', 'Proprietary'),  # Проприетарная -> H = '-'
        (40, 'Phi 4 Reasoning', '14', 'Open'),  # Open dense -> H = 14
        (41, 'Qwen3 30B A3B', '30.5', 'Open'),  # MoE модель (A3B) -> H = 3
        (42, 'DeepSeek R1 Distill Llama 70B', '70.6', 'Open'),  # Open dense -> H = 70.6
        (43, 'QwQ-32B', '32.5', 'Open'),  # Open dense -> H = 32.5
        (44, 'GPT-4.1 mini', '-', 'Proprietary'),  # Проприетарная -> H = '-'
        (45, 'Gemini 2.5 Flash-Lite', '-', 'Open'),  # Open но без параметров -> H = '-'
        (46, 'DeepSeek R1 Distill Qwen 32B', '32.8', 'Open'),  # Open dense -> H = 32.8
        (47, 'Gemini 2.0 Flash', '-', 'Proprietary'),  # Проприетарная -> H = '-'
        (48, 'o1-mini', '-', 'Proprietary'),  # Проприетарная -> H = '-'
        (49, 'Claude 3.5 Sonnet', '-', 'Proprietary'),  # Проприетарная -> H = '-'
        (50, 'DeepSeek R1 Distill Qwen 14B', '14.8', 'Open'),  # Open dense -> H = 14.8
        (51, 'DeepSeek-V3', '671', 'Open'),  # MoE модель -> H = 37
        (52, 'Gemini 1.5 Pro', '-', 'Proprietary'),  # Проприетарная -> H = '-'
        (53, 'Llama 4 Scout', '109', 'Open'),  # Open dense -> H = 109
        (54, 'Phi 4', '14.7', 'Open'),  # Open dense -> H = 14.7
        (55, 'Grok-2', '-', 'Proprietary'),  # Проприетарная -> H = '-'
        (56, 'Llama 3.1 Nemotron Nano 8B V1', '8', 'Open'),  # Open dense -> H = 8
        (57, 'GPT-4o', '-', 'Proprietary'),  # Проприетарная -> H = '-'
        (58, 'Phi 4 Mini Reasoning', '3.8', 'Open'),  # Open dense -> H = 3.8
        (59, 'Gemini 2.0 Flash-Lite', '-', 'Proprietary'),  # Проприетарная -> H = '-'
    ]
    
    for row_num, model_name, total_params, license_type in rows_data:
        # Определяем значение для H
        if total_params == '-' or not total_params:
            h_value = '-'
        elif model_name in MOE_MODELS:
            h_value = MOE_MODELS[model_name]
        elif license_type == 'Proprietary':
            h_value = '-'
        else:
            # Dense модель - active = total
            h_value = total_params
        
        updates_needed.append({
            'row': row_num,
            'model': model_name,
            'value': h_value
        })
        
        print(f"Строка {row_num}: {model_name[:30]:30} -> H = {h_value}")
    
    print("\n" + "=" * 60)
    print(f"Всего строк для обновления: {len(updates_needed)}")
    
    # Генерируем команды для обновления
    print("\nКоманды для обновления:")
    print("-" * 60)
    
    for update in updates_needed[:10]:  # Показываем первые 10
        print(f"mcp__gdrive__gsheets_update_cell(")
        print(f"  fileId='{SPREADSHEET_ID}',")
        print(f"  range='llmstat!H{update['row']}',")
        print(f"  value='{update['value']}'")
        print(f")")
        print()
    
    if len(updates_needed) > 10:
        print(f"... и еще {len(updates_needed) - 10} строк")
    
    return updates_needed

if __name__ == "__main__":
    asyncio.run(process_all_rows())