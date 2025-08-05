#!/usr/bin/env python3
"""
Mass Update Categories via Database Plugin
Массовое обновление всех категорий через плагин прямого доступа к БД
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


def mass_update_via_db():
    """Массовое обновление через БД плагин"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🗄️  Массовое обновление через прямой доступ к БД')
    print('=' * 60)
    
    # Получаем все категории
    categories_response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
    if categories_response.status_code != 200:
        print('❌ Не удалось получить список категорий')
        return False
    
    categories = categories_response.json()
    category_map = {cat['name']: cat['id'] for cat in categories}
    
    print(f'📂 Найдено категорий: {len(categories)}')
    
    # Подготавливаем данные для массового обновления
    bulk_data = []
    for cat_name, seo_data in CATEGORY_SEO_DATA.items():
        if cat_name in category_map:
            bulk_data.append({
                'category_id': category_map[cat_name],
                'title': seo_data['title'],
                'desc': seo_data['desc'],
                'keyword': seo_data['keyword']
            })
            print(f'✓ {cat_name} (ID: {category_map[cat_name]})')
        else:
            print(f'❌ {cat_name} не найдена')
    
    if not bulk_data:
        print('❌ Нет данных для обновления')
        return False
    
    print(f'\n🚀 Запускаем массовое обновление {len(bulk_data)} категорий...')
    
    # Отправляем массовое обновление
    response = requests.post(
        'https://ailynx.ru/wp-json/yoast-db/v1/bulk-update',
        json=bulk_data,
        auth=auth
    )
    
    if response.status_code == 200:
        result = response.json()
        print('✅ Массовое обновление успешно!')
        print(f'📊 Обработано: {result.get("processed", 0)} категорий')
        
        # Показываем результаты
        results = result.get('results', [])
        success_count = 0
        
        for res in results:
            if res.get('success'):
                print(f'  ✅ {res.get("category_id")}: {res.get("results", {})}')
                success_count += 1
            else:
                print(f'  ❌ {res.get("category_id")}: Ошибка')
        
        print(f'\n📈 Итого успешно: {success_count}/{len(bulk_data)}')
        return success_count > 0
    else:
        print(f'❌ Ошибка массового обновления: {response.status_code}')
        print(f'   Ответ: {response.text[:200]}...')
        return False


def verify_db_results():
    """Проверка результатов через БД"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔍 Проверяем результаты через БД...')
    
    # Проверяем структуру БД
    check_response = requests.get('https://ailynx.ru/wp-json/yoast-db/v1/check-tables', auth=auth)
    if check_response.status_code == 200:
        data = check_response.json()
        yoast_tables = data.get('yoast_tables', {})
        
        print(f'📊 Yoast indexable записей: {yoast_tables.get("yoast_indexable_count", 0)}')
        print(f'📋 Termmeta записей с Yoast: {len(data.get("termmeta_yoast", []))}')
        
        # Проверяем конкретные категории
        test_categories = ['Машинное обучение', 'LLM', 'Техника']
        categories_response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
        
        if categories_response.status_code == 200:
            categories = categories_response.json()
            category_map = {cat['name']: cat['id'] for cat in categories}
            
            found_updates = 0
            
            for cat_name in test_categories:
                if cat_name not in category_map:
                    continue
                    
                cat_id = category_map[cat_name]
                
                # Проверяем через WordPress API
                wp_response = requests.get(f'{config.wordpress_api_url}/categories/{cat_id}', auth=auth)
                if wp_response.status_code == 200:
                    wp_data = wp_response.json()
                    yoast_head = wp_data.get('yoast_head', '')
                    yoast_title = wp_data.get('yoast_head_json', {}).get('title', '')
                    
                    print(f'\n📂 {cat_name}:')
                    
                    # Ищем наши данные в head
                    if 'AI Lynx' in yoast_head and ('ML новости' in yoast_head or 'LLM' in yoast_head or 'AI Техника' in yoast_head):
                        print(f'  ✅ Yoast head обновился: {yoast_title}')
                        found_updates += 1
                    else:
                        print(f'  ❌ Yoast head: {yoast_title}')
                        
                        # Проверяем мета-поля напрямую
                        meta_response = requests.get(f'{config.wordpress_api_url}/categories/{cat_id}?_fields=meta', auth=auth)
                        if meta_response.status_code == 200:
                            meta_data = meta_response.json()
                            meta = meta_data.get('meta', {})
                            if any('AI Lynx' in str(v) for v in meta.values()):
                                print(f'  ℹ️ Данные в мета-полях найдены')
                            else:
                                print(f'  ⚠️ Данные в мета-полях не найдены')
            
            if found_updates > 0:
                print(f'\n🎉 Найдено {found_updates} успешных обновлений в Yoast head!')
            else:
                print(f'\n⏳ Обновления пока не отражаются в Yoast head')
                print('💡 Возможно, нужно:')
                print('  1. Подождать обновления кэша Yoast')
                print('  2. Перестроить indexables в админке Yoast')
                print('  3. Проверить настройки Yoast SEO')
    else:
        print('❌ Не удалось проверить таблицы БД')


def main():
    print('🗄️  Массовое обновление Yoast через прямой доступ к БД')
    print('=' * 60)
    
    if mass_update_via_db():
        print('\n⏳ Ждем обновления системы (3 секунды)...')
        time.sleep(3)
        
        verify_db_results()
        
        print('\n✅ Массовое обновление через БД завершено!')
        print('\n💡 Если изменения не видны в Yoast head:')
        print('1. Зайдите в админку: https://ailynx.ru/wp-admin/admin.php?page=wpseo_tools')
        print('2. Найдите "SEO Data" → "Reindex"')
        print('3. Нажмите "Reindex" для принудительного обновления')
        print('4. Проверьте любую категорию: https://ailynx.ru/wp-admin/edit-tags.php?taxonomy=category')
        
    else:
        print('\n❌ Произошла ошибка при массовом обновлении')
        print('💡 Попробуйте ручной ввод или плагин V2')


if __name__ == "__main__":
    main()