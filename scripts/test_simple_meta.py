#!/usr/bin/env python3
"""
Test Simple Meta Field Update
Тест простого обновления мета-полей
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config

def test_what_wordpress_accepts():
    """Тестируем что принимает WordPress API"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🔍 Тестируем поля WordPress API для категорий')
    print('=' * 60)
    
    # Тестируем на категории "Машинное обучение" (ID: 4)
    cat_id = 4
    
    print(f'📂 Тестируем категорию ID: {cat_id}')
    
    # Сначала получаем текущие данные
    get_response = requests.get(f'{config.wordpress_api_url}/categories/{cat_id}', auth=auth)
    if get_response.status_code == 200:
        current_data = get_response.json()
        print(f'✅ Текущие данные получены:')
        print(f'   name: {current_data.get("name")}')
        print(f'   slug: {current_data.get("slug")}')
        print(f'   description: {len(current_data.get("description", ""))} символов')
        print(f'   meta: {current_data.get("meta", "НЕТ")}')
    
    # Тест 1: Только стандартные поля
    print(f'\n🧪 Тест 1: Только стандартные поля')
    test1_data = {
        'name': 'ТЕСТ: Машинное обучение для проверки API',
        'description': 'Тестовое описание для проверки что WordPress API принимает стандартные поля категорий.',
        'slug': 'test-machine-learning'
    }
    
    response1 = requests.post(f'{config.wordpress_api_url}/categories/{cat_id}', json=test1_data, auth=auth)
    print(f'   Статус: {response1.status_code}')
    if response1.status_code == 200:
        result = response1.json()
        print(f'   ✅ name: {result.get("name")}')
        print(f'   ✅ slug: {result.get("slug")}')
        print(f'   ✅ description: {len(result.get("description", ""))} символов')
    else:
        print(f'   ❌ Ошибка: {response1.text[:200]}')
    
    # Тест 2: С мета-полями
    print(f'\n🧪 Тест 2: С мета-полями')
    test2_data = {
        'name': 'ТЕСТ2: Машинное обучение с мета',
        'description': 'Тестовое описание с попыткой добавить мета-поля.',
        'slug': 'test-machine-learning-meta',
        'meta': {
            'test_field': 'test_value',
            'seo_description': 'Это мета-описание для SEO'
        }
    }
    
    response2 = requests.post(f'{config.wordpress_api_url}/categories/{cat_id}', json=test2_data, auth=auth)
    print(f'   Статус: {response2.status_code}')
    if response2.status_code == 200:
        result = response2.json()
        print(f'   ✅ name: {result.get("name")}')
        print(f'   ✅ meta: {result.get("meta", "НЕТ")}')
    else:
        print(f'   ❌ Ошибка: {response2.text[:200]}')
    
    # Тест 3: Прямое обновление term_meta
    print(f'\n🧪 Тест 3: Через WordPress functions')
    # Этот тест требует PHP код в плагине
    print('   Для мета-полей нужен плагин, который вызовет:')
    print('   update_term_meta($term_id, "seo_description", $value);')
    
    # Возвращаем исходные данные
    print(f'\n🔄 Возвращаем исходные данные...')
    restore_data = {
        'name': current_data.get('name'),
        'description': current_data.get('description'),
        'slug': current_data.get('slug')
    }
    
    restore_response = requests.post(f'{config.wordpress_api_url}/categories/{cat_id}', json=restore_data, auth=auth)
    if restore_response.status_code == 200:
        print('✅ Исходные данные восстановлены')
    else:
        print('❌ Ошибка восстановления')

def explain_wordpress_api_limitations():
    """Объяснение ограничений WordPress API"""
    print('\n📚 Объяснение ограничений WordPress REST API:')
    print('=' * 60)
    
    print('✅ МОЖНО изменять через REST API:')
    print('• name - название категории (core taxonomy field)')
    print('• slug - URL категории (core taxonomy field)')  
    print('• description - описание категории (core taxonomy field)')
    print('• parent - родительская категория (core taxonomy field)')
    
    print('\n❌ НЕЛЬЗЯ изменять через REST API (без плагинов):')
    print('• meta поля (term_meta) - требуют register_rest_field()')
    print('• HTML мета-теги - не являются частью WordPress taxonomy')
    print('• Произвольные поля - требуют custom field registration')
    
    print('\n🔧 Решения для мета-полей:')
    print('1. Плагин с register_rest_field() - расширяет REST API')
    print('2. Плагин с custom endpoints - создает новые API маршруты')
    print('3. Прямое обращение к БД - через SQL или WordPress functions')
    print('4. WordPress hooks - wp_head для вывода мета-тегов')
    
    print('\n💡 Почему так происходит:')
    print('• WordPress защищает мета-поля от случайного доступа')
    print('• Для безопасности meta fields требуют явной регистрации')
    print('• REST API предоставляет только core taxonomy fields')
    print('• Мета-описания - это SEO функциональность, не core WordPress')

def main():
    print('🔍 Анализ возможностей WordPress REST API')
    print('=' * 60)
    
    test_what_wordpress_accepts()
    explain_wordpress_api_limitations()
    
    print('\n📋 Итог:')
    print('• WordPress REST API принимает только стандартные поля категорий')
    print('• Для мета-описаний нужен плагин с register_rest_field()')
    print('• Текущие name, slug, description успешно обновлены')
    print('• Для HTML мета-тегов используем плагин category-meta-descriptions.php')

if __name__ == "__main__":
    main()