#!/usr/bin/env python3
"""
Test Yoast Category API Plugin
Тестирование плагина для управления Yoast SEO полями категорий
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
from app_logging import get_logger

logger = get_logger('test_yoast_plugin')

# SEO данные для тестирования
CATEGORY_SEO_DATA = {
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
}


def test_plugin_availability():
    """Проверка доступности плагина"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    try:
        # Проверяем наш новый эндпоинт
        response = requests.get(
            'https://ailynx.ru/wp-json/yoast-category/v1/category/4',  # ID категории "Машинное обучение"
            auth=auth
        )
        
        print(f'🔍 Статус плагина: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print('✅ Плагин работает!')
            print(f'📂 Категория: {data.get("category_name")}')
            print(f'🏷️  Slug: {data.get("category_slug")}')
            print(f'📝 Yoast Title: {data.get("yoast_title") or "Не установлен"}')
            print(f'📄 Yoast Desc: {data.get("yoast_desc") or "Не установлено"}')
            print(f'🔑 Yoast Keyword: {data.get("yoast_keyword") or "Не установлено"}')
            return True
        elif response.status_code == 404:
            print('❌ Плагин не найден или не активен')
            print('💡 Нужно загрузить и активировать плагин в WordPress')
        else:
            print(f'❌ Ошибка: {response.status_code}')
            print(f'   Ответ: {response.text[:200]}')
        
        return False
        
    except Exception as e:
        print(f'❌ Ошибка соединения: {e}')
        return False


def update_category_seo(category_id, seo_data):
    """Обновление SEO данных категории через наш API"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    try:
        response = requests.post(
            f'https://ailynx.ru/wp-json/yoast-category/v1/category/{category_id}',
            json=seo_data,
            auth=auth
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f'✅ Обновлена категория: {result.get("category_name")}')
            print(f'   Обновленные поля: {list(result.get("updated_fields", {}).keys())}')
            return True
        else:
            print(f'❌ Ошибка обновления: {response.status_code}')
            print(f'   Ответ: {response.text[:200]}')
            return False
            
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        return False


def bulk_update_categories():
    """Массовое обновление категорий"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    # Сначала получаем ID категорий
    categories_response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
    if categories_response.status_code != 200:
        print('❌ Не удалось получить список категорий')
        return False
    
    categories = categories_response.json()
    category_map = {cat['name']: cat['id'] for cat in categories}
    
    # Подготавливаем данные для массового обновления
    bulk_data = []
    for cat_name, seo_data in CATEGORY_SEO_DATA.items():
        if cat_name in category_map:
            bulk_data.append({
                'category_id': category_map[cat_name],
                **seo_data
            })
    
    if not bulk_data:
        print('❌ Нет данных для обновления')
        return False
    
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
            
            for item in result.get('results', []):
                if item.get('success'):
                    print(f'   ✅ {item.get("category_name")}: {list(item.get("updated_fields", {}).keys())}')
                else:
                    print(f'   ❌ {item.get("category_id")}: {item.get("error")}')
            
            return True
        else:
            print(f'❌ Ошибка массового обновления: {response.status_code}')
            print(f'   Ответ: {response.text[:200]}')
            return False
            
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        return False


def verify_updates():
    """Проверка результатов обновления"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔍 Проверяем результаты обновления...')
    
    # Проверяем через WordPress API
    response = requests.get(f'{config.wordpress_api_url}/categories/4', auth=auth)  # Машинное обучение
    if response.status_code == 200:
        category = response.json()
        yoast_head = category.get('yoast_head', '')
        
        print(f'📂 Категория: {category.get("name")}')
        
        # Ищем наш заголовок в Yoast head
        if 'ML новости и исследования' in yoast_head:
            print('✅ SEO заголовок применился в Yoast head!')
        else:
            print('❌ SEO заголовок не найден в Yoast head')
            
        # Проверяем через наш API
        plugin_response = requests.get('https://ailynx.ru/wp-json/yoast-category/v1/category/4', auth=auth)
        if plugin_response.status_code == 200:
            plugin_data = plugin_response.json()
            print(f'📝 Плагин Title: {plugin_data.get("yoast_title")}')
            print(f'📄 Плагин Desc: {plugin_data.get("yoast_desc")}')
            print(f'🔑 Плагин Keyword: {plugin_data.get("yoast_keyword")}')


def main():
    print('🧪 Тестирование Yoast Category API Plugin')
    print('=' * 50)
    
    # Проверяем доступность плагина
    if not test_plugin_availability():
        print('\n💡 Инструкции по установке плагина:')
        print('1. Скопируйте файл yoast-category-api.php в папку /wp-content/plugins/')
        print('2. Активируйте плагин в админке WordPress')
        print('3. Убедитесь, что Yoast SEO активен')
        return
    
    print('\n📝 Тестируем обновление отдельной категории...')
    update_category_seo(4, CATEGORY_SEO_DATA["Машинное обучение"])
    
    print('\n📦 Тестируем массовое обновление...')
    bulk_update_categories()
    
    print('\n🔍 Проверяем результаты...')
    verify_updates()
    
    print('\n✅ Тестирование завершено!')


if __name__ == "__main__":
    main()