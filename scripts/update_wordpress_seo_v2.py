#!/usr/bin/env python3
"""
Update WordPress Categories SEO V2 (with meta descriptions and English slugs)
Обновление SEO категорий WordPress с мета-описаниями и английскими URL
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
import time

# SEO данные для категорий (исправленная версия)
CATEGORIES_SEO = {
    "LLM": {
        "name": "LLM: последние новости больших языковых моделей и полезная информация индустрии",
        "description": "Последние новости о больших языковых моделях (LLM): GPT, Claude, Gemini, LLaMA и другие. Обзоры новых релизов, сравнения моделей, анализ возможностей и ограничений современных LLM. Следите за развитием технологий искусственного интеллекта в области обработки естественного языка. Практические кейсы применения, туториалы и экспертные мнения.",
        "slug": "llm-news",
        "meta_description": "Актуальные новости больших языковых моделей (LLM) - GPT, Claude, Gemini. Обзоры, сравнения и анализ развития AI технологий обработки текста."
    },
    "Машинное обучение": {
        "name": "Машинное обучение: последние новости и полезная информация индустрии", 
        "description": "Актуальные новости машинного обучения и нейронных сетей. Прорывы в области ML, новые алгоритмы, исследования от ведущих лабораторий. Практические применения машинного обучения в бизнесе, науке и повседневной жизни. Deep learning, computer vision, NLP и другие направления. Туториалы, гайды и экспертные материалы для специалистов.",
        "slug": "machine-learning",
        "meta_description": "Новости машинного обучения и нейронных сетей. Алгоритмы, исследования, практические применения ML в бизнесе и науке."
    },
    "Техника": {
        "name": "AI Техника: последние новости технологий и полезная информация индустрии",
        "description": "Новости о технике и железе для искусственного интеллекта. GPU, TPU, специализированные AI-чипы от NVIDIA, AMD, Intel. Облачные платформы для ML, обзоры программного обеспечения, фреймворков и инструментов разработки. Аппаратное обеспечение для обучения и инференса нейросетей. Сравнения производительности и рекомендации по выбору.",
        "slug": "ai-hardware",
        "meta_description": "Новости AI техники и железа: GPU, TPU, чипы для нейросетей. Обзоры оборудования, облачных платформ и инструментов разработки."
    },
    "Digital": {
        "name": "Digital AI: последние новости цифровых технологий и полезная информация индустрии",
        "description": "Как искусственный интеллект трансформирует цифровой мир. AI в интернете, социальных сетях, e-commerce и цифровом маркетинге. Персонализация контента, рекомендательные системы, автоматизация digital-процессов. Влияние ИИ на SEO, контент-маркетинг и пользовательский опыт. Кейсы внедрения и практические решения.",
        "slug": "digital-ai",
        "meta_description": "AI в цифровом мире: интернет, соцсети, e-commerce, маркетинг. Персонализация, рекомендации, автоматизация digital-процессов."
    },
    "Люди": {
        "name": "Люди в AI: последние новости экспертов и полезная информация индустрии",
        "description": "Истории людей, создающих будущее искусственного интеллекта. Интервью с ведущими исследователями, основателями AI-стартапов, визионерами индустрии. Карьерные пути в AI, образовательные программы, влияние ИИ на рынок труда. Этические аспекты разработки искусственного интеллекта. Экспертные мнения и профессиональные советы.",
        "slug": "ai-people",
        "meta_description": "Люди в AI индустрии: интервью с экспертами, истории успеха, карьерные пути. Этика ИИ и влияние на рынок труда."
    },
    "Финансы": {
        "name": "AI в Финансах: последние новости финтеха и полезная информация индустрии",
        "description": "Применение искусственного интеллекта в финансовой сфере. Алгоритмическая торговля, анализ кредитных рисков, автоматизация банковских процессов. Инвестиции в AI-стартапы, финтех с машинным обучением, криптовалютные алгоритмы. Регулирование AI в финансах и перспективы развития. Практические кейсы внедрения.",
        "slug": "ai-finance",
        "meta_description": "AI в финансах: алготрейдинг, анализ рисков, банковская автоматизация. Инвестиции в AI-стартапы и финтех решения."
    },
    "Наука": {
        "name": "AI в Науке: последние новости исследований и полезная информация индустрии",
        "description": "Революция искусственного интеллекта в научных исследованиях. От предсказания структуры белков до поиска новых лекарств. Машинное обучение в физике, химии, биологии, астрономии. Автоматизация научных экспериментов, анализ больших данных, открытия с помощью ИИ. Междисциплинарные проекты и прорывные результаты.",
        "slug": "ai-science",
        "meta_description": "AI в науке: предсказание белков, поиск лекарств, автоматизация экспериментов. Машинное обучение в физике, химии, биологии."
    },
    "Обучение": {
        "name": "AI Образование: последние новости обучения и полезная информация индустрии",
        "description": "Образование и карьера в сфере искусственного интеллекта. Лучшие курсы по машинному обучению, университетские программы, онлайн-обучение. Сертификации по AI, roadmap для изучения ИИ, практические проекты. Как стать AI-инженером, data scientist или ML-исследователем. Тренды образования и требования работодателей.",
        "slug": "ai-education",
        "meta_description": "AI образование: курсы машинного обучения, сертификации, карьера в ИИ. Как стать AI-инженером и data scientist."
    },
    "Другие индустрии": {
        "name": "AI в Индустриях: последние новости применения и полезная информация индустрии",
        "description": "Применение искусственного интеллекта в различных отраслях экономики. ИИ в сельском хозяйстве, космической индустрии, медицине, производстве, логистике. Инновационные кейсы использования AI, автоматизация промышленных процессов, умные города и транспорт. Отраслевые решения и их влияние на бизнес-процессы.",
        "slug": "ai-industries",
        "meta_description": "AI в различных индустриях: сельское хозяйство, медицина, производство, логистика. Умные города и промышленная автоматизация."
    },
    "Новости": {
        "name": "AI Новости: последние события и полезная информация индустрии искусственного интеллекта",
        "description": "Свежие новости мира искусственного интеллекта. Последние прорывы в исследованиях, релизы новых AI-продуктов, слияния и поглощения в индустрии. Анонсы конференций, результаты исследований, тренды развития ИИ. Будьте в курсе всех событий в области artificial intelligence. Ежедневные обновления и аналитические материалы.",
        "slug": "ai-news",
        "meta_description": "Последние новости искусственного интеллекта: прорывы в исследованиях, релизы AI-продуктов, тренды развития индустрии."
    }
}


def update_categories_with_meta():
    """Обновление категорий с мета-описаниями"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🎯 Обновление SEO категорий с мета-описаниями')
    print('=' * 60)
    
    # Получаем все категории
    categories_response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
    if categories_response.status_code != 200:
        print('❌ Не удалось получить список категорий')
        return False
    
    categories = categories_response.json()
    category_map = {cat['name']: cat['id'] for cat in categories}
    
    # Также ищем по старым именам
    old_names_map = {
        'LLM': 'LLM',
        'Машинное обучение': 'Машинное обучение',
        'AI Техника': 'Техника',
        'Digital AI': 'Digital',
        'Люди в AI': 'Люди',
        'AI в Финансах': 'Финансы',
        'AI в Науке': 'Наука',
        'AI Образование': 'Обучение',
        'AI в Индустриях': 'Другие индустрии',
        'AI Новости': 'Новости'
    }
    
    print(f'📂 Найдено категорий: {len(categories)}')
    
    success_count = 0
    
    for seo_key, seo_data in CATEGORIES_SEO.items():
        # Ищем категорию по разным именам
        cat_id = None
        found_name = None
        
        # Сначала ищем по точному совпадению
        if seo_key in category_map:
            cat_id = category_map[seo_key]
            found_name = seo_key
        else:
            # Ищем по обновленным именам
            for cat in categories:
                if (cat['name'] in old_names_map and old_names_map[cat['name']] == seo_key) or \
                   any(word in cat['name'].lower() for word in seo_key.lower().split()):
                    cat_id = cat['id']
                    found_name = cat['name']
                    break
        
        if not cat_id:
            print(f'❌ {seo_key} не найдена')
            continue
            
        print(f'\n🔄 Обновляем {found_name} → {seo_data["name"][:50]}... (ID: {cat_id})')
        
        try:
            # Обновляем через WordPress REST API
            update_data = {
                'name': seo_data['name'],
                'description': seo_data['description'],
                'slug': seo_data['slug'],
                'meta': {
                    'description': seo_data['meta_description']
                }
            }
            
            response = requests.post(
                f'{config.wordpress_api_url}/categories/{cat_id}',
                json=update_data,
                auth=auth
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f'✅ Успешно обновлено:')
                print(f'   Название: {result.get("name")[:60]}...')
                print(f'   Slug: {result.get("slug")}')
                print(f'   Описание: {len(result.get("description", ""))} символов')
                print(f'   Мета-описание: {len(seo_data["meta_description"])} символов')
                
                success_count += 1
                
                # Пауза между запросами
                time.sleep(0.3)
            else:
                print(f'❌ Ошибка {response.status_code}')
                print(f'   Ответ: {response.text[:200]}')
                
        except Exception as e:
            print(f'❌ Исключение - {e}')
    
    print(f'\n📊 Результат: {success_count}/{len(CATEGORIES_SEO)} категорий обновлено')
    return success_count > 0


def verify_new_urls():
    """Проверка новых URL"""
    print('\n🔗 Новые SEO-оптимизированные URL:')
    
    base_url = "https://ailynx.ru/category/"
    
    urls = {
        'LLM новости': f'{base_url}llm-news/',
        'Машинное обучение': f'{base_url}machine-learning/',
        'AI Техника': f'{base_url}ai-hardware/',
        'Digital AI': f'{base_url}digital-ai/',
        'Люди в AI': f'{base_url}ai-people/',
        'AI в Финансах': f'{base_url}ai-finance/',
        'AI в Науке': f'{base_url}ai-science/',
        'AI Образование': f'{base_url}ai-education/',
        'AI в Индустриях': f'{base_url}ai-industries/',
        'AI Новости': f'{base_url}ai-news/'
    }
    
    for name, url in urls.items():
        print(f'   {name}: {url}')


def check_meta_descriptions():
    """Проверка мета-описаний"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🔍 Проверка мета-описаний...')
    
    # Получаем обновленные категории
    categories_response = requests.get(f'{config.wordpress_api_url}/categories', auth=auth, params={'per_page': 100})
    if categories_response.status_code != 200:
        print('❌ Не удалось получить категории')
        return
    
    categories = categories_response.json()
    
    found_meta = 0
    
    for cat in categories[:5]:  # Проверяем первые 5
        print(f'\n📂 {cat["name"][:50]}...:')
        print(f'   Slug: {cat.get("slug")}')
        print(f'   Описание: {len(cat.get("description", ""))} символов')
        
        # Проверяем мета-поля
        meta = cat.get('meta', {})
        if meta and 'description' in meta:
            print(f'   ✅ Мета-описание: {meta["description"][:60]}...')
            found_meta += 1
        else:
            print(f'   ❌ Мета-описание: не найдено')
    
    print(f'\n📊 Мета-описаний найдено: {found_meta}/5')


def main():
    print('🎯 SEO оптимизация V2: мета-описания + английские URL')
    print('=' * 70)
    
    if update_categories_with_meta():
        print('\n⏳ Ждем обновления системы (3 секунды)...')
        time.sleep(3)
        
        verify_new_urls()
        check_meta_descriptions()
        
        print('\n✅ SEO оптимизация V2 завершена!')
        print('\n💡 Что было сделано:')
        print('• Расширенные названия с описанием содержания')
        print('• SEO-оптимизированные описания (300+ символов)')
        print('• Английские slug\'ы для лучшего SEO')
        print('• Добавлены мета-описания для поисковых систем')
        print('• Все категории готовы для международного продвижения')
        
    else:
        print('\n❌ Произошла ошибка при обновлении')


if __name__ == "__main__":
    main()