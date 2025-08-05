#!/usr/bin/env python3
"""
Verify Yoast SEO on Frontend
Проверка Yoast SEO на фронтенде
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config

def check_category_seo_on_frontend():
    """Проверка SEO данных на фронтенде"""
    
    # Тестовые URL категорий
    test_urls = [
        ('machine-learning', 'Машинное обучение'),
        ('llm-news', 'LLM'),
        ('ai-hardware', 'AI Техника'),
        ('digital-ai', 'Digital AI'),
        ('ai-education', 'AI Образование')
    ]
    
    print('🔍 Проверка Yoast SEO на фронтенде')
    print('=' * 50)
    
    found_yoast_data = 0
    
    for slug, name in test_urls:
        url = f'https://ailynx.ru/category/{slug}/'
        print(f'\n📂 {name}:')
        print(f'🔗 {url}')
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                html_content = response.text
                
                # Ищем мета-теги
                title_found = False
                description_found = False
                
                # Поиск title тега
                if '<title>' in html_content:
                    title_start = html_content.find('<title>') + 7
                    title_end = html_content.find('</title>', title_start)
                    if title_end > title_start:
                        title = html_content[title_start:title_end].strip()
                        if 'AI Lynx' in title and len(title) > 20:
                            print(f'   ✅ Title: {title}')
                            title_found = True
                        else:
                            print(f'   ❌ Title: {title}')
                
                # Поиск meta description
                if 'name="description"' in html_content:
                    desc_start = html_content.find('name="description" content="')
                    if desc_start > 0:
                        desc_start += 28  # длина 'name="description" content="'
                        desc_end = html_content.find('"', desc_start)
                        if desc_end > desc_start:
                            description = html_content[desc_start:desc_end].strip()
                            if len(description) > 50:
                                print(f'   ✅ Description: {description[:60]}...')
                                description_found = True
                            else:
                                print(f'   ❌ Description: {description}')
                
                # Поиск Open Graph данных (Yoast добавляет их)
                og_title = False
                if 'property="og:title"' in html_content:
                    og_start = html_content.find('property="og:title" content="')
                    if og_start > 0:
                        og_start += 29
                        og_end = html_content.find('"', og_start)
                        if og_end > og_start:
                            og_title_text = html_content[og_start:og_end]
                            if 'AI Lynx' in og_title_text:
                                print(f'   ✅ OG Title: {og_title_text[:50]}...')
                                og_title = True
                
                # Счетчик успешных результатов
                if title_found and description_found:
                    found_yoast_data += 1
                    print(f'   🎉 Yoast SEO полностью работает!')
                elif title_found or description_found:
                    print(f'   ⚠️ Yoast SEO частично работает')
                else:
                    print(f'   ❌ Yoast SEO не найден')
                    
            else:
                print(f'   ❌ Ошибка загрузки: {response.status_code}')
                
        except Exception as e:
            print(f'   ❌ Ошибка: {e}')
    
    print(f'\n📊 Результат проверки:')
    print(f'   ✅ Полностью работающих категорий: {found_yoast_data}/{len(test_urls)}')
    
    if found_yoast_data >= len(test_urls) // 2:
        print('🎉 Yoast SEO успешно работает на фронтенде!')
        return True
    else:
        print('⚠️ Yoast SEO требует дополнительной настройки')
        return False

def check_api_vs_frontend():
    """Сравнение данных API и фронтенда"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔄 Сравнение API и фронтенд данных')
    print('=' * 50)
    
    # Получаем данные из API
    category_id = 4  # Машинное обучение
    api_response = requests.get(f'{config.wordpress_api_url}/categories/{category_id}', auth=auth)
    
    if api_response.status_code == 200:
        api_data = api_response.json()
        api_title = api_data.get('yoast_title', '')
        api_description = api_data.get('yoast_description', '')
        
        print(f'📊 API данные:')
        print(f'   Title: {api_title}')
        print(f'   Description: {api_description}')
        
        # Получаем данные с фронтенда
        frontend_url = 'https://ailynx.ru/category/machine-learning/'
        frontend_response = requests.get(frontend_url, timeout=10)
        
        if frontend_response.status_code == 200:
            html_content = frontend_response.text
            
            # Извлекаем title
            if '<title>' in html_content:
                title_start = html_content.find('<title>') + 7
                title_end = html_content.find('</title>', title_start)
                frontend_title = html_content[title_start:title_end].strip()
            else:
                frontend_title = 'НЕ НАЙДЕН'
            
            # Извлекаем description
            frontend_description = 'НЕ НАЙДЕН'
            if 'name="description"' in html_content:
                desc_start = html_content.find('name="description" content="')
                if desc_start > 0:
                    desc_start += 28
                    desc_end = html_content.find('"', desc_start)
                    if desc_end > desc_start:
                        frontend_description = html_content[desc_start:desc_end].strip()
            
            print(f'\n🌐 Фронтенд данные:')
            print(f'   Title: {frontend_title}')
            print(f'   Description: {frontend_description}')
            
            # Сравнение
            title_match = api_title in frontend_title if api_title else False
            desc_match = api_description == frontend_description if api_description else False
            
            print(f'\n🔍 Сравнение:')
            print(f'   Title совпадает: {"✅" if title_match else "❌"}')
            print(f'   Description совпадает: {"✅" if desc_match else "❌"}')
            
            if title_match and desc_match:
                print('🎉 API и фронтенд полностью синхронизированы!')
                return True
            else:
                print('⚠️ Есть расхождения между API и фронтендом')
                return False
        else:
            print(f'❌ Ошибка загрузки фронтенда: {frontend_response.status_code}')
    else:
        print(f'❌ Ошибка API: {api_response.status_code}')
    
    return False

def main():
    print('🔍 Проверка Yoast SEO на фронтенде')
    print('=' * 60)
    
    frontend_works = check_category_seo_on_frontend()
    api_sync = check_api_vs_frontend()
    
    print('\n📋 ИТОГОВЫЙ ОТЧЕТ:')
    print('=' * 30)
    
    if frontend_works and api_sync:
        print('🎉 УСПЕХ! Yoast SEO полностью интегрирован')
        print('✅ Мета-теги отображаются на фронтенде')
        print('✅ API данные синхронизированы с фронтендом')
        print('✅ SEO оптимизация завершена')
        
        print('\n🔗 Проверьте категории:')
        print('• https://ailynx.ru/category/machine-learning/')
        print('• https://ailynx.ru/category/llm-news/')
        print('• https://ailynx.ru/category/ai-hardware/')
        print('• https://ailynx.ru/category/digital-ai/')
        
    else:
        print('⚠️ Требуется дополнительная настройка')
        if not frontend_works:
            print('❌ Мета-теги не отображаются корректно')
        if not api_sync:
            print('❌ API и фронтенд не синхронизированы')
        
        print('\n💡 Рекомендации:')
        print('1. Очистить кэш WordPress')
        print('2. Проверить настройки Yoast SEO')
        print('3. Пересохранить категории в админке')

if __name__ == "__main__":
    main()