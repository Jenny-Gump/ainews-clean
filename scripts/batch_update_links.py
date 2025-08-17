#!/usr/bin/env python3
"""Пакетное обновление ссылок в Google Sheets"""

import time

# Данные для обновления (строка: ссылка)
UPDATES = {
    # 121-140
    121: "https://ailynx.ru/tag/nova-micro/",
    122: "https://ailynx.ru/tag/gemini-1-5-flash-8b/",
    123: "https://ailynx.ru/tag/mistral-small-3-1-24b-base/",
    124: "https://ailynx.ru/tag/jamba-1-5-large/",
    125: "https://ailynx.ru/tag/phi-3-5-moe-instruct/",
    126: "https://ailynx.ru/tag/qwen2-5-7b-instruct/",
    127: "https://ailynx.ru/tag/grok-1-5/",
    128: "https://ailynx.ru/tag/gpt-4/",
    129: "https://ailynx.ru/tag/mistral-small-3-24b-base/",
    130: "https://ailynx.ru/tag/deepseek-r1-distill-qwen-1-5b/",
    131: "https://ailynx.ru/tag/claude-3-haiku/",
    132: "https://ailynx.ru/tag/llama-3-2-11b-instruct/",
    133: "https://ailynx.ru/tag/llama-3-2-3b-instruct/",
    134: "https://ailynx.ru/tag/jamba-1-5-mini/",
    135: "https://ailynx.ru/tag/gemma-3-4b/",
    136: "https://ailynx.ru/tag/gpt-3-5-turbo/",
    137: "https://ailynx.ru/tag/qwen2-5-omni-7b/",
    138: "https://ailynx.ru/tag/llama-3-1-8b-instruct/",
    139: "https://ailynx.ru/tag/phi-3-5-mini-instruct/",
    140: "https://ailynx.ru/tag/gemini-1-0-pro/",
    
    # 141-160
    141: "https://ailynx.ru/tag/qwen2-7b-instruct/",
    142: "https://ailynx.ru/tag/phi-4-mini/",
    143: "https://ailynx.ru/tag/gemma-3n-e2b-instructed/",
    144: "https://ailynx.ru/tag/gemma-3n-e2b-instructed-litert-preview/",
    145: "https://ailynx.ru/tag/gemma-3n-e4b-instructed/",
    146: "https://ailynx.ru/tag/gemma-3n-e4b-instructed-litert-preview/",
    147: "https://ailynx.ru/tag/gemma-3-1b/",
    148: "https://ailynx.ru/tag/codestral-22b/",
    149: "https://ailynx.ru/tag/command-r-plus/",
    150: "https://ailynx.ru/tag/deepseek-v2-5/",
    151: "https://ailynx.ru/tag/deepseek-vl2/",
    152: "https://ailynx.ru/tag/deepseek-vl2-small/",
    153: "https://ailynx.ru/tag/deepseek-vl2-tiny/",
    154: "https://ailynx.ru/tag/devstral-medium/",
    155: "https://ailynx.ru/tag/devstral-small-1-1/",
    156: "https://ailynx.ru/tag/gemma-2-27b/",
    157: "https://ailynx.ru/tag/gemma-2-9b/",
    158: "https://ailynx.ru/tag/gemma-3n-e2b/",
    159: "https://ailynx.ru/tag/gemma-3n-e4b/",
    160: "https://ailynx.ru/tag/granite-3-3-8b-base/",
    
    # 161-182
    161: "https://ailynx.ru/tag/granite-3-3-8b-instruct/",
    162: "https://ailynx.ru/tag/ibm-granite-4-0-tiny-preview/",
    163: "https://ailynx.ru/tag/grok-1-5v/",
    164: "https://ailynx.ru/tag/kimi-k1-5/",
    165: "https://ailynx.ru/tag/llama-3-1-nemotron-70b-instruct/",
    166: "https://ailynx.ru/tag/medgemma-4b-it/",
    167: "https://ailynx.ru/tag/ministral-8b-instruct/",
    168: "https://ailynx.ru/tag/mistral-large-2/",
    169: "https://ailynx.ru/tag/mistral-nemo-instruct/",
    170: "https://ailynx.ru/tag/mistral-small/",
    171: "https://ailynx.ru/tag/o3-pro/",
    172: "https://ailynx.ru/tag/phi-3-5-vision-instruct/",
    173: "https://ailynx.ru/tag/phi-4-multimodal-instruct/",
    174: "https://ailynx.ru/tag/pixtral-12b/",
    175: "https://ailynx.ru/tag/pixtral-large/",
    176: "https://ailynx.ru/tag/qvq-72b-preview/",
    177: "https://ailynx.ru/tag/qwen2-5-coder-32b-instruct/",
    178: "https://ailynx.ru/tag/qwen2-5-coder-7b-instruct/",
    179: "https://ailynx.ru/tag/qwen2-vl-72b-instruct/",
    180: "https://ailynx.ru/tag/qwen2-5-vl-72b-instruct/",
    181: "https://ailynx.ru/tag/qwen2-5-vl-7b-instruct/",
    182: "https://ailynx.ru/tag/qwen3-32b/",
}

# Выводим команды для обновления через MCP
for row, link in UPDATES.items():
    print(f'mcp__gdrive__gsheets_update_cell(fileId="1s-A1X5UQIYMDnJQjqhIySnrMUxp299lGtegHqOVft2k", range="llmstat!D{row}", value="{link}")')
    time.sleep(0.1)

print(f"\nВсего строк для обновления: {len(UPDATES)}")