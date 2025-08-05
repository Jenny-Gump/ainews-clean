#!/usr/bin/env python3
"""
Fix Category SEO Fields - Alternative approach
Исправление SEO полей категорий альтернативным методом
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config

def update_category_seo_direct():
    """Прямое обновление SEO полей через WordPress API"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    # Обновляем категорию "Машинное обучение" (ID: 4)
    category_id = 4
    
    # Пробуем разные варианты обновления
    update_variants = [
        # Вариант 1: Прямые Yoast поля
        {
            'yoast_wpseo_title': 'Машинное обучение - ML новости и исследования | AI Lynx',
            'yoast_wpseo_metadesc': 'Актуальные новости машинного обучения: алгоритмы, нейросети, исследования. Прорывы в области ML и практические применения.',
            'yoast_wpseo_focuskw': 'машинное обучение'
        },
        # Вариант 2: Через мета
        {
            'meta': {
                'yoast_wpseo_title': 'Машинное обучение - ML новости и исследования | AI Lynx',
                'yoast_wpseo_metadesc': 'Актуальные новости машинного обучения: алгоритмы, нейросети, исследования. Прорывы в области ML и практические применения.',
                'yoast_wpseo_focuskw': 'машинное обучение'
            }
        },
        # Вариант 3: С подчеркиваниями в мета
        {
            'meta': {
                '_yoast_wpseo_title': 'Машинное обучение - ML новости и исследования | AI Lynx',
                '_yoast_wpseo_metadesc': 'Актуальные новости машинного обучения: алгоритмы, нейросети, исследования. Прорывы в области ML и практические применения.',
                '_yoast_wpseo_focuskw': 'машинное обучение'
            }
        }
    ]
    
    for i, variant in enumerate(update_variants, 1):
        print(f'\n🔄 Пробуем вариант {i}...')
        
        try:
            response = requests.post(
                f"{config.wordpress_api_url}/categories/{category_id}",
                json=variant,
                auth=auth
            )
            
            print(f'Статус: {response.status_code}')
            if response.status_code == 200:
                print('✅ Успешно обновлено!')
                
                # Проверяем результат
                check_response = requests.get(f"{config.wordpress_api_url}/categories/{category_id}", auth=auth)
                if check_response.status_code == 200:
                    cat = check_response.json()
                    yoast_head = cat.get('yoast_head', '')
                    if 'ML новости и исследования' in yoast_head:
                        print('✅ SEO заголовок применился!')
                        return True
                    else:
                        print('❌ SEO заголовок не изменился')
            else:
                print(f'❌ Ошибка: {response.text[:200]}')
                
        except Exception as e:
            print(f'❌ Исключение: {e}')
    
    return False


def check_yoast_capabilities():
    """Проверка возможностей Yoast через API"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🔍 Проверяем Yoast API эндпоинты...')
    
    # Проверяем доступные Yoast эндпоинты
    yoast_endpoints = [
        '/yoast/v1/',
        '/wp/v2/',
        '/wp/v2/categories/4?context=edit'
    ]
    
    for endpoint in yoast_endpoints:
        try:
            response = requests.get(f"https://ailynx.ru/wp-json{endpoint}", auth=auth)
            print(f'{endpoint}: {response.status_code}')
            if response.status_code == 200 and 'yoast' in endpoint:
                data = response.json()
                print(f'  Yoast данные: {list(data.keys())[:5]}')
        except Exception as e:
            print(f'{endpoint}: Ошибка - {e}')


def main():
    print('🔧 Исправление SEO полей категорий')
    print('=' * 50)
    
    # Сначала проверим возможности Yoast
    check_yoast_capabilities()
    
    # Попробуем обновить SEO
    print('\n📝 Обновляем SEO поля...')
    if update_category_seo_direct():
        print('\n✅ SEO поля успешно обновлены!')
    else:
        print('\n❌ Не удалось обновить SEO поля через API')
        print('\nℹ️  Возможные причины:')
        print('1. Yoast SEO API не активирован')
        print('2. Нужны дополнительные права доступа')
        print('3. Требуется прямое обращение к базе данных')


if __name__ == "__main__":
    main()