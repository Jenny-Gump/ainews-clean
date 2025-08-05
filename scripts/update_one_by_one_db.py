#!/usr/bin/env python3
"""
Update Categories One by One via DB Plugin
Обновление категорий по одной через БД плагин
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
import time

# SEO данные для всех категорий
CATEGORY_SEO_DATA = {
    "LLM": {
        "title": "Новости LLM - Большие языковые модели | AI Lynx",
        "desc": "Последние новости о больших языковых моделях: GPT, Claude, Gemini, LLaMA. Обзоры, сравнения и анализ развития LLM технологий.",
        "keyword": "LLM новости"
    },
    "Машинное обучение": {
        "title": "Машинное обучение - ML новости и исследования | AI Lynx",
        "desc": "Актуальные новости машинного обучения: алгоритмы, нейросети, исследования. Прорывы в области ML и практические применения.",
        "keyword": "машинное обучение"
    },
    "Техника": {
        "title": "AI Техника - Железо и софт для ИИ | AI Lynx",
        "desc": "Новости о технике для ИИ: GPU, TPU, чипы, облачные платформы. Обзоры железа и программного обеспечения для машинного обучения.",
        "keyword": "AI техника"
    },
    "Digital": {
        "title": "Digital AI - Цифровая трансформация с ИИ | AI Lynx",
        "desc": "Как ИИ меняет цифровой мир: интернет, соцсети, e-commerce, маркетинг. Инновации в digital-сфере с использованием AI.",
        "keyword": "digital AI"
    },
    "Люди": {
        "title": "Люди в AI - Лидеры и визионеры ИИ | AI Lynx",
        "desc": "Истории людей, создающих будущее ИИ: интервью с исследователями, предпринимателями, визионерами индустрии искусственного интеллекта.",
        "keyword": "лидеры AI"
    },
    "Финансы": {
        "title": "AI в Финансах - ИИ в банкинге и инвестициях | AI Lynx",
        "desc": "Применение ИИ в финансах: алгоритмическая торговля, кредитные риски, инвестиции в AI-стартапы, финтех с машинным обучением.",
        "keyword": "AI финансы"
    },
    "Наука": {
        "title": "AI в Науке - Научные прорывы с ИИ | AI Lynx", 
        "desc": "Как ИИ революционизирует науку: от предсказания белков до поиска лекарств. Машинное обучение в физике, химии, биологии.",
        "keyword": "AI наука"
    },
    "Обучение": {
        "title": "AI Образование - Курсы и обучение ИИ | AI Lynx",
        "desc": "Образование в сфере ИИ: курсы, программы, сертификации по машинному обучению. Roadmap и карьера в artificial intelligence.",
        "keyword": "обучение AI"
    },
    "Другие индустрии": {
        "title": "AI в Индустриях - Применение ИИ в разных сферах | AI Lynx",
        "desc": "ИИ в различных отраслях: сельское хозяйство, космос, медицина, производство. Инновационные кейсы применения AI.",
        "keyword": "AI индустрии"
    },
    "Новости": {
        "title": "AI Новости - Последние события в мире ИИ | AI Lynx",
        "desc": "Свежие новости искусственного интеллекта: прорывы, исследования, релизы. Будьте в курсе развития AI технологий.",
        "keyword": "AI новости"
    }
}


def update_categories_one_by_one():
    """Обновление категорий по одной"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🔄 Обновление категорий по одной через БД плагин')
    print('=' * 60)
    
    # Получаем все категории
    categories_response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
    if categories_response.status_code != 200:
        print('❌ Не удалось получить список категорий')
        return False
    
    categories = categories_response.json()
    category_map = {cat['name']: cat['id'] for cat in categories}
    
    print(f'📂 Найдено категорий: {len(categories)}')
    
    success_count = 0
    
    for cat_name, seo_data in CATEGORY_SEO_DATA.items():
        if cat_name not in category_map:
            print(f'❌ {cat_name} не найдена')
            continue
            
        cat_id = category_map[cat_name]
        print(f'\n🔄 Обновляем {cat_name} (ID: {cat_id})...')
        
        try:
            # Обновляем через БД плагин
            response = requests.post(
                f'https://ailynx.ru/wp-json/yoast-db/v1/update-category/{cat_id}',
                json=seo_data,
                auth=auth
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f'✅ {cat_name}: Успешно обновлено')
                
                # Показываем детали
                results = result.get('results', {})
                for field, status in results.items():
                    print(f'   {field}: {status}')
                
                success_count += 1
                
                # Пауза между запросами
                time.sleep(0.5)
            else:
                print(f'❌ {cat_name}: Ошибка {response.status_code}')
                print(f'   Ответ: {response.text[:200]}')
                
        except Exception as e:
            print(f'❌ {cat_name}: Исключение - {e}')
    
    print(f'\n📊 Результат: {success_count}/{len(CATEGORY_SEO_DATA)} категорий обновлено')
    return success_count > 0


def check_one_category_result():
    """Проверка результата одной категории"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔍 Проверяем результат категории "Машинное обучение"...')
    
    # ID категории "Машинное обучение" = 4
    category_id = 4
    
    # Проверяем через WordPress API
    wp_response = requests.get(f'{config.wordpress_api_url}/categories/{category_id}', auth=auth)
    if wp_response.status_code == 200:
        wp_data = wp_response.json()
        yoast_head = wp_data.get('yoast_head', '')
        yoast_title = wp_data.get('yoast_head_json', {}).get('title', '')
        
        print(f'🔍 WordPress API:')
        print(f'   Yoast title в head: {yoast_title}')
        
        # Ищем наши данные
        if 'AI Lynx' in yoast_head and 'ML новости' in yoast_head:
            print('✅ УСПЕХ! Наши данные найдены в Yoast head!')
            return True
        else:
            print('❌ Наши данные пока не в Yoast head')
            
            # Проверяем raw head
            if '<title>' in yoast_head:
                current_title = yoast_head.split('<title>')[1].split('</title>')[0]
                print(f'   Текущий title: {current_title}')
    
    # Проверяем мета-поля напрямую
    print(f'\n🔍 Проверяем мета-поля...')
    meta_response = requests.get(f'{config.wordpress_api_url}/categories/{category_id}?_fields=meta', auth=auth)
    if meta_response.status_code == 200:
        meta_data = meta_response.json()
        meta = meta_data.get('meta', {})
        
        yoast_fields = {k: v for k, v in meta.items() if '_yoast_wpseo_' in k}
        if yoast_fields:
            print('✅ Yoast мета-поля найдены:')
            for field, value in yoast_fields.items():
                if value:
                    print(f'   {field}: {value[:50]}...')
        else:
            print('❌ Yoast мета-поля не найдены')
    
    return False


def main():
    print('🗄️  Обновление через БД плагин (по одной)')
    print('=' * 60)
    
    if update_categories_one_by_one():
        print('\n⏳ Ждем обновления системы (3 секунды)...')
        time.sleep(3)
        
        success = check_one_category_result()
        
        if success:
            print('\n🎉 Отлично! Данные обновились в Yoast!')
        else:
            print('\n⏳ Данные сохранены, но пока не отображаются в Yoast head')
            print('\n💡 Рекомендуемые действия:')
            print('1. Админка Yoast: https://ailynx.ru/wp-admin/admin.php?page=wpseo_tools')
            print('2. Найдите "SEO Data" и нажмите "Reindex"')
            print('3. Или попробуйте вручную сохранить одну категорию в админке')
        
    else:
        print('\n❌ Произошла ошибка при обновлении')


if __name__ == "__main__":
    main()