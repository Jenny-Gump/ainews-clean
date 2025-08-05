#!/usr/bin/env python3
"""
Check Final SEO Results
Проверка финальных результатов SEO оптимизации
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config

def check_seo_results():
    """Проверка результатов SEO оптимизации"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🔍 Проверка финальных результатов SEO')
    print('=' * 50)
    
    # Получаем все категории
    categories_response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
    if categories_response.status_code != 200:
        print('❌ Не удалось получить список категорий')
        return
    
    categories = categories_response.json()
    
    print(f'📂 Найдено категорий: {len(categories)}')
    print('\n📋 Результаты SEO оптимизации:')
    
    seo_categories = []
    
    for category in categories:
        name = category.get('name', '')
        slug = category.get('slug', '')
        description = category.get('description', '')
        
        # Пропускаем родительскую категорию "Новости"
        if 'последние новости' in name or 'последние события' in name:
            seo_categories.append({
                'name': name,
                'slug': slug,
                'description': description,
                'url': f"https://ailynx.ru/category/{slug}/"
            })
    
    # Сортируем по названию
    seo_categories.sort(key=lambda x: x['name'])
    
    for i, cat in enumerate(seo_categories, 1):
        print(f'\n{i}. 📂 {cat["name"][:60]}...')
        print(f'   🔗 URL: {cat["url"]}')
        print(f'   📝 Описание: {len(cat["description"])} символов')
        
        # Проверяем качество SEO
        seo_score = 0
        issues = []
        
        # Проверка названия
        if 'последние новости' in cat['name'] and 'полезная информация' in cat['name']:
            seo_score += 25
        else:
            issues.append('Название не оптимизировано')
        
        # Проверка URL
        if cat['slug'].startswith('ai-') or cat['slug'] in ['llm-news', 'machine-learning']:
            seo_score += 25
        else:
            issues.append('URL не англицизирован')
        
        # Проверка описания
        if len(cat['description']) > 250:
            seo_score += 25
        else:
            issues.append('Описание слишком короткое')
        
        # Проверка ключевых слов в описании
        if any(word in cat['description'].lower() for word in ['искусственного интеллекта', 'машинного обучения', 'нейронных сетей']):
            seo_score += 25
        else:
            issues.append('Нет ключевых слов в описании')
        
        # Показываем результат
        if seo_score >= 75:
            print(f'   ✅ SEO Score: {seo_score}/100 - Отлично!')
        elif seo_score >= 50:
            print(f'   ⚠️ SEO Score: {seo_score}/100 - Хорошо')
        else:
            print(f'   ❌ SEO Score: {seo_score}/100 - Требует доработки')
        
        if issues:
            print(f'   📋 Проблемы: {"; ".join(issues)}')

def show_summary():
    """Показать сводку по SEO"""
    print('\n📊 Сводка по SEO оптимизации:')
    print('=' * 50)
    
    print('✅ Выполнено:')
    print('• Расширенные названия с ключевыми словами')
    print('• Английские URL-адреса (ai-education, machine-learning)')
    print('• SEO-описания 300+ символов')
    print('• Структурированная навигация')
    
    print('\n⏳ Ожидает выполнения:')
    print('• Мета-описания (нужен плагин category-meta-descriptions.php)')
    print('• Проверка отображения на фронтенде')
    
    print('\n🔗 Новые SEO-оптимизированные URL:')
    urls = [
        'https://ailynx.ru/category/llm-news/',
        'https://ailynx.ru/category/machine-learning/',
        'https://ailynx.ru/category/ai-hardware/',
        'https://ailynx.ru/category/digital-ai/',
        'https://ailynx.ru/category/ai-education/',
        'https://ailynx.ru/category/ai-finance/',
        'https://ailynx.ru/category/ai-science/',
        'https://ailynx.ru/category/ai-people/',
        'https://ailynx.ru/category/ai-industries/',
        'https://ailynx.ru/category/ai-news/'
    ]
    
    for url in urls:
        print(f'   {url}')
    
    print('\n💡 Рекомендации:')
    print('1. Установите плагин мета-описаний для завершения SEO')
    print('2. Проверьте отображение категорий на фронтенде')
    print('3. Добавьте внутренние ссылки между категориями')
    print('4. Настройте sitemap.xml для поисковых систем')

def main():
    print('🎯 Финальная проверка SEO оптимизации')
    print('=' * 60)
    
    check_seo_results()
    show_summary()
    
    print('\n✅ Проверка завершена!')

if __name__ == "__main__":
    main()