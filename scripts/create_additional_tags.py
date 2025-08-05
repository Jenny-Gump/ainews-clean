#!/usr/bin/env python3
"""
Create Additional WordPress Tags for AI News
Создание дополнительных тегов по запросу пользователя
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
from app_logging import get_logger
import time

logger = get_logger('create_additional_tags')

# Дополнительные теги
ADDITIONAL_TAGS = [
    {
        "name": "Runway",
        "slug": "runway",
        "description": "Runway - революционная платформа для AI-видео. Gen-2 и Gen-3 модели для генерации видео из текста. Инструменты для креаторов и режиссеров."
    },
    {
        "name": "Notion AI",
        "slug": "notion-ai",
        "description": "Notion AI - интеграция искусственного интеллекта в популярную систему управления знаниями. Автоматизация написания, суммаризация, анализ данных."
    },
    {
        "name": "ElevenLabs",
        "slug": "elevenlabs",
        "description": "ElevenLabs - лидер в синтезе голоса с помощью AI. Реалистичное клонирование голоса, многоязычная озвучка, аудиокниги нового поколения."
    },
    {
        "name": "Scale AI",
        "slug": "scale-ai",
        "description": "Scale AI - инфраструктура для обучения AI. Разметка данных, RLHF, оценка моделей. Поставщик данных для OpenAI, Meta и других гигантов."
    },
    {
        "name": "Qwen",
        "slug": "qwen",
        "description": "Qwen - серия моделей от Alibaba Cloud. Мультимодальные возможности, поддержка длинного контекста. Конкурент GPT из Китая."
    },
    {
        "name": "Alibaba Cloud",
        "slug": "alibaba-cloud",
        "description": "Alibaba Cloud - китайский облачный гигант с мощным AI-портфолио. Qwen модели, Tongyi серия, облачная инфраструктура для AI."
    },
    {
        "name": "Manus",
        "slug": "manus",
        "description": "Manus - технологии захвата движения для VR/AR и AI. Перчатки и костюмы для анимации. Мост между физическим и цифровым мирами."
    },
    {
        "name": "Gemini Pro",
        "slug": "gemini-pro",
        "description": "Gemini Pro - продвинутая версия Gemini от Google. Расширенный контекст, улучшенное рассуждение. Доступна через API и Vertex AI."
    },
    {
        "name": "Grok-2",
        "slug": "grok-2",
        "description": "Grok-2 - улучшенная версия AI от xAI. Интеграция с X (Twitter), реальное время, улучшенные способности к рассуждению."
    },
    {
        "name": "Kimi",
        "slug": "kimi",
        "description": "Kimi - китайский AI-ассистент от Moonshot AI. Поддержка супер-длинного контекста (до 2M токенов). Популярен в Китае."
    },
    {
        "name": "Flux",
        "slug": "flux",
        "description": "Flux - новое поколение моделей генерации изображений от Black Forest Labs. Создана командой из Stability AI. Открытая альтернатива Midjourney."
    },
    {
        "name": "Veo",
        "slug": "veo",
        "description": "Veo - генератор видео от Google DeepMind. Создает высококачественные видео из текста. Конкурент Sora от OpenAI."
    },
    {
        "name": "Minimax",
        "slug": "minimax",
        "description": "MiniMax - китайская AI-компания. Создатели чат-бота Talkie и моделей abab. Фокус на диалоговом AI и развлечениях."
    },
    {
        "name": "Krea AI",
        "slug": "krea-ai",
        "description": "Krea AI - платформа для генерации и редактирования изображений в реальном времени. Инновационный подход к AI-креативности."
    },
    {
        "name": "Black Forest Labs",
        "slug": "black-forest-labs",
        "description": "Black Forest Labs - создатели Flux. Основана бывшими сотрудниками Stability AI. Новое слово в open-source генерации изображений."
    },
    {
        "name": "Moonshot AI",
        "slug": "moonshot-ai",
        "description": "Moonshot AI - создатели Kimi Chat. Специализация на длинном контексте и понимании документов. Китайский единорог."
    },
    {
        "name": "Pika Labs",
        "slug": "pika-labs",
        "description": "Pika Labs - AI для генерации и редактирования видео. Простой интерфейс, впечатляющие результаты. Конкурент Runway."
    },
    {
        "name": "Midjourney v6",
        "slug": "midjourney-v6",
        "description": "Midjourney v6 - последняя версия с улучшенным пониманием промптов, реалистичностью и контролем над генерацией."
    },
    {
        "name": "GPT-4o",
        "slug": "gpt-4o",
        "description": "GPT-4o (Omni) - мультимодальная версия GPT-4 с нативной поддержкой голоса, изображений и текста. Быстрее и дешевле GPT-4."
    },
    {
        "name": "Suno AI",
        "slug": "suno-ai",
        "description": "Suno AI - генерация музыки из текста. Создает полные песни с вокалом. Революция в музыкальной индустрии."
    }
]


def create_additional_tags():
    """Создание дополнительных тегов в WordPress"""
    config = Config()
    
    if not all([config.wordpress_api_url, config.wordpress_username, config.wordpress_app_password]):
        logger.error("WordPress API не настроен")
        return False
    
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    base_url = f"{config.wordpress_api_url}/tags"
    
    # Получаем существующие теги
    try:
        response = requests.get(base_url, auth=auth, params={'per_page': 100})
        if response.status_code != 200:
            logger.error(f"Не удалось получить теги: {response.status_code}")
            return False
        
        existing = {tag['name']: tag['id'] for tag in response.json()}
        logger.info(f"Найдено существующих тегов: {len(existing)}")
        
    except Exception as e:
        logger.error(f"Ошибка при получении тегов: {e}")
        return False
    
    # Создаем теги
    created_count = 0
    print("\n📌 Создаем дополнительные теги")
    print("-" * 50)
    
    for tag_info in ADDITIONAL_TAGS:
        if tag_info['name'] in existing:
            logger.info(f"✅ {tag_info['name']} - уже существует (ID: {existing[tag_info['name']]})")
            continue
        
        # Создаем тег
        data = {
            'name': tag_info['name'],
            'slug': tag_info['slug'],
            'description': tag_info['description']
        }
        
        try:
            response = requests.post(base_url, json=data, auth=auth)
            
            if response.status_code == 201:
                new_tag = response.json()
                logger.info(f"✅ {tag_info['name']} - создан (ID: {new_tag['id']})")
                created_count += 1
                time.sleep(0.5)  # Небольшая задержка между запросами
            else:
                logger.error(f"❌ {tag_info['name']} - ошибка создания: {response.status_code}")
                logger.error(f"   Ответ: {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"❌ {tag_info['name']} - ошибка: {e}")
    
    print(f"\n✅ Создано новых тегов: {created_count}")
    return True


def main():
    """Главная функция"""
    print("\n🚀 Создание дополнительных тегов для AI News")
    print("=" * 50)
    
    print(f"Всего тегов для создания: {len(ADDITIONAL_TAGS)}")
    
    if create_additional_tags():
        print("\n✅ Дополнительные теги успешно созданы!")
        
        # Также создаем недостающий тег Джеффри Хинтон
        print("\n📌 Создаем недостающий тег")
        try:
            config = Config()
            auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
            
            data = {
                'name': 'Джеффри Хинтон',
                'slug': 'geoffrey-hinton',
                'description': 'Джеффри Хинтон - крестный отец AI. Пионер глубокого обучения. Нобелевская премия 2024. Предупреждает о рисках AGI.'
            }
            
            response = requests.post(f'{config.wordpress_api_url}/tags', json=data, auth=auth)
            
            if response.status_code == 201:
                print('✅ Тег "Джеффри Хинтон" создан успешно!')
            elif response.status_code == 400:
                print('ℹ️  Тег "Джеффри Хинтон" уже существует')
            else:
                print(f'❌ Ошибка создания тега "Джеффри Хинтон": {response.status_code}')
        except Exception as e:
            print(f'❌ Ошибка: {e}')
            
    else:
        print("\n❌ Произошла ошибка при создании тегов")


if __name__ == "__main__":
    main()