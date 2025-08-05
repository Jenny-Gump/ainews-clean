#!/usr/bin/env python3
"""
Update Category SEO Fields via WordPress API
Обновление SEO полей категорий через WordPress API
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
from app_logging import get_logger

logger = get_logger('update_category_seo')

# SEO данные для категорий
CATEGORY_SEO = {
    "LLM": {
        "yoast_title": "Новости LLM - Большие языковые модели | AI Lynx",
        "yoast_desc": "Последние новости о больших языковых моделях: GPT, Claude, Gemini, LLaMA. Обзоры, сравнения и анализ развития LLM технологий.",
        "yoast_keyword": "LLM новости"
    },
    "Машинное обучение": {
        "yoast_title": "Машинное обучение - ML новости и исследования | AI Lynx",
        "yoast_desc": "Актуальные новости машинного обучения: алгоритмы, нейросети, исследования. Прорывы в области ML и практические применения.",
        "yoast_keyword": "машинное обучение"
    },
    "Техника": {
        "yoast_title": "AI Техника - Железо и софт для ИИ | AI Lynx",
        "yoast_desc": "Новости о технике для ИИ: GPU, TPU, чипы, облачные платформы. Обзоры железа и программного обеспечения для машинного обучения.",
        "yoast_keyword": "AI техника"
    },
    "Digital": {
        "yoast_title": "Digital AI - Цифровая трансформация с ИИ | AI Lynx",
        "yoast_desc": "Как ИИ меняет цифровой мир: интернет, соцсети, e-commerce, маркетинг. Инновации в digital-сфере с использованием AI.",
        "yoast_keyword": "digital AI"
    },
    "Люди": {
        "yoast_title": "Люди в AI - Лидеры и визионеры ИИ | AI Lynx",
        "yoast_desc": "Истории людей, создающих будущее ИИ: интервью с исследователями, предпринимателями, визионерами индустрии искусственного интеллекта.",
        "yoast_keyword": "лидеры AI"
    },
    "Финансы": {
        "yoast_title": "AI в Финансах - ИИ в банкинге и инвестициях | AI Lynx",
        "yoast_desc": "Применение ИИ в финансах: алгоритмическая торговля, кредитные риски, инвестиции в AI-стартапы, финтех с машинным обучением.",
        "yoast_keyword": "AI финансы"
    },
    "Наука": {
        "yoast_title": "AI в Науке - Научные прорывы с ИИ | AI Lynx", 
        "yoast_desc": "Как ИИ революционизирует науку: от предсказания белков до поиска лекарств. Машинное обучение в физике, химии, биологии.",
        "yoast_keyword": "AI наука"
    },
    "Обучение": {
        "yoast_title": "AI Образование - Курсы и обучение ИИ | AI Lynx",
        "yoast_desc": "Образование в сфере ИИ: курсы, программы, сертификации по машинному обучению. Roadmap и карьера в artificial intelligence.",
        "yoast_keyword": "обучение AI"
    },
    "Другие индустрии": {
        "yoast_title": "AI в Индустриях - Применение ИИ в разных сферах | AI Lynx",
        "yoast_desc": "ИИ в различных отраслях: сельское хозяйство, космос, медицина, производство. Инновационные кейсы применения AI.",
        "yoast_keyword": "AI индустрии"
    },
    "Новости": {
        "yoast_title": "AI Новости - Последние события в мире ИИ | AI Lynx",
        "yoast_desc": "Свежие новости искусственного интеллекта: прорывы, исследования, релизы. Будьте в курсе развития AI технологий.",
        "yoast_keyword": "AI новости"
    }
}


def update_categories_seo():
    """Обновление SEO полей категорий"""
    config = Config()
    
    if not all([config.wordpress_api_url, config.wordpress_username, config.wordpress_app_password]):
        logger.error("WordPress API не настроен")
        return False
    
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    # Получаем все категории
    try:
        response = requests.get(f"{config.wordpress_api_url}/categories", auth=auth, params={'per_page': 100})
        if response.status_code != 200:
            logger.error(f"Не удалось получить категории: {response.status_code}")
            return False
        
        categories = response.json()
        category_map = {cat['name']: cat['id'] for cat in categories}
        
        logger.info(f"Найдено категорий: {len(categories)}")
        
    except Exception as e:
        logger.error(f"Ошибка при получении категорий: {e}")
        return False
    
    # Обновляем SEO для каждой категории
    updated_count = 0
    for cat_name, seo_data in CATEGORY_SEO.items():
        if cat_name not in category_map:
            logger.warning(f"Категория '{cat_name}' не найдена")
            continue
        
        category_id = category_map[cat_name]
        
        # Данные для обновления
        update_data = {
            'meta': {
                '_yoast_wpseo_title': seo_data['yoast_title'],
                '_yoast_wpseo_metadesc': seo_data['yoast_desc'],
                '_yoast_wpseo_focuskw': seo_data['yoast_keyword']
            }
        }
        
        try:
            # Обновляем категорию
            response = requests.post(
                f"{config.wordpress_api_url}/categories/{category_id}",
                json=update_data,
                auth=auth
            )
            
            if response.status_code == 200:
                logger.info(f"✅ {cat_name} - SEO поля обновлены")
                updated_count += 1
            else:
                logger.error(f"❌ {cat_name} - ошибка обновления: {response.status_code}")
                logger.error(f"   Ответ: {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"❌ {cat_name} - ошибка: {e}")
    
    print(f"\n✅ Обновлено категорий: {updated_count}")
    return True


def update_specific_category(category_name: str, title: str, description: str, keyword: str):
    """Обновление конкретной категории"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    # Найти категорию
    response = requests.get(f"{config.wordpress_api_url}/categories", auth=auth, params={'search': category_name})
    if response.status_code != 200:
        print(f"❌ Ошибка поиска категории: {response.status_code}")
        return False
    
    categories = response.json()
    category = None
    for cat in categories:
        if cat['name'] == category_name:
            category = cat
            break
    
    if not category:
        print(f"❌ Категория '{category_name}' не найдена")
        return False
    
    # Обновить SEO поля
    update_data = {
        'meta': {
            '_yoast_wpseo_title': title,
            '_yoast_wpseo_metadesc': description,
            '_yoast_wpseo_focuskw': keyword
        }
    }
    
    response = requests.post(
        f"{config.wordpress_api_url}/categories/{category['id']}",
        json=update_data,
        auth=auth
    )
    
    if response.status_code == 200:
        print(f"✅ Категория '{category_name}' обновлена")
        return True
    else:
        print(f"❌ Ошибка обновления: {response.status_code}")
        print(f"   Ответ: {response.text[:200]}")
        return False


def main():
    """Главная функция"""
    print("\n🔧 Обновление SEO полей категорий")
    print("=" * 50)
    
    print("Выберите действие:")
    print("1. Обновить все категории")
    print("2. Обновить конкретную категорию")
    
    choice = input("\nВведите номер (1 или 2): ").strip()
    
    if choice == "1":
        if update_categories_seo():
            print("\n✅ SEO поля всех категорий успешно обновлены!")
        else:
            print("\n❌ Произошла ошибка при обновлении")
    
    elif choice == "2":
        category_name = input("Введите название категории: ").strip()
        title = input("SEO заголовок: ").strip()
        description = input("Мета-описание: ").strip()
        keyword = input("Ключевое слово: ").strip()
        
        if update_specific_category(category_name, title, description, keyword):
            print(f"\n✅ Категория '{category_name}' обновлена!")
        else:
            print(f"\n❌ Ошибка обновления категории '{category_name}'")
    
    else:
        print("❌ Неверный выбор")


if __name__ == "__main__":
    main()