#!/usr/bin/env python3
"""Скрипт для обновления ссылок на теги в Google Sheets"""

# Словарь соответствия моделей и ссылок на теги
MODEL_LINKS = {
    # xAI models
    "Grok-4 Heavy": "https://ailynx.ru/tag/grok-4-heavy/",
    "Grok-4": "https://ailynx.ru/tag/grok-4/",
    "Grok-3": "https://ailynx.ru/tag/grok-3/",
    "Grok-3 Mini": "https://ailynx.ru/tag/grok-3-mini/",
    "Grok-2": "https://ailynx.ru/tag/grok-2/",
    "Grok-2 mini": "https://ailynx.ru/tag/grok-2-mini/",
    
    # Google models
    "Gemini 2.5 Pro Preview 06-05": "https://ailynx.ru/tag/gemini-2-5-pro-preview-06-05/",
    "Gemini 2.5 Pro": "https://ailynx.ru/tag/gemini-2-5-pro/",
    "Gemini 2.5 Flash": "https://ailynx.ru/tag/gemini-2-5-flash/",
    "Gemini 2.5 Flash-Lite": "https://ailynx.ru/tag/gemini-2-5-flash-lite/",
    "Gemini 2.0 Flash Thinking": "https://ailynx.ru/tag/gemini-2-0-flash-thinking/",
    "Gemini 2.0 Flash": "https://ailynx.ru/tag/gemini-2-0-flash/",
    "Gemini 2.0 Flash-Lite": "https://ailynx.ru/tag/gemini-2-0-flash-lite/",
    "Gemini 1.5 Pro": "https://ailynx.ru/tag/gemini-1-5-pro/",
    "Gemini 1.5 Flash": "https://ailynx.ru/tag/gemini-1-5-flash/",
    
    # OpenAI models
    "GPT-5": "https://ailynx.ru/tag/gpt-5/",
    "GPT-5 mini": "https://ailynx.ru/tag/gpt-5-mini/",
    "GPT-5 nano": "https://ailynx.ru/tag/gpt-5-nano/",
    "o3": "https://ailynx.ru/tag/o3/",
    "o3-mini": "https://ailynx.ru/tag/o3-mini/",
    "o4-mini": "https://ailynx.ru/tag/o4-mini/",
    "o1-pro": "https://ailynx.ru/tag/o1-pro/",
    "o1": "https://ailynx.ru/tag/o1/",
    "o1-preview": "https://ailynx.ru/tag/o1-preview/",
    "o1-mini": "https://ailynx.ru/tag/o1-mini/",
    "GPT OSS 120B": "https://ailynx.ru/tag/gpt-oss-120b/",
    "GPT OSS 20B": "https://ailynx.ru/tag/gpt-oss-20b/",
    "GPT-4o": "https://ailynx.ru/tag/gpt-4o/",
    "GPT-4.5": "https://ailynx.ru/tag/gpt-4-5/",
    "GPT-4.1": "https://ailynx.ru/tag/gpt-4-1/",
    "GPT-4.1 mini": "https://ailynx.ru/tag/gpt-4-1-mini/",
    "GPT-4.1 nano": "https://ailynx.ru/tag/gpt-4-1-nano/",
    
    # Anthropic models
    "Claude 3.7 Sonnet": "https://ailynx.ru/tag/claude-3-7-sonnet/",
    "Claude Opus 4.1": "https://ailynx.ru/tag/claude-opus-4-1/",
    "Claude Opus 4": "https://ailynx.ru/tag/claude-opus-4/",
    "Claude Sonnet 4": "https://ailynx.ru/tag/claude-sonnet-4/",
    "Claude 3.5 Sonnet": "https://ailynx.ru/tag/claude-3-5-sonnet/",
    "Claude 3 Opus": "https://ailynx.ru/tag/claude-3-opus/",
    
    # DeepSeek models
    "DeepSeek-R1-0528": "https://ailynx.ru/tag/deepseek-r1-0528/",
    "DeepSeek-R1": "https://ailynx.ru/tag/deepseek-r1/",
    "DeepSeek R1 Zero": "https://ailynx.ru/tag/deepseek-r1-zero/",
    "DeepSeek R1 Distill Llama 70B": "https://ailynx.ru/tag/deepseek-r1-distill-llama-70b/",
    "DeepSeek R1 Distill Qwen 32B": "https://ailynx.ru/tag/deepseek-r1-distill-qwen-32b/",
    "DeepSeek R1 Distill Qwen 14B": "https://ailynx.ru/tag/deepseek-r1-distill-qwen-14b/",
    "DeepSeek R1 Distill Qwen 7B": "https://ailynx.ru/tag/deepseek-r1-distill-qwen-7b/",
    "DeepSeek R1 Distill Llama 8B": "https://ailynx.ru/tag/deepseek-r1-distill-llama-8b/",
    "DeepSeek-V3 0324": "https://ailynx.ru/tag/deepseek-v3-0324/",
    "DeepSeek-V3": "https://ailynx.ru/tag/deepseek-v3/",
    
    # Alibaba models
    "Qwen3-235B-A22B-Instruct-2507": "https://ailynx.ru/tag/qwen3-235b-a22b-instruct-2507/",
    "Qwen3 30B A3B": "https://ailynx.ru/tag/qwen3-30b-a3b/",
    "QwQ-32B": "https://ailynx.ru/tag/qwq-32b/",
    "QwQ-32B-Preview": "https://ailynx.ru/tag/qwq-32b-preview/",
    "Qwen2.5 32B Instruct": "https://ailynx.ru/tag/qwen2-5-32b-instruct/",
    
    # NVIDIA models
    "Llama 3.1 Nemotron Ultra 253B v1": "https://ailynx.ru/tag/llama-3-1-nemotron-ultra-253b-v1/",
    "Llama-3.3 Nemotron Super 49B v1": "https://ailynx.ru/tag/llama-3-3-nemotron-super-49b-v1/",
    "Llama 3.1 Nemotron Nano 8B V1": "https://ailynx.ru/tag/llama-3-1-nemotron-nano-8b-v1/",
    
    # Meta models
    "Llama 4 Maverick": "https://ailynx.ru/tag/llama-4-maverick/",
    "Llama 4 Scout": "https://ailynx.ru/tag/llama-4-scout/",
    "Llama 3.3 70B Instruct": "https://ailynx.ru/tag/llama-3-3-70b-instruct/",
    "Llama 3.1 405B Instruct": "https://ailynx.ru/tag/llama-3-1-405b-instruct/",
    
    # Microsoft models
    "Phi 4 Reasoning Plus": "https://ailynx.ru/tag/phi-4-reasoning-plus/",
    "Phi 4 Reasoning": "https://ailynx.ru/tag/phi-4-reasoning/",
    "Phi 4 Mini Reasoning": "https://ailynx.ru/tag/phi-4-mini-reasoning/",
    "Phi 4": "https://ailynx.ru/tag/phi-4/",
    
    # Moonshot AI models
    "Kimi K2 Instruct": "https://ailynx.ru/tag/kimi-k2-instruct/",
    
    # Magistral models
    "Magistral Medium": "https://ailynx.ru/tag/magistral-medium/",
    "Magistral Small 2506": "https://ailynx.ru/tag/magistral-small-2506/"
}

# Выводим список для проверки
print("Модели и их ссылки на теги:")
print("-" * 50)
for model, link in MODEL_LINKS.items():
    print(f"{model}: {link}")
print("-" * 50)
print(f"Всего моделей с ссылками: {len(MODEL_LINKS)}")