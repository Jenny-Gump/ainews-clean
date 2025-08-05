#!/usr/bin/env python3
"""
Test Yoast REST API Extension
Тестирование расширения Yoast REST API
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
import time

def test_yoast_extension():
    """Тест расширения Yoast REST API"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🧪 Тестирование Yoast REST API Extension')
    print('=' * 50)
    
    # Тестируем на категории "Машинное обучение" (ID: 4)
    category_id = 4
    
    print(f'📂 Тестируем категорию ID: {category_id}')
    
    # Шаг 1: Получаем текущие данные с новыми полями
    print('\n1️⃣ Получаем текущие Yoast поля...')
    
    response = requests.get(f'{config.wordpress_api_url}/categories/{category_id}', auth=auth)
    
    if response.status_code == 200:
        data = response.json()
        print(f'✅ Категория получена: {data.get("name")[:50]}...')
        
        # Проверяем новые Yoast поля
        yoast_fields = ['yoast_title', 'yoast_description', 'yoast_keyword', 'yoast_canonical']
        
        for field in yoast_fields:
            value = data.get(field, 'НЕТ ПОЛЯ')
            if value and value != 'НЕТ ПОЛЯ':
                print(f'  ✅ {field}: {value[:50]}...')
            else:
                print(f'  ❌ {field}: {value}')
    else:
        print(f'❌ Ошибка получения категории: {response.status_code}')
        return False
    
    # Шаг 2: Обновляем Yoast поля
    print('\n2️⃣ Обновляем Yoast SEO поля...')
    
    test_data = {
        'yoast_title': 'ТЕСТ: Машинное обучение - новости и обучение | AI Lynx',
        'yoast_description': 'Тестовое мета-описание для проверки Yoast REST API Extension. Новости машинного обучения, алгоритмы, нейронные сети.',
        'yoast_keyword': 'машинное обучение тест'
    }
    
    update_response = requests.post(
        f'{config.wordpress_api_url}/categories/{category_id}',
        json=test_data,
        auth=auth
    )
    
    if update_response.status_code == 200:
        result = update_response.json()
        print('✅ Обновление успешно!')
        
        # Проверяем обновленные поля
        for field, expected_value in test_data.items():
            actual_value = result.get(field, 'НЕТ')
            if actual_value == expected_value:
                print(f'  ✅ {field}: Обновлено правильно')
            else:
                print(f'  ❌ {field}: Ожидали "{expected_value[:30]}...", получили "{actual_value}"')
    else:
        print(f'❌ Ошибка обновления: {update_response.status_code}')
        print(f'   Ответ: {update_response.text[:200]}')
        return False
    
    # Шаг 3: Проверяем сохранение после паузы
    print('\n3️⃣ Проверяем сохранение (через 2 сек)...')
    time.sleep(2)
    
    verify_response = requests.get(f'{config.wordpress_api_url}/categories/{category_id}', auth=auth)
    
    if verify_response.status_code == 200:
        verify_data = verify_response.json()
        
        for field, expected_value in test_data.items():
            actual_value = verify_data.get(field, 'НЕТ')
            if actual_value == expected_value:
                print(f'  ✅ {field}: Сохранено в БД')
            else:
                print(f'  ❌ {field}: Не сохранено в БД')
    else:
        print(f'❌ Ошибка проверки: {verify_response.status_code}')
    
    return True

def update_all_categories_yoast():
    """Обновление всех категорий через Yoast REST API"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🚀 Массовое обновление через Yoast REST API Extension')
    print('=' * 60)
    
    # SEO данные для категорий
    CATEGORIES_YOAST_SEO = {
        3: {  # LLM
            'yoast_title': 'LLM новости: большие языковые модели | AI Lynx',
            'yoast_description': 'Актуальные новости больших языковых моделей (LLM) - GPT, Claude, Gemini. Обзоры, сравнения и анализ развития AI технологий.',
            'yoast_keyword': 'LLM новости'
        },
        4: {  # Машинное обучение
            'yoast_title': 'Машинное обучение: новости ML и нейросетей | AI Lynx',
            'yoast_description': 'Новости машинного обучения и нейронных сетей. Алгоритмы, исследования, практические применения ML в бизнесе и науке.',
            'yoast_keyword': 'машинное обучение'
        },
        5: {  # AI Техника
            'yoast_title': 'AI Техника: новости железа и GPU | AI Lynx',
            'yoast_description': 'Новости AI техники и железа: GPU, TPU, чипы для нейросетей. Обзоры оборудования, облачных платформ и инструментов.',
            'yoast_keyword': 'AI техника'
        },
        6: {  # Digital AI
            'yoast_title': 'Digital AI: цифровые технологии и ИИ | AI Lynx',
            'yoast_description': 'AI в цифровом мире: интернет, соцсети, e-commerce, маркетинг. Персонализация, рекомендации, автоматизация процессов.',
            'yoast_keyword': 'digital AI'
        },
        7: {  # AI в Финансах
            'yoast_title': 'AI в Финансах: финтех и алготрейдинг | AI Lynx',
            'yoast_description': 'AI в финансах: алготрейдинг, анализ рисков, банковская автоматизация. Инвестиции в AI-стартапы и финтех решения.',
            'yoast_keyword': 'AI финансы'
        },
        8: {  # AI в Науке
            'yoast_title': 'AI в Науке: исследования и открытия | AI Lynx',
            'yoast_description': 'AI в науке: предсказание белков, поиск лекарств, автоматизация экспериментов. Машинное обучение в физике, химии, биологии.',
            'yoast_keyword': 'AI наука'
        },
        9: {  # AI Образование
            'yoast_title': 'AI Образование: курсы и карьера в ИИ | AI Lynx',
            'yoast_description': 'AI образование: курсы машинного обучения, сертификации, карьера в ИИ. Как стать AI-инженером и data scientist.',
            'yoast_keyword': 'AI образование'
        },
        10: {  # AI в Индустриях
            'yoast_title': 'AI в Индустриях: применение по отраслям | AI Lynx',
            'yoast_description': 'AI в различных индустриях: сельское хозяйство, медицина, производство, логистика. Умные города и автоматизация.',
            'yoast_keyword': 'AI индустрии'
        },
        11: {  # Люди в AI
            'yoast_title': 'Люди в AI: эксперты и карьера | AI Lynx',
            'yoast_description': 'Люди в AI индустрии: интервью с экспертами, истории успеха, карьерные пути. Этика ИИ и влияние на рынок труда.',
            'yoast_keyword': 'люди AI'
        },
        2: {  # AI Новости
            'yoast_title': 'AI Новости: последние события ИИ | AI Lynx',
            'yoast_description': 'Последние новости искусственного интеллекта: прорывы в исследованиях, релизы AI-продуктов, тренды развития индустрии.',
            'yoast_keyword': 'AI новости'
        }
    }
    
    success_count = 0
    
    for cat_id, yoast_data in CATEGORIES_YOAST_SEO.items():
        print(f'\n🔄 Обновляем категорию ID {cat_id}...')
        
        try:
            response = requests.post(
                f'{config.wordpress_api_url}/categories/{cat_id}',
                json=yoast_data,
                auth=auth
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f'✅ Успешно: {result.get("name", "")[:40]}...')
                print(f'   Title: {result.get("yoast_title", "НЕТ")[:50]}...')
                print(f'   Description: {len(result.get("yoast_description", ""))} символов')
                print(f'   Keyword: {result.get("yoast_keyword", "НЕТ")}')
                
                success_count += 1
            else:
                print(f'❌ Ошибка {response.status_code}: {response.text[:100]}')
                
            time.sleep(0.3)
            
        except Exception as e:
            print(f'❌ Исключение: {e}')
    
    print(f'\n📊 Результат: {success_count}/{len(CATEGORIES_YOAST_SEO)} категорий обновлено')
    return success_count > 0

def main():
    print('🔧 Тестирование Yoast REST API Extension')
    print('=' * 60)
    
    # Сначала тестируем расширение
    if test_yoast_extension():
        print('\n🎉 Расширение работает! Запускаем массовое обновление...')
        
        if update_all_categories_yoast():
            print('\n✅ Массовое обновление Yoast SEO завершено!')
            print('\n💡 Проверьте результаты:')
            print('1. Админка категорий: https://ailynx.ru/wp-admin/edit-tags.php?taxonomy=category')
            print('2. Любая категория: https://ailynx.ru/category/machine-learning/')
            print('3. Исходный код страницы должен содержать наши мета-теги')
        else:
            print('\n❌ Ошибка массового обновления')
    else:
        print('\n⏳ Сначала установите и активируйте плагин yoast-rest-api-extension.php')

if __name__ == "__main__":
    main()