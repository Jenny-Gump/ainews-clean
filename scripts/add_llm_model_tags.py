#!/usr/bin/env python3
"""Скрипт для добавления тегов LLM моделей на WordPress"""

import requests
import json
import time

# WordPress API настройки
WP_URL = "https://ailynx.ru/wp-json/wp/v2"
WP_USER = "admin"
WP_PASS = "tE85 PFT4 Ghq9 nl26 nQlt gBnG"

# Модели из таблицы llmstat с описаниями
LLM_MODELS = {
    # xAI models
    "Grok-4 Heavy": "Самая мощная модель xAI для сложных задач рассуждения",
    "Grok-4": "Продвинутая языковая модель от xAI с улучшенными способностями",
    "Grok-3": "Третье поколение модели Grok от xAI",
    "Grok-3 Mini": "Облегченная версия Grok-3 для быстрых ответов",
    "Grok-2": "Второе поколение модели Grok с мультимодальными возможностями",
    "Grok-2 mini": "Компактная версия Grok-2 для эффективной обработки",
    
    # Google models
    "Gemini 2.5 Pro Preview 06-05": "Предварительная версия Gemini 2.5 Pro от Google",
    "Gemini 2.5 Pro": "Профессиональная версия Gemini 2.5 с расширенными возможностями",
    "Gemini 2.5 Flash": "Быстрая версия Gemini 2.5 для low-latency задач",
    "Gemini 2.5 Flash-Lite": "Ультралегкая версия Gemini 2.5 Flash",
    "Gemini 2.0 Flash Thinking": "Версия Gemini 2.0 с chain-of-thought рассуждениями",
    "Gemini 2.0 Flash": "Быстрая модель Gemini второго поколения",
    "Gemini 2.0 Flash-Lite": "Облегченная версия Gemini 2.0 Flash",
    "Gemini 1.5 Pro": "Профессиональная модель Gemini 1.5 с контекстом до 2M токенов",
    "Gemini 1.5 Flash": "Быстрая версия Gemini 1.5 для производственных задач",
    
    # OpenAI models
    "GPT-5": "Следующее поколение языковой модели от OpenAI",
    "GPT-5 mini": "Компактная версия GPT-5 для эффективных вычислений",
    "GPT-5 nano": "Минимальная версия GPT-5 для edge-устройств",
    "o3": "Модель рассуждения третьего поколения от OpenAI",
    "o3-mini": "Облегченная версия o3 для быстрых рассуждений",
    "o4-mini": "Предварительная версия четвертого поколения модели рассуждения",
    "o1-pro": "Профессиональная версия модели o1 с улучшенными способностями",
    "o1": "Первая модель OpenAI с chain-of-thought рассуждениями",
    "o1-preview": "Предварительная версия модели o1",
    "o1-mini": "Компактная версия модели o1 для быстрых задач",
    "GPT OSS 120B": "Open-source версия GPT модели с 120B параметров",
    "GPT OSS 20B": "Open-source версия GPT модели с 20B параметров",
    "GPT-4.5": "Промежуточная версия между GPT-4 и GPT-5",
    "GPT-4.1": "Улучшенная версия GPT-4 с оптимизациями",
    "GPT-4.1 mini": "Компактная версия GPT-4.1",
    "GPT-4.1 nano": "Минимальная версия GPT-4.1 для мобильных устройств",
    
    # Anthropic models
    "Claude 3.7 Sonnet": "Улучшенная версия Claude Sonnet с расширенными возможностями",
    "Claude Opus 4.1": "Последняя версия Claude Opus с улучшенной производительностью",
    "Claude Opus 4": "Четвертое поколение Claude Opus для сложных задач",
    "Claude Sonnet 4": "Четвертое поколение Claude Sonnet",
    "Claude 3.5 Sonnet": "Версия Claude 3.5 с балансом скорости и качества",
    "Claude 3 Opus": "Самая мощная модель Claude третьего поколения",
    
    # DeepSeek models
    "DeepSeek-R1-0528": "Последняя версия модели рассуждения DeepSeek",
    "DeepSeek-R1": "Первая модель рассуждения от DeepSeek",
    "DeepSeek R1 Zero": "Базовая версия DeepSeek R1 без fine-tuning",
    "DeepSeek R1 Distill Llama 70B": "Дистилляция DeepSeek R1 в Llama 70B",
    "DeepSeek R1 Distill Qwen 32B": "Дистилляция DeepSeek R1 в Qwen 32B",
    "DeepSeek R1 Distill Qwen 14B": "Дистилляция DeepSeek R1 в Qwen 14B",
    "DeepSeek R1 Distill Qwen 7B": "Дистилляция DeepSeek R1 в Qwen 7B",
    "DeepSeek R1 Distill Llama 8B": "Дистилляция DeepSeek R1 в Llama 8B",
    "DeepSeek-V3 0324": "Версия DeepSeek V3 от марта 2024",
    "DeepSeek-V3": "Третье поколение основной модели DeepSeek",
    
    # Alibaba models
    "Qwen3-235B-A22B-Instruct-2507": "Самая большая модель Qwen3 с активными 22B параметрами",
    "Qwen3 30B A3B": "Модель Qwen3 с 30B параметров и 3B активных",
    "QwQ-32B": "Модель рассуждения QwQ с 32B параметров",
    "QwQ-32B-Preview": "Предварительная версия QwQ-32B",
    "Qwen2.5 32B Instruct": "Инструктированная версия Qwen2.5 с 32B параметров",
    
    # NVIDIA models
    "Llama 3.1 Nemotron Ultra 253B v1": "Самая мощная версия Llama от NVIDIA",
    "Llama-3.3 Nemotron Super 49B v1": "Оптимизированная версия Llama 3.3 от NVIDIA",
    "Llama 3.1 Nemotron Nano 8B V1": "Компактная версия Llama 3.1 от NVIDIA",
    
    # Meta models
    "Llama 4 Maverick": "Экспериментальная версия Llama 4",
    "Llama 4 Scout": "Разведывательная версия Llama 4 для тестирования",
    "Llama 3.3 70B Instruct": "Инструктированная версия Llama 3.3 с 70B параметров",
    "Llama 3.1 405B Instruct": "Самая большая открытая модель Llama 3.1",
    
    # Microsoft models
    "Phi 4 Reasoning Plus": "Расширенная версия Phi 4 для сложных рассуждений",
    "Phi 4 Reasoning": "Версия Phi 4 оптимизированная для рассуждений",
    "Phi 4 Mini Reasoning": "Компактная версия Phi 4 Reasoning",
    "Phi 4": "Четвертое поколение компактной модели от Microsoft",
    
    # Moonshot AI models
    "Kimi K2 Instruct": "Инструктированная версия Kimi K2 от Moonshot AI",
    
    # Magistral models
    "Magistral Medium": "Средняя по размеру модель Magistral",
    "Magistral Small 2506": "Компактная версия Magistral от июня 2025"
}

def get_existing_tags():
    """Получить список существующих тегов"""
    existing = set()
    page = 1
    while True:
        response = requests.get(
            f"{WP_URL}/tags",
            params={"per_page": 100, "page": page},
            auth=(WP_USER, WP_PASS)
        )
        if response.status_code != 200:
            break
        tags = response.json()
        if not tags:
            break
        for tag in tags:
            existing.add(tag['name'])
        page += 1
    return existing

def create_tag(name, description):
    """Создать тег на WordPress"""
    url = f"{WP_URL}/tags"
    slug = name.lower().replace(" ", "-").replace(".", "-").replace("+", "plus")
    
    data = {
        "name": name,
        "description": description,
        "slug": slug
    }
    
    response = requests.post(
        url,
        auth=(WP_USER, WP_PASS),
        json=data
    )
    
    if response.status_code == 201:
        print(f"✅ Создан тег: {name}")
        return True
    elif response.status_code == 400:
        error = response.json()
        if "term_exists" in str(error):
            print(f"⚠️ Тег уже существует: {name}")
        else:
            print(f"❌ Ошибка создания тега {name}: {error}")
        return False
    else:
        print(f"❌ Ошибка создания тега {name}: {response.status_code}")
        return False

def main():
    """Основная функция"""
    print("🚀 Получаем существующие теги...")
    existing_tags = get_existing_tags()
    print(f"📊 Найдено существующих тегов: {len(existing_tags)}")
    
    # Фильтруем модели, которых еще нет
    models_to_add = {}
    for model, description in LLM_MODELS.items():
        if model not in existing_tags:
            models_to_add[model] = description
    
    print(f"📝 Моделей для добавления: {len(models_to_add)}")
    print("-" * 50)
    
    if not models_to_add:
        print("✅ Все модели уже добавлены!")
        return
    
    created = 0
    failed = 0
    
    for name, description in models_to_add.items():
        if create_tag(name, description):
            created += 1
        else:
            failed += 1
        time.sleep(0.5)  # Пауза между запросами
    
    print("-" * 50)
    print(f"✅ Успешно создано: {created}")
    print(f"❌ Ошибок: {failed}")
    print("🎉 Готово!")

if __name__ == "__main__":
    main()