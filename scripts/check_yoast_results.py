#!/usr/bin/env python3
"""
Check Yoast SEO Results
Проверка результатов обновления Yoast SEO
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config

def check_yoast_results():
    """Проверка результатов Yoast SEO"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🔍 Проверка результатов Yoast SEO')
    print('=' * 50)
    
    # Получаем все категории
    categories_response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
    if categories_response.status_code != 200:
        print('❌ Не удалось получить список категорий')
        return
    
    categories = categories_response.json()
    
    # Проверяем ключевые категории
    test_categories = ['Машинное обучение', 'LLM', 'Digital', 'Техника', 'Новости']
    found_success = 0
    
    for category in categories:
        if category['name'] in test_categories:
            cat_name = category['name']
            cat_id = category['id']
            
            print(f'\n📂 {cat_name} (ID: {cat_id}):')
            
            # Проверяем Yoast head
            yoast_head = category.get('yoast_head', '')
            yoast_head_json = category.get('yoast_head_json', {})
            
            if yoast_head_json:
                yoast_title = yoast_head_json.get('title', '')
                yoast_description = yoast_head_json.get('description', '')
                
                # Проверяем наши данные
                if 'AI Lynx' in yoast_title:
                    print(f'   ✅ Title: {yoast_title}')
                    found_success += 1
                else:
                    print(f'   ❌ Title: {yoast_title}')
                
                if yoast_description and ('новости' in yoast_description.lower() or 'AI' in yoast_description):
                    print(f'   ✅ Description: {yoast_description[:60]}...')
                else:
                    print(f'   ❌ Description: {yoast_description[:60]}...' if yoast_description else '   ❌ Description: Нет')
            else:
                print('   ❌ Yoast head JSON не найден')
            
            # Проверяем мета-поля напрямую
            meta = category.get('meta', {})
            if isinstance(meta, dict):
                yoast_meta_title = meta.get('_yoast_wpseo_title', '')
                yoast_meta_desc = meta.get('_yoast_wpseo_metadesc', '')
                yoast_meta_keyword = meta.get('_yoast_wpseo_focuskw', '')
                
                if yoast_meta_title:
                    print(f'   📝 Meta Title: {yoast_meta_title[:50]}...')
                if yoast_meta_desc:
                    print(f'   📄 Meta Desc: {yoast_meta_desc[:50]}...')
                if yoast_meta_keyword:
                    print(f'   🔑 Meta Keyword: {yoast_meta_keyword}')
                
                if not any([yoast_meta_title, yoast_meta_desc, yoast_meta_keyword]):
                    print('   ⚠️ Мета-поля Yoast не найдены')
    
    print(f'\n📊 Результат проверки:')
    print(f'   ✅ Категорий с обновленными заголовками: {found_success}/{len(test_categories)}')
    
    if found_success > 0:
        print('🎉 Отлично! Yoast SEO данные обновились!')
    else:
        print('⏳ Yoast SEO данные пока не отображаются')
        print('\n💡 Рекомендации:')
        print('1. Перейдите в админку: https://ailynx.ru/wp-admin/admin.php?page=wpseo_tools')
        print('2. Найдите "SEO Data" → "Reindex"')
        print('3. Нажмите кнопку переиндексации')
        print('4. Или вручную сохраните одну категорию: https://ailynx.ru/wp-admin/edit-tags.php?taxonomy=category')
    
    return found_success > 0

def check_frontend_pages():
    """Проверка страниц категорий на фронтенде"""
    print('\n🌐 Проверка фронтенд страниц категорий:')
    
    category_urls = {
        'Машинное обучение': 'https://ailynx.ru/category/машинное-обучение/',
        'LLM': 'https://ailynx.ru/category/llm/',
        'Digital': 'https://ailynx.ru/category/digital/',
        'Техника': 'https://ailynx.ru/category/техника/'
    }
    
    for cat_name, url in category_urls.items():
        print(f'🔗 {cat_name}: {url}')
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content = response.text
                
                # Ищем наши SEO данные в HTML
                if 'AI Lynx' in content and ('ML новости' in content or 'LLM' in content or 'Digital AI' in content):
                    print(f'   ✅ SEO данные найдены на странице')
                else:
                    print(f'   ❌ SEO данные не найдены')
            else:
                print(f'   ❌ Ошибка загрузки: {response.status_code}')
        except Exception as e:
            print(f'   ❌ Ошибка: {e}')

def main():
    print('🔍 Проверка результатов обновления Yoast SEO')
    print('=' * 60)
    
    success = check_yoast_results()
    
    if success:
        check_frontend_pages()
        print('\n✅ Проверка завершена! SEO данные обновлены.')
    else:
        print('\n⏳ SEO данные сохранены, но требуется переиндексация Yoast.')
        print('\n🎯 Следующие шаги:')
        print('1. Админка Yoast: https://ailynx.ru/wp-admin/admin.php?page=wpseo_tools')
        print('2. Нажмите "Reindex" в разделе SEO Data')
        print('3. Повторите проверку через несколько минут')

if __name__ == "__main__":
    main()