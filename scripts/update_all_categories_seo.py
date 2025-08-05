#!/usr/bin/env python3
"""
Update All Categories SEO via Plugin
Обновление SEO всех категорий через наш плагин
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config

# Полный список SEO данных для всех категорий
ALL_CATEGORIES_SEO = {
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


def update_all_categories():
    """Обновление SEO всех категорий"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    # Получаем все категории
    categories_response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
    if categories_response.status_code != 200:
        print('❌ Не удалось получить список категорий')
        return False
    
    categories = categories_response.json()
    category_map = {cat['name']: cat['id'] for cat in categories}
    
    print(f'📂 Найдено категорий: {len(categories)}')
    
    # Подготавливаем данные для массового обновления
    bulk_data = []
    for cat_name, seo_data in ALL_CATEGORIES_SEO.items():
        if cat_name in category_map:
            bulk_data.append({
                'category_id': category_map[cat_name],
                **seo_data
            })
            print(f'   ✅ {cat_name} → ID {category_map[cat_name]}')
        else:
            print(f'   ❌ {cat_name} не найдена')
    
    if not bulk_data:
        print('❌ Нет данных для обновления')
        return False
    
    print(f'\n🚀 Обновляем {len(bulk_data)} категорий...')
    
    try:
        response = requests.post(
            'https://ailynx.ru/wp-json/yoast-category/v1/categories/bulk',
            json=bulk_data,
            auth=auth
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Массовое обновление завершено')
            print(f'   Обработано категорий: {result.get("processed")}')
            
            success_count = 0
            for item in result.get('results', []):
                if item.get('success'):
                    updated_fields = list(item.get('updated_fields', {}).keys())
                    print(f'   ✅ {item.get("category_name")}: {updated_fields}')
                    success_count += 1
                else:
                    print(f'   ❌ {item.get("category_id")}: {item.get("error")}')
            
            print(f'\n📊 Результат: {success_count}/{len(bulk_data)} категорий обновлено')
            return True
        else:
            print(f'❌ Ошибка массового обновления: {response.status_code}')
            print(f'   Ответ: {response.text[:200]}')
            return False
            
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        return False


def trigger_yoast_reindex():
    """Запуск переиндексации Yoast"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔄 Запускаем переиндексацию Yoast...')
    
    try:
        # Переиндексация терминов (категорий)
        response = requests.post('https://ailynx.ru/wp-json/yoast/v1/indexing/terms', auth=auth)
        print(f'   Термины: {response.status_code}')
        
        # Общая переиндексация
        response = requests.post('https://ailynx.ru/wp-json/yoast/v1/indexing/general', auth=auth)
        print(f'   Общая: {response.status_code}')
        
        print('✅ Переиндексация запущена')
        return True
        
    except Exception as e:
        print(f'❌ Ошибка переиндексации: {e}')
        return False


def verify_random_categories():
    """Проверка нескольких случайных категорий"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔍 Проверяем результаты обновления...')
    
    # Проверим несколько категорий
    test_categories = ["LLM", "Техника", "Люди"]
    
    # Получаем mapping категорий
    categories_response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
    if categories_response.status_code != 200:
        print('❌ Не удалось получить категории')
        return
    
    categories = categories_response.json()
    category_map = {cat['name']: cat['id'] for cat in categories}
    
    for cat_name in test_categories:
        if cat_name not in category_map:
            continue
            
        cat_id = category_map[cat_name]
        
        try:
            # Проверяем через наш плагин
            response = requests.get(f'https://ailynx.ru/wp-json/yoast-category/v1/category/{cat_id}', auth=auth)
            if response.status_code == 200:
                data = response.json()
                print(f'📂 {cat_name}:')
                print(f'   Title: {data.get("yoast_title", "Не установлен")[:60]}...')
                print(f'   Desc: {data.get("yoast_desc", "Не установлено")[:60]}...')
                print(f'   Keyword: {data.get("yoast_keyword", "Не установлено")}')
            else:
                print(f'❌ {cat_name}: Ошибка {response.status_code}')
                
        except Exception as e:
            print(f'❌ {cat_name}: {e}')


def main():
    print('🎯 Массовое обновление SEO категорий')
    print('=' * 50)
    
    # Обновляем все категории
    if update_all_categories():
        # Запускаем переиндексацию
        trigger_yoast_reindex()
        
        # Проверяем результат
        verify_random_categories()
        
        print('\n✅ Все категории обновлены!')
        print('\n💡 Теперь можно проверить в админке:')
        print('   https://ailynx.ru/wp-admin/edit-tags.php?taxonomy=category')
        
    else:
        print('\n❌ Произошла ошибка при обновлении')


if __name__ == "__main__":
    main()