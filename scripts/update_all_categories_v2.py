#!/usr/bin/env python3
"""
Update All Categories via V2 Plugin
Обновление всех категорий через плагин V2 с принудительной индексацией
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
import time

# Полный список SEO данных
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


def update_categories_v2():
    """Обновление всех категорий через V2 API"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🚀 Обновление категорий через плагин V2')
    print('=' * 50)
    
    # Получаем все категории
    categories_response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
    if categories_response.status_code != 200:
        print('❌ Не удалось получить список категорий')
        return False
    
    categories = categories_response.json()
    category_map = {cat['name']: cat['id'] for cat in categories}
    
    print(f'📂 Найдено категорий: {len(categories)}')
    
    # Обновляем каждую категорию по отдельности через V2
    success_count = 0
    
    for cat_name, seo_data in ALL_CATEGORIES_SEO.items():
        if cat_name not in category_map:
            print(f'❌ {cat_name} не найдена')
            continue
            
        cat_id = category_map[cat_name]
        print(f'\n🔄 Обновляем {cat_name} (ID: {cat_id})...')
        
        try:
            # Обновляем через V2 API
            response = requests.post(
                f'https://ailynx.ru/wp-json/yoast-category/v2/category/{cat_id}',
                json=seo_data,
                auth=auth
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f'✅ {cat_name}: {result.get("message")}')
                print(f'   Yoast: {result.get("yoast_updated")}')
                success_count += 1
                
                # Небольшая пауза между запросами
                time.sleep(0.5)
            else:
                print(f'❌ {cat_name}: Ошибка {response.status_code}')
                print(f'   Ответ: {response.text[:200]}')
                
        except Exception as e:
            print(f'❌ {cat_name}: Исключение - {e}')
    
    print(f'\n📊 Результат: {success_count}/{len(ALL_CATEGORIES_SEO)} категорий обновлено')
    return success_count > 0


def clear_all_caches():
    """Очистка всех кэшей"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🧹 Очищаем все кэши...')
    
    # Очищаем кэш через V2 плагин
    cache_response = requests.post('https://ailynx.ru/wp-json/yoast-category/v2/clear-cache', auth=auth)
    print(f'   V2 кэш: {cache_response.status_code}')
    
    # Запускаем все доступные очистки Yoast
    yoast_endpoints = [
        '/yoast/v1/indexing/prepare',
        '/yoast/v1/indexing/terms', 
        '/yoast/v1/indexing/complete'
    ]
    
    for endpoint in yoast_endpoints:
        try:
            response = requests.post(f'https://ailynx.ru/wp-json{endpoint}', auth=auth)
            print(f'   {endpoint.split("/")[-1]}: {response.status_code}')
            time.sleep(0.5)
        except Exception as e:
            print(f'   {endpoint}: Ошибка - {e}')


def verify_results():
    """Проверка результатов"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔍 Проверяем результаты...')
    
    # Проверяем несколько категорий
    test_categories = ['Машинное обучение', 'LLM', 'Техника']
    categories_response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
    
    if categories_response.status_code != 200:
        print('❌ Не удалось получить категории для проверки')
        return
    
    categories = categories_response.json()
    category_map = {cat['name']: cat['id'] for cat in categories}
    
    found_changes = 0
    
    for cat_name in test_categories:
        if cat_name not in category_map:
            continue
            
        cat_id = category_map[cat_name]
        
        # Проверяем через V2 плагин
        v2_response = requests.get(f'https://ailynx.ru/wp-json/yoast-category/v2/category/{cat_id}', auth=auth)
        if v2_response.status_code == 200:
            v2_data = v2_response.json()
            print(f'\n📂 {cat_name}:')
            print(f'   V2 Title: {v2_data.get("yoast_title", "Не установлен")[:60]}...')
            print(f'   Indexable: {v2_data.get("yoast_indexable")}')
        
        # Проверяем через WordPress API 
        wp_response = requests.get(f'{config.wordpress_api_url}/categories/{cat_id}', auth=auth)
        if wp_response.status_code == 200:
            wp_data = wp_response.json()
            yoast_head = wp_data.get('yoast_head', '')
            yoast_title = wp_data.get('yoast_head_json', {}).get('title', '')
            
            # Ищем наши данные
            if 'AI Lynx' in yoast_head or 'ML новости' in yoast_head:
                print(f'   ✅ Yoast обновился!')
                found_changes += 1
            else:
                print(f'   ❌ Yoast показывает: {yoast_title}')
    
    if found_changes > 0:
        print(f'\n🎉 Найдено {found_changes} успешных обновлений!')
    else:
        print(f'\n⏳ Изменения пока не отображаются в Yoast head')
        print('💡 Возможно, нужно время для обновления или ручная настройка в админке')


def main():
    print('🎯 Массовое обновление через V2 плагин')
    print('=' * 50)
    
    if update_categories_v2():
        clear_all_caches()
        
        print('\n⏳ Ждем обновления Yoast (5 секунд)...')
        time.sleep(5)
        
        verify_results()
        
        print('\n✅ Обновление через V2 завершено!')
        print('\n💡 Если изменения не видны:')
        print('1. Проверьте админку: https://ailynx.ru/wp-admin/edit-tags.php?taxonomy=category')
        print('2. Может потребоваться время для обновления Yoast кэша')
        print('3. Попробуйте вручную сохранить одну категорию в админке')
        
    else:
        print('\n❌ Произошла ошибка при обновлении')


if __name__ == "__main__":
    main()