#!/usr/bin/env python3
"""
Get SEO Data for Manual Entry
Получение SEO данных для ручного ввода в админку WordPress
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config

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


def get_category_urls():
    """Получение URL категорий для редактирования"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    # Получаем все категории
    response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
    if response.status_code != 200:
        print('❌ Не удалось получить категории')
        return {}
    
    categories = response.json()
    category_map = {}
    
    for cat in categories:
        name = cat['name']
        cat_id = cat['id']
        if name in CATEGORY_SEO_DATA:
            category_map[name] = {
                'id': cat_id,
                'edit_url': f'https://ailynx.ru/wp-admin/term.php?taxonomy=category&tag_ID={cat_id}&post_type=post'
            }
    
    return category_map


def main():
    print('📋 SEO данные для ручного ввода в WordPress')
    print('=' * 60)
    
    # Получаем URLs категорий
    categories = get_category_urls()
    
    if not categories:
        print('❌ Не удалось получить данные категорий')
        return
    
    print('💡 Инструкция:')
    print('1. Скопируйте данные для каждой категории')
    print('2. Перейдите по ссылке на редактирование')
    print('3. Найдите секцию "Yoast SEO" внизу страницы')
    print('4. Вставьте данные в соответствующие поля')
    print('5. Нажмите "Обновить"')
    print()
    
    for cat_name, cat_info in categories.items():
        if cat_name in CATEGORY_SEO_DATA:
            seo_data = CATEGORY_SEO_DATA[cat_name]
            
            print(f'📂 КАТЕГОРИЯ: {cat_name}')
            print(f'🔗 URL: {cat_info["edit_url"]}')
            print()
            print('📝 SEO ЗАГОЛОВОК:')
            print(seo_data['title'])
            print()
            print('📄 МЕТА-ОПИСАНИЕ:')
            print(seo_data['desc'])
            print()
            print('🔑 КЛЮЧЕВОЕ СЛОВО:')
            print(seo_data['keyword'])
            print()
            print('─' * 60)
            print()
    
    print('🎯 БЫСТРЫЙ СПОСОБ:')
    print('Можете открыть все ссылки в отдельных вкладках и заполнять поочередно')
    print()
    
    # Выводим все ссылки для быстрого открытия
    print('🔗 Все ссылки для копирования:')
    for cat_name, cat_info in categories.items():
        if cat_name in CATEGORY_SEO_DATA:
            print(f'{cat_name}: {cat_info["edit_url"]}')
    
    print()
    print('✅ После заполнения всех категорий проверьте результат на фронтенде!')


if __name__ == "__main__":
    main()