#!/usr/bin/env python3
"""Финальное обновление строк 141-182"""

# Оставшиеся обновления (141-182)
FINAL_UPDATES = [
    # 141-160
    (141, "https://ailynx.ru/tag/qwen2-7b-instruct/"),
    (142, "https://ailynx.ru/tag/phi-4-mini/"),
    (143, "https://ailynx.ru/tag/gemma-3n-e2b-instructed/"),
    (144, "https://ailynx.ru/tag/gemma-3n-e2b-instructed-litert-preview/"),
    (145, "https://ailynx.ru/tag/gemma-3n-e4b-instructed/"),
    (146, "https://ailynx.ru/tag/gemma-3n-e4b-instructed-litert-preview/"),
    (147, "https://ailynx.ru/tag/gemma-3-1b/"),
    (148, "https://ailynx.ru/tag/codestral-22b/"),
    (149, "https://ailynx.ru/tag/command-r-plus/"),
    (150, "https://ailynx.ru/tag/deepseek-v2-5/"),
    (151, "https://ailynx.ru/tag/deepseek-vl2/"),
    (152, "https://ailynx.ru/tag/deepseek-vl2-small/"),
    (153, "https://ailynx.ru/tag/deepseek-vl2-tiny/"),
    (154, "https://ailynx.ru/tag/devstral-medium/"),
    (155, "https://ailynx.ru/tag/devstral-small-1-1/"),
    (156, "https://ailynx.ru/tag/gemma-2-27b/"),
    (157, "https://ailynx.ru/tag/gemma-2-9b/"),
    (158, "https://ailynx.ru/tag/gemma-3n-e2b/"),
    (159, "https://ailynx.ru/tag/gemma-3n-e4b/"),
    (160, "https://ailynx.ru/tag/granite-3-3-8b-base/"),
    
    # 161-182
    (161, "https://ailynx.ru/tag/granite-3-3-8b-instruct/"),
    (162, "https://ailynx.ru/tag/ibm-granite-4-0-tiny-preview/"),
    (163, "https://ailynx.ru/tag/grok-1-5v/"),
    (164, "https://ailynx.ru/tag/kimi-k1-5/"),
    (165, "https://ailynx.ru/tag/llama-3-1-nemotron-70b-instruct/"),
    (166, "https://ailynx.ru/tag/medgemma-4b-it/"),
    (167, "https://ailynx.ru/tag/ministral-8b-instruct/"),
    (168, "https://ailynx.ru/tag/mistral-large-2/"),
    (169, "https://ailynx.ru/tag/mistral-nemo-instruct/"),
    (170, "https://ailynx.ru/tag/mistral-small/"),
    (171, "https://ailynx.ru/tag/o3-pro/"),
    (172, "https://ailynx.ru/tag/phi-3-5-vision-instruct/"),
    (173, "https://ailynx.ru/tag/phi-4-multimodal-instruct/"),
    (174, "https://ailynx.ru/tag/pixtral-12b/"),
    (175, "https://ailynx.ru/tag/pixtral-large/"),
    (176, "https://ailynx.ru/tag/qvq-72b-preview/"),
    (177, "https://ailynx.ru/tag/qwen2-5-coder-32b-instruct/"),
    (178, "https://ailynx.ru/tag/qwen2-5-coder-7b-instruct/"),
    (179, "https://ailynx.ru/tag/qwen2-vl-72b-instruct/"),
    (180, "https://ailynx.ru/tag/qwen2-5-vl-72b-instruct/"),
    (181, "https://ailynx.ru/tag/qwen2-5-vl-7b-instruct/"),
    (182, "https://ailynx.ru/tag/qwen3-32b/"),
]

print(f"Всего строк для обновления: {len(FINAL_UPDATES)}")
for row, link in FINAL_UPDATES:
    print(f"{row}: {link}")