#!/usr/bin/env python3
"""Быстрое обновление ссылок через API"""

# Оставшиеся обновления
UPDATES = [
    (126, "https://ailynx.ru/tag/qwen2-5-7b-instruct/"),
    (127, "https://ailynx.ru/tag/grok-1-5/"),
    (128, "https://ailynx.ru/tag/gpt-4/"),
    (129, "https://ailynx.ru/tag/mistral-small-3-24b-base/"),
    (130, "https://ailynx.ru/tag/deepseek-r1-distill-qwen-1-5b/"),
    (131, "https://ailynx.ru/tag/claude-3-haiku/"),
    (132, "https://ailynx.ru/tag/llama-3-2-11b-instruct/"),
    (133, "https://ailynx.ru/tag/llama-3-2-3b-instruct/"),
    (134, "https://ailynx.ru/tag/jamba-1-5-mini/"),
    (135, "https://ailynx.ru/tag/gemma-3-4b/"),
    (136, "https://ailynx.ru/tag/gpt-3-5-turbo/"),
    (137, "https://ailynx.ru/tag/qwen2-5-omni-7b/"),
    (138, "https://ailynx.ru/tag/llama-3-1-8b-instruct/"),
    (139, "https://ailynx.ru/tag/phi-3-5-mini-instruct/"),
    (140, "https://ailynx.ru/tag/gemini-1-0-pro/"),
]

# Выводим для копирования
for row, link in UPDATES:
    print(f"Строка {row}: {link}")