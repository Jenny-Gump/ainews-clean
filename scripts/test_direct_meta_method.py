#!/usr/bin/env python3
"""
Test Direct Meta Method (like in your other project)
Тест прямого метода через meta поля (как в вашем другом проекте)
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
import time

def test_direct_meta_update():
    """Тест прямого обновления через meta поля"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🧪 Тестирование прямого метода через meta поля')
    print('=' * 60)
    
    test_category = 4  # Машинное обучение
    
    # Ваш метод - прямое обращение к meta полям
    direct_meta_data = {
        "meta": {
            "_yoast_wpseo_title": "ТЕСТ: Машинное обучение | AI Lynx",
            "_yoast_wpseo_metadesc": "Тестовое мета-описание через прямой метод meta полей WordPress REST API."
        }
    }
    
    print(f'📤 Отправляем данные через прямой meta метод для категории {test_category}...')
    print(f'   Title: {direct_meta_data["meta"]["_yoast_wpseo_title"]}')
    print(f'   Description: {direct_meta_data["meta"]["_yoast_wpseo_metadesc"]}')
    
    try:
        # Используем PATCH как в вашем примере
        response = requests.patch(
            f'{config.wordpress_api_url}/categories/{test_category}',
            json=direct_meta_data,
            auth=auth
        )
        
        print(f'\n📥 Ответ сервера: {response.status_code}')
        
        if response.status_code == 200:
            result = response.json()
            print('✅ Запрос успешен!')
            
            # Проверяем что вернулось
            meta_data = result.get('meta', {})
            print(f'📊 Возвращенные meta данные:')
            
            for key, value in meta_data.items():
                if '_yoast_wpseo_' in key:
                    print(f'   {key}: {value}')
            
            # Проверяем через наш плагин для сравнения
            yoast_title = result.get('yoast_title', 'НЕТ')
            yoast_desc = result.get('yoast_description', 'НЕТ')
            
            print(f'\n🔍 Через наш плагин:')
            print(f'   yoast_title: {yoast_title}')
            print(f'   yoast_description: {yoast_desc}')
            
            # Проверяем yoast_head_json
            yoast_head_json = result.get('yoast_head_json', {})
            if yoast_head_json:
                actual_title = yoast_head_json.get('title', '')
                actual_desc = yoast_head_json.get('description', '')
                
                print(f'\n📊 Yoast Head JSON:')
                print(f'   title: {actual_title}')
                print(f'   description: {actual_desc}')
                
                # Проверяем совпадение
                expected_title = direct_meta_data["meta"]["_yoast_wpseo_title"]
                expected_desc = direct_meta_data["meta"]["_yoast_wpseo_metadesc"]
                
                title_match = expected_title in actual_title if expected_title else False
                desc_match = expected_desc == actual_desc if expected_desc else False
                
                if title_match and desc_match:
                    print('\n🎉 УСПЕХ! Прямой meta метод работает!')
                    return True
                else:
                    print('\n❌ Данные не совпадают с ожидаемыми')
            else:
                print('\n❌ yoast_head_json пуст')
                
        else:
            print(f'❌ Ошибка: {response.status_code}')
            print(f'   Текст ошибки: {response.text[:200]}')
            
    except Exception as e:
        print(f'❌ Исключение: {e}')
    
    return False

def mass_update_direct_meta():
    """Массовое обновление через прямой meta метод"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🚀 Массовое обновление через прямой meta метод')
    print('=' * 60)
    
    # SEO данные для всех категорий
    CATEGORIES_META = {
        2: {  # Новости
            "_yoast_wpseo_title": "AI Новости: последние события ИИ | AI Lynx",
            "_yoast_wpseo_metadesc": "Последние новости искусственного интеллекта: прорывы в исследованиях, релизы AI-продуктов, тренды развития индустрии."
        },
        3: {  # LLM
            "_yoast_wpseo_title": "LLM новости: большие языковые модели | AI Lynx",
            "_yoast_wpseo_metadesc": "Актуальные новости больших языковых моделей (LLM) - GPT, Claude, Gemini. Обзоры, сравнения и анализ развития AI технологий."
        },
        4: {  # Машинное обучение
            "_yoast_wpseo_title": "Машинное обучение: новости ML и нейросетей | AI Lynx",
            "_yoast_wpseo_metadesc": "Новости машинного обучения и нейронных сетей. Алгоритмы, исследования, практические применения ML в бизнесе и науке."
        },
        5: {  # Техника
            "_yoast_wpseo_title": "AI Техника: новости железа и GPU | AI Lynx",
            "_yoast_wpseo_metadesc": "Новости AI техники и железа: GPU, TPU, чипы для нейросетей. Обзоры оборудования, облачных платформ и инструментов."
        },
        6: {  # Digital
            "_yoast_wpseo_title": "Digital AI: цифровые технологии и ИИ | AI Lynx",
            "_yoast_wpseo_metadesc": "AI в цифровом мире: интернет, соцсети, e-commerce, маркетинг. Персонализация, рекомендации, автоматизация процессов."
        }
    }
    
    success_count = 0
    
    for cat_id, meta_fields in CATEGORIES_META.items():
        print(f'\n🔄 Обновляем категорию {cat_id}...')
        
        meta_data = {"meta": meta_fields}
        
        try:
            response = requests.patch(
                f'{config.wordpress_api_url}/categories/{cat_id}',
                json=meta_data,
                auth=auth
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f'✅ Успешно: {result.get("name", "")}')
                
                # Проверяем yoast_head_json
                yoast_head_json = result.get('yoast_head_json', {})
                if yoast_head_json:
                    actual_desc = yoast_head_json.get('description', '')
                    if actual_desc and len(actual_desc) > 50:
                        print(f'   🎉 Мета-описание работает: {actual_desc[:60]}...')
                        success_count += 1
                    else:
                        print(f'   ⚠️ Мета-описание короткое: {actual_desc}')
                else:
                    print(f'   ❌ yoast_head_json пуст')
            else:
                print(f'❌ Ошибка {response.status_code}: {response.text[:100]}')
                
            time.sleep(0.3)
            
        except Exception as e:
            print(f'❌ Исключение: {e}')
    
    print(f'\n📊 Результат: {success_count}/{len(CATEGORIES_META)} категорий успешно обновлено')
    return success_count > 0

def main():
    print('🔍 Тестирование прямого meta метода (как в вашем проекте)')
    print('=' * 70)
    
    # Сначала тестируем на одной категории
    if test_direct_meta_update():
        print('\n🎉 Прямой meta метод работает! Запускаем массовое обновление...')
        
        if mass_update_direct_meta():
            print('\n✅ Массовое обновление завершено!')
            print('\n💡 Теперь мета-описания должны работать через прямые meta поля!')
        else:
            print('\n❌ Проблемы с массовым обновлением')
    else:
        print('\n❌ Прямой meta метод не работает')
        print('\n💡 Возможные причины:')
        print('   1. WordPress не поддерживает meta поля для категорий')
        print('   2. Нужны дополнительные права доступа')
        print('   3. Yoast SEO настроен по-другому на этом сайте')

if __name__ == "__main__":
    main()