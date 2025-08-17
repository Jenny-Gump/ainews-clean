#!/usr/bin/env python3
"""Скрипт для добавления тегов моделей из строк 101-182"""

import requests
import time

# WordPress API настройки
WP_URL = "https://ailynx.ru/wp-json/wp/v2"
WP_USER = "admin"
WP_PASS = "tE85 PFT4 Ghq9 nl26 nQlt gBnG"

# Модели из строк 101-182 с описаниями
MODELS_101_182 = {
    # Строка 101 в таблице уже есть Qwen2.5 72B Instruct
    "Kimi K2 Base": "Базовая версия модели Kimi K2 от Moonshot AI",
    "GPT-4 Turbo": "Улучшенная версия GPT-4 с увеличенной скоростью и контекстом",
    "Qwen3 235B A22B": "Версия Qwen3 с 235B параметров и 22B активных",
    "Nova Pro": "Профессиональная языковая модель от Amazon",
    "Llama 3.2 90B Instruct": "Большая версия Llama 3.2 с 90B параметров",
    "Qwen2.5 VL 32B Instruct": "Мультимодальная версия Qwen2.5 с 32B параметров",
    "Mistral Small 3.1 24B Instruct": "Компактная версия Mistral 3.1 с инструкциями",
    "Qwen2.5 14B Instruct": "Средняя версия Qwen2.5 с 14B параметров",
    "Mistral Small 3 24B Instruct": "Третье поколение компактной Mistral с инструкциями",
    "Mistral Small 3.2 24B Instruct": "Обновленная версия Mistral Small 3.2",
    "Gemma 3 27B": "Модель Gemma третьего поколения с 27B параметров",
    "Qwen2 72B Instruct": "Большая версия Qwen2 с инструкциями",
    "Nova Lite": "Облегченная версия модели Nova от Amazon",
    "Llama 3.1 70B Instruct": "Инструктированная версия Llama 3.1 с 70B параметров",
    "Claude 3.5 Haiku": "Компактная версия Claude 3.5 для быстрых ответов",
    "Gemma 3 12B": "Средняя модель Gemma 3 с 12B параметров",
    "Claude 3 Sonnet": "Сбалансированная версия Claude 3",
    "Gemini Diffusion": "Модель Gemini для генерации изображений",
    "GPT-4o mini": "Компактная версия мультимодальной модели GPT-4o",
    "Nova Micro": "Минимальная версия модели Nova от Amazon",
    "Gemini 1.5 Flash 8B": "Быстрая версия Gemini 1.5 с 8B параметров",
    "Mistral Small 3.1 24B Base": "Базовая версия Mistral Small 3.1",
    "Jamba 1.5 Large": "Большая версия гибридной модели Jamba от AI21",
    "Phi-3.5-MoE-instruct": "Версия Phi с архитектурой Mixture of Experts",
    "Qwen2.5 7B Instruct": "Компактная версия Qwen2.5 с 7B параметров",
    "Grok-1.5": "Версия 1.5 модели Grok от xAI",
    "GPT-4": "Четвертое поколение модели GPT от OpenAI",
    "Mistral Small 3 24B Base": "Базовая версия Mistral Small 3",
    "DeepSeek R1 Distill Qwen 1.5B": "Дистилляция DeepSeek R1 в Qwen 1.5B",
    "Claude 3 Haiku": "Самая быстрая модель Claude 3",
    "Llama 3.2 11B Instruct": "Средняя версия Llama 3.2 с инструкциями",
    "Llama 3.2 3B Instruct": "Компактная версия Llama 3.2 с инструкциями",
    "Jamba 1.5 Mini": "Компактная версия гибридной модели Jamba",
    "Gemma 3 4B": "Малая модель Gemma 3 с 4B параметров",
    "GPT-3.5 Turbo": "Быстрая версия GPT-3.5 для диалогов",
    "Qwen2.5-Omni-7B": "Мультимодальная версия Qwen2.5 с 7B параметров",
    "Llama 3.1 8B Instruct": "Компактная версия Llama 3.1 с инструкциями",
    "Phi-3.5-mini-instruct": "Минимальная версия Phi 3.5 с инструкциями",
    "Gemini 1.0 Pro": "Первая профессиональная версия Gemini",
    "Qwen2 7B Instruct": "Компактная версия Qwen2 с инструкциями",
    "Phi 4 Mini": "Минимальная версия Phi 4 от Microsoft",
    "Gemma 3n E2B Instructed": "Оптимизированная версия Gemma для edge-устройств",
    "Gemma 3n E2B Instructed LiteRT (Preview)": "Предварительная версия Gemma для мобильных устройств",
    "Gemma 3n E4B Instructed": "Расширенная edge-версия Gemma",
    "Gemma 3n E4B Instructed LiteRT Preview": "Предварительная LiteRT версия Gemma E4B",
    "Gemma 3 1B": "Минимальная модель Gemma 3 с 1B параметров",
    "Codestral-22B": "Специализированная модель Mistral для кода",
    "Command R+": "Расширенная версия Command R от Cohere",
    "DeepSeek-V2.5": "Версия 2.5 основной модели DeepSeek",
    "DeepSeek VL2": "Мультимодальная модель DeepSeek второго поколения",
    "DeepSeek VL2 Small": "Компактная версия DeepSeek VL2",
    "DeepSeek VL2 Tiny": "Минимальная версия DeepSeek VL2",
    "Devstral Medium": "Средняя версия Devstral для разработки",
    "Devstral Small 1.1": "Компактная версия Devstral 1.1",
    "Gemma 2 27B": "Второе поколение Gemma с 27B параметров",
    "Gemma 2 9B": "Второе поколение Gemma с 9B параметров",
    "Gemma 3n E2B": "Базовая edge-версия Gemma 3n",
    "Gemma 3n E4B": "Расширенная edge-версия Gemma 3n",
    "Granite 3.3 8B Base": "Базовая версия Granite 3.3 от IBM",
    "Granite 3.3 8B Instruct": "Инструктированная версия Granite 3.3",
    "IBM Granite 4.0 Tiny Preview": "Предварительная минимальная версия Granite 4.0",
    "Grok-1.5V": "Мультимодальная версия Grok 1.5",
    "Kimi-k1.5": "Версия 1.5 модели Kimi от Moonshot AI",
    "Llama 3.1 Nemotron 70B Instruct": "Оптимизированная NVIDIA версия Llama 3.1",
    "MedGemma 4B IT": "Медицинская версия Gemma для IT-задач",
    "Ministral 8B Instruct": "Минимальная версия Mistral с 8B параметров",
    "Mistral Large 2": "Второе поколение большой модели Mistral",
    "Mistral NeMo Instruct": "Версия Mistral, разработанная с NVIDIA",
    "Mistral Small": "Компактная версия Mistral для производства",
    "o3-pro": "Профессиональная версия модели рассуждения o3",
    "Phi-3.5-vision-instruct": "Мультимодальная версия Phi 3.5",
    "Phi-4-multimodal-instruct": "Мультимодальная версия Phi 4",
    "Pixtral-12B": "Мультимодальная модель Mistral с 12B параметров",
    "Pixtral Large": "Большая мультимодальная модель от Mistral",
    "QvQ-72B-Preview": "Предварительная версия визуальной модели QvQ",
    "Qwen2.5-Coder 32B Instruct": "Специализированная версия Qwen для программирования",
    "Qwen2.5-Coder 7B Instruct": "Компактная версия Qwen для кода",
    "Qwen2-VL-72B-Instruct": "Мультимодальная версия Qwen2 с 72B параметров",
    "Qwen2.5 VL 72B Instruct": "Большая мультимодальная версия Qwen2.5",
    "Qwen2.5 VL 7B Instruct": "Компактная мультимодальная версия Qwen2.5",
    "Qwen3 32B": "Версия Qwen3 с 32B параметров"
}

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
        return True, response.json()['id']
    elif response.status_code == 400:
        error = response.json()
        if "term_exists" in str(error):
            print(f"⚠️ Тег уже существует: {name}")
            # Попробуем получить ID существующего тега
            search_response = requests.get(
                f"{WP_URL}/tags?search={name}",
                auth=(WP_USER, WP_PASS)
            )
            if search_response.status_code == 200:
                tags = search_response.json()
                for tag in tags:
                    if tag['name'] == name:
                        return False, tag['id']
        else:
            print(f"❌ Ошибка создания тега {name}: {error}")
        return False, None
    else:
        print(f"❌ Ошибка создания тега {name}: {response.status_code}")
        return False, None

def main():
    """Основная функция"""
    print("🚀 Начинаем добавление тегов моделей (строки 101-182)...")
    print(f"📊 Всего моделей для добавления: {len(MODELS_101_182)}")
    print("-" * 50)
    
    created = 0
    existed = 0
    failed = 0
    tag_links = {}
    
    for name, description in MODELS_101_182.items():
        success, tag_id = create_tag(name, description)
        if success:
            created += 1
            tag_links[name] = f"https://ailynx.ru/tag/{name.lower().replace(' ', '-').replace('.', '-').replace('+', 'plus')}/"
        elif tag_id:
            existed += 1
            tag_links[name] = f"https://ailynx.ru/tag/{name.lower().replace(' ', '-').replace('.', '-').replace('+', 'plus')}/"
        else:
            failed += 1
        time.sleep(0.5)  # Пауза между запросами
    
    print("-" * 50)
    print(f"✅ Успешно создано: {created}")
    print(f"⚠️ Уже существовало: {existed}")
    print(f"❌ Ошибок: {failed}")
    
    # Сохраняем ссылки для обновления таблицы
    print("\n📝 Сохраняем ссылки для обновления таблицы...")
    with open('/tmp/model_links_101_182.txt', 'w') as f:
        for model, link in tag_links.items():
            f.write(f"{model}|{link}\n")
    
    print("🎉 Готово!")

if __name__ == "__main__":
    main()