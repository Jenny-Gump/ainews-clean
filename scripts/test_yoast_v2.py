#!/usr/bin/env python3
"""
Test Yoast Category API Plugin V2
Тестирование улучшенной версии плагина
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
import time

def test_v2_plugin():
    """Тест плагина V2"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🧪 Тестирование Yoast Category API V2...')
    
    # Проверяем доступность V2
    response = requests.get('https://ailynx.ru/wp-json/yoast-category/v2/category/4', auth=auth)
    
    if response.status_code == 200:
        print('✅ Плагин V2 работает!')
        data = response.json()
        print(f'📂 Категория: {data.get("category_name")}')
        print(f'📝 Yoast Title: {data.get("yoast_title") or "Не установлен"}')
        print(f'🔍 Yoast Indexable: {data.get("yoast_indexable")}')
        
        # Тестируем обновление
        print(f'\n🔄 Обновляем категорию через V2...')
        update_data = {
            'yoast_title': 'ТЕСТ - Машинное обучение и ИИ | AI Lynx',
            'yoast_desc': 'Тестовое описание для проверки работы плагина V2',
            'yoast_keyword': 'тест машинное обучение'
        }
        
        update_response = requests.post(
            'https://ailynx.ru/wp-json/yoast-category/v2/category/4',
            json=update_data,
            auth=auth
        )
        
        if update_response.status_code == 200:
            result = update_response.json()
            print('✅ Обновление через V2 успешно!')
            print(f'   Yoast updated: {result.get("yoast_updated")}')
            
            # Ждем и проверяем результат
            print('\n⏳ Ждем обновления Yoast...')
            time.sleep(3)
            
            # Проверяем через WordPress API
            wp_check = requests.get(f'{config.wordpress_api_url}/categories/4', auth=auth)
            if wp_check.status_code == 200:
                wp_data = wp_check.json()
                yoast_head = wp_data.get('yoast_head', '')
                
                if 'ТЕСТ - Машинное обучение' in yoast_head:
                    print('🎉 УСПЕХ! Yoast показывает наш заголовок!')
                else:
                    print('❌ Yoast все еще не обновился')
                    print(f'🔍 Текущий title в head: {yoast_head.split("<title>")[1].split("</title>")[0] if "<title>" in yoast_head else "Не найден"}')
            
            # Очищаем кэш принудительно
            print('\n🧹 Очищаем кэш...')
            cache_response = requests.post('https://ailynx.ru/wp-json/yoast-category/v2/clear-cache', auth=auth)
            print(f'   Очистка кэша: {cache_response.status_code}')
        else:
            print(f'❌ Ошибка обновления V2: {update_response.status_code}')
            print(f'   Ответ: {update_response.text[:200]}')
        
        return True
    else:
        print('❌ Плагин V2 не найден')
        return False


def revert_test_changes():
    """Возвращаем нормальные данные"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔄 Возвращаем нормальные данные...')
    
    normal_data = {
        'yoast_title': 'Машинное обучение - ML новости и исследования | AI Lynx',
        'yoast_desc': 'Актуальные новости машинного обучения: алгоритмы, нейросети, исследования. Прорывы в области ML и практические применения.',
        'yoast_keyword': 'машинное обучение'
    }
    
    response = requests.post(
        'https://ailynx.ru/wp-json/yoast-category/v2/category/4',
        json=normal_data,
        auth=auth
    )
    
    if response.status_code == 200:
        print('✅ Данные восстановлены')
    else:
        print(f'❌ Ошибка восстановления: {response.status_code}')


def main():
    print('🔧 Тестирование улучшенного плагина')
    print('=' * 50)
    
    if test_v2_plugin():
        time.sleep(2)
        revert_test_changes()
        
        print('\n💡 Инструкции:')
        print('1. Замените старый плагин на V2 в WordPress')
        print('2. Загрузите yoast-category-api-v2.php')
        print('3. Активируйте новую версию')
    else:
        print('\n💡 Сначала установите плагин V2:')
        print('1. Деактивируйте старую версию')  
        print('2. Загрузите yoast-category-api-v2.php')
        print('3. Активируйте V2')


if __name__ == "__main__":
    main()