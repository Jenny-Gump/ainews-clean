#!/usr/bin/env python3
"""
Create WordPress Tags for AI News
Создание тегов для AI новостей с описаниями
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

logger = get_logger('create_tags')

# Теги по категориям
TAGS = {
    "LLM и нейросети": [
        {
            "name": "ChatGPT",
            "slug": "chatgpt",
            "description": "ChatGPT - революционный чат-бот от OpenAI на базе GPT-3.5 и GPT-4. Лидер в области диалоговых AI-систем, способный писать код, создавать контент и решать сложные задачи."
        },
        {
            "name": "Claude",
            "slug": "claude",
            "description": "Claude - передовой AI-ассистент от Anthropic. Известен своей безопасностью, точностью и способностью к глубокому анализу. Конкурент ChatGPT с упором на этичность."
        },
        {
            "name": "Gemini",
            "slug": "gemini",
            "description": "Gemini - мультимодальная AI-модель от Google DeepMind. Обрабатывает текст, изображения, аудио и видео. Прямой конкурент GPT-4 с впечатляющими возможностями."
        },
        {
            "name": "GPT-4",
            "slug": "gpt4",
            "description": "GPT-4 - флагманская модель OpenAI. Мультимодальная система с расширенными возможностями понимания и генерации. Основа для ChatGPT Plus и API."
        },
        {
            "name": "LLaMA",
            "slug": "llama",
            "description": "LLaMA - открытая языковая модель от Meta. Доступна для исследований и коммерческого использования. Основа для многих опенсорс проектов."
        },
        {
            "name": "Mistral",
            "slug": "mistral",
            "description": "Mistral - европейская AI-модель от Mistral AI. Компактная, но мощная. Лидер среди открытых моделей по соотношению качество/размер."
        },
        {
            "name": "DeepSeek",
            "slug": "deepseek",
            "description": "DeepSeek - китайская AI-модель с фокусом на рассуждения и кодирование. Конкурирует с западными аналогами, предлагая доступные API."
        },
        {
            "name": "Grok",
            "slug": "grok",
            "description": "Grok - AI от xAI (компания Илона Маска). Известен остроумием и доступом к реальному времени через X (Twitter). Альтернативный взгляд на AI."
        },
        {
            "name": "Stable Diffusion",
            "slug": "stable-diffusion",
            "description": "Stable Diffusion - открытая модель генерации изображений. Революция в AI-арте. Работает локально, без ограничений."
        },
        {
            "name": "DALL-E",
            "slug": "dalle",
            "description": "DALL-E - генератор изображений от OpenAI. Версии 2 и 3 установили стандарты качества в AI-арте. Интегрирован в ChatGPT."
        },
        {
            "name": "Midjourney",
            "slug": "midjourney",
            "description": "Midjourney - лидер в художественной генерации изображений. Известен уникальным стилем и качеством. Работает через Discord."
        },
        {
            "name": "Copilot",
            "slug": "copilot",
            "description": "GitHub Copilot - AI-помощник программиста от Microsoft и OpenAI. Автодополнение кода на базе GPT. Меняет процесс разработки."
        },
        {
            "name": "Bard",
            "slug": "bard",
            "description": "Bard - предшественник Gemini от Google. Чат-бот с доступом к поиску Google. Эволюционировал в Gemini."
        },
        {
            "name": "Perplexity",
            "slug": "perplexity",
            "description": "Perplexity - AI-поисковик нового поколения. Комбинирует LLM с веб-поиском. Предоставляет ответы с источниками."
        },
        {
            "name": "Sora",
            "slug": "sora",
            "description": "Sora - революционный генератор видео от OpenAI. Создает реалистичные видео из текстовых описаний. Будущее контента."
        }
    ],
    
    "Компании": [
        {
            "name": "OpenAI",
            "slug": "openai",
            "description": "OpenAI - лидер AI-революции. Создатели ChatGPT, GPT-4, DALL-E и Sora. От некоммерческой организации до $100B компании."
        },
        {
            "name": "Google",
            "slug": "google",
            "description": "Google - технологический гигант с мощным AI-подразделением. DeepMind, Gemini, Bard. Пионер в машинном обучении и поиске."
        },
        {
            "name": "Microsoft",
            "slug": "microsoft",
            "description": "Microsoft - крупнейший инвестор OpenAI. Интегрирует AI во все продукты: Office, Windows, Azure. Лидер корпоративного AI."
        },
        {
            "name": "Meta",
            "slug": "meta",
            "description": "Meta (Facebook) - чемпион открытого AI. LLaMA, SAM, Make-A-Video. Инвестирует миллиарды в AI и метавселенную."
        },
        {
            "name": "Anthropic",
            "slug": "anthropic",
            "description": "Anthropic - создатели Claude. Основана выходцами из OpenAI. Фокус на безопасном и полезном AI. Привлекли $7B инвестиций."
        },
        {
            "name": "NVIDIA",
            "slug": "nvidia",
            "description": "NVIDIA - производитель GPU для AI. Их чипы питают революцию машинного обучения. Капитализация превысила $3 триллиона."
        },
        {
            "name": "Apple",
            "slug": "apple",
            "description": "Apple - фокус на приватном AI на устройстве. Apple Intelligence, обновленная Siri. Интеграция AI в экосистему."
        },
        {
            "name": "Amazon",
            "slug": "amazon",
            "description": "Amazon - AWS лидирует в облачном AI. Bedrock, Q, инвестиции в Anthropic. AI для e-commerce и логистики."
        },
        {
            "name": "Tesla",
            "slug": "tesla",
            "description": "Tesla - автопилот и роботы. Dojo суперкомпьютер для обучения AI. Optimus робот. Нейросети для автономного вождения."
        },
        {
            "name": "xAI",
            "slug": "xai",
            "description": "xAI - компания Илона Маска. Создатели Grok. Миссия: понять истинную природу вселенной через AI."
        },
        {
            "name": "DeepMind",
            "slug": "deepmind",
            "description": "DeepMind - подразделение Google. AlphaGo, AlphaFold, Gemini. Прорывы в науке благодаря AI. Нобелевская премия 2024."
        },
        {
            "name": "Stability AI",
            "slug": "stability-ai",
            "description": "Stability AI - чемпионы открытого AI. Stable Diffusion, Stable Audio. Демократизация генеративного AI."
        },
        {
            "name": "Hugging Face",
            "slug": "hugging-face",
            "description": "Hugging Face - GitHub для AI моделей. Крупнейшая платформа для ML сообщества. Хостинг моделей и датасетов."
        },
        {
            "name": "Mistral AI",
            "slug": "mistral-ai",
            "description": "Mistral AI - европейский ответ OpenAI. Основана выходцами из DeepMind и Meta. Эффективные открытые модели."
        },
        {
            "name": "Cohere",
            "slug": "cohere",
            "description": "Cohere - корпоративный AI из Канады. Специализация на NLP для бизнеса. Модели Command и Embed."
        }
    ],
    
    "Люди": [
        {
            "name": "Сэм Альтман",
            "slug": "sam-altman",
            "description": "Сэм Альтман - CEO OpenAI, отец ChatGPT. Визионер AI-революции. От стартап-инкубатора Y Combinator до лидерства в AI."
        },
        {
            "name": "Илон Маск",
            "slug": "elon-musk",
            "description": "Илон Маск - сооснователь OpenAI, основатель xAI. Tesla, Neuralink. Предупреждает о рисках AI, создавая альтернативы."
        },
        {
            "name": "Демис Хассабис",
            "slug": "demis-hassabis",
            "description": "Демис Хассабис - CEO DeepMind, создатель AlphaGo и AlphaFold. Нобелевский лауреат 2024. Гений AI и нейронауки."
        },
        {
            "name": "Джеффри Хинтон",
            "slug": "geoffrey-hinton",
            "description": "Джеффри Хинтон - крестный отец AI. Пионер глубокого обучения. Нобелевская премия 2024. Предупреждает о рисках AGI."
        },
        {
            "name": "Янн ЛеКун",
            "slug": "yann-lecun",
            "description": "Янн ЛеКун - главный AI-ученый Meta. Пионер сверточных нейросетей. Премия Тьюринга. Скептик AGI-хайпа."
        },
        {
            "name": "Эндрю Ын",
            "slug": "andrew-ng",
            "description": "Эндрю Ын - основатель Coursera, Google Brain. Демократизатор AI-образования. Преподаватель миллионов."
        },
        {
            "name": "Дарио Амодей",
            "slug": "dario-amodei",
            "description": "Дарио Амодей - CEO Anthropic, создатель Claude. Бывший VP Research OpenAI. Лидер в области AI безопасности."
        },
        {
            "name": "Марк Цукерберг",
            "slug": "mark-zuckerberg",
            "description": "Марк Цукерберг - CEO Meta. Поворот к открытому AI с LLaMA. Инвестирует десятки миллиардов в AI и метавселенную."
        },
        {
            "name": "Сатья Наделла",
            "slug": "satya-nadella",
            "description": "Сатья Наделла - CEO Microsoft. Архитектор партнерства с OpenAI. Трансформирует Microsoft через AI."
        },
        {
            "name": "Дженсен Хуанг",
            "slug": "jensen-huang",
            "description": "Дженсен Хуанг - CEO NVIDIA. Визионер GPU-революции для AI. Сделал NVIDIA самой дорогой tech-компанией."
        },
        {
            "name": "Андрей Карпатый",
            "slug": "andrej-karpathy",
            "description": "Андрей Карпатый - бывший директор AI Tesla и OpenAI. Популяризатор AI. Создатель образовательного контента."
        },
        {
            "name": "Йошуа Бенджио",
            "slug": "yoshua-bengio",
            "description": "Йошуа Бенджио - пионер глубокого обучения. Премия Тьюринга. Основатель Mila. Адвокат этичного AI."
        },
        {
            "name": "Фей-Фей Ли",
            "slug": "fei-fei-li",
            "description": "Фей-Фей Ли - создатель ImageNet. Профессор Stanford. Пионер компьютерного зрения. Адвокат человеко-центричного AI."
        },
        {
            "name": "Мустафа Сулейман",
            "slug": "mustafa-suleyman",
            "description": "Мустафа Сулейман - сооснователь DeepMind, CEO Microsoft AI. От Google к Microsoft. Автор 'The Coming Wave'."
        },
        {
            "name": "Эмад Мостак",
            "slug": "emad-mostaque",
            "description": "Эмад Мостак - основатель Stability AI. Демократизатор AI через Stable Diffusion. Адвокат открытых моделей."
        }
    ]
}


def create_tags():
    """Создание тегов в WordPress"""
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
    for category, tags in TAGS.items():
        print(f"\n📌 Создаем теги категории: {category}")
        print("-" * 50)
        
        for tag_info in tags:
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
    print("\n🚀 Создание тегов для AI News")
    print("=" * 50)
    
    total_tags = sum(len(tags) for tags in TAGS.values())
    print(f"Всего тегов для создания: {total_tags}")
    print(f"Категории: {', '.join(TAGS.keys())}")
    
    if create_tags():
        print("\n✅ Теги успешно созданы!")
        print("\nТеперь система будет автоматически назначать теги при публикации.")
    else:
        print("\n❌ Произошла ошибка при создании тегов")


if __name__ == "__main__":
    main()