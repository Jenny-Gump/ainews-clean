# Yoast SEO API - Примеры кода

Практические примеры работы с Yoast SEO через расширенный WordPress REST API.

## Базовая настройка

```python
import requests
from requests.auth import HTTPBasicAuth
import time
import json

# Конфигурация
API_BASE = "https://ailynx.ru/wp-json/wp/v2"
AUTH = HTTPBasicAuth('admin', 'tE85 PFT4 Ghq9 nl26 nQlt gBnG')

def make_request(method, endpoint, data=None):
    """Базовая функция для API запросов"""
    url = f"{API_BASE}{endpoint}"
    
    if method == 'GET':
        response = requests.get(url, auth=AUTH)
    elif method == 'POST':
        response = requests.post(url, json=data, auth=AUTH)
    
    return response
```

## 1. Проверка доступности Yoast полей

```python
def check_yoast_fields_available():
    """Проверяет доступны ли Yoast поля в API"""
    response = make_request('GET', '/categories/4')
    
    if response.status_code == 200:
        data = response.json()
        yoast_fields = ['yoast_title', 'yoast_description', 'yoast_keyword']
        
        available_fields = []
        for field in yoast_fields:
            if field in data:
                available_fields.append(field)
                print(f"✅ {field}: доступно")
            else:
                print(f"❌ {field}: недоступно")
        
        return len(available_fields) == len(yoast_fields)
    
    print(f"❌ Ошибка API: {response.status_code}")
    return False

# Использование
if check_yoast_fields_available():
    print("🎉 Yoast REST API Extension работает!")
else:
    print("⚠️ Установите плагин yoast-rest-api-extension.php")
```

## 2. Получение всех категорий с Yoast данными

```python
def get_all_categories_with_yoast():
    """Получает все категории с Yoast SEO данными"""
    response = make_request('GET', '/categories?per_page=100')
    
    if response.status_code != 200:
        print(f"❌ Ошибка получения категорий: {response.status_code}")
        return []
    
    categories = response.json()
    categories_with_yoast = []
    
    for category in categories:
        yoast_data = {
            'id': category['id'],
            'name': category['name'],
            'slug': category['slug'],
            'yoast_title': category.get('yoast_title', ''),
            'yoast_description': category.get('yoast_description', ''),
            'yoast_keyword': category.get('yoast_keyword', ''),
            'has_yoast_data': bool(
                category.get('yoast_title') or 
                category.get('yoast_description') or 
                category.get('yoast_keyword')
            )
        }
        categories_with_yoast.append(yoast_data)
    
    return categories_with_yoast

# Использование
categories = get_all_categories_with_yoast()
for cat in categories:
    status = "✅" if cat['has_yoast_data'] else "❌"
    print(f"{status} {cat['name']}: {len(cat['yoast_title'])} chars title")
```

## 3. Обновление отдельной категории

```python
def update_category_yoast(category_id, title, description, keyword):
    """Обновляет Yoast SEO поля одной категории"""
    
    # Валидация входных данных
    if len(title) > 60:
        print(f"⚠️ Заголовок слишком длинный: {len(title)} символов")
    
    if len(description) > 160:
        print(f"⚠️ Описание слишком длинное: {len(description)} символов")
    
    # Данные для обновления
    yoast_data = {
        'yoast_title': title,
        'yoast_description': description,
        'yoast_keyword': keyword
    }
    
    # Отправка запроса
    response = make_request('POST', f'/categories/{category_id}', yoast_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Категория {category_id} обновлена:")
        print(f"   Title: {result.get('yoast_title', 'НЕТ')}")
        print(f"   Description: {len(result.get('yoast_description', ''))} символов")
        print(f"   Keyword: {result.get('yoast_keyword', 'НЕТ')}")
        return True
    else:
        print(f"❌ Ошибка обновления: {response.status_code}")
        print(f"   Ответ: {response.text[:200]}")
        return False

# Пример использования
success = update_category_yoast(
    category_id=4,
    title="Машинное обучение: новости ML и AI | AI Lynx",
    description="Актуальные новости машинного обучения: алгоритмы, нейросети, deep learning. Практические применения ML в бизнесе.",
    keyword="машинное обучение"
)
```

## 4. Массовое обновление с обработкой ошибок

```python
def bulk_update_categories_yoast(categories_data, delay=0.5):
    """
    Массовое обновление категорий с обработкой ошибок
    
    categories_data: словарь {category_id: {yoast_data}}
    delay: пауза между запросами в секундах
    """
    
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }
    
    total = len(categories_data)
    
    for i, (cat_id, yoast_data) in enumerate(categories_data.items(), 1):
        print(f"\n[{i}/{total}] Обновляем категорию {cat_id}...")
        
        try:
            # Проверяем обязательные поля
            if not yoast_data.get('yoast_title'):
                print(f"⚠️ Пропускаем {cat_id}: нет заголовка")
                results['skipped'].append(cat_id)
                continue
            
            # Отправляем запрос
            response = make_request('POST', f'/categories/{cat_id}', yoast_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Успешно: {result.get('name', '')[:40]}...")
                results['success'].append({
                    'id': cat_id,
                    'name': result.get('name', ''),
                    'yoast_title': result.get('yoast_title', '')
                })
            else:
                print(f"❌ Ошибка {response.status_code}")
                results['failed'].append({
                    'id': cat_id,
                    'error': response.status_code,
                    'message': response.text[:100]
                })
            
            # Пауза между запросами
            if delay > 0:
                time.sleep(delay)
                
        except Exception as e:
            print(f"❌ Исключение для {cat_id}: {e}")
            results['failed'].append({
                'id': cat_id,
                'error': 'exception',
                'message': str(e)
            })
    
    # Выводим итоговую статистику
    print(f"\n📊 Результаты массового обновления:")
    print(f"   ✅ Успешно: {len(results['success'])}")
    print(f"   ❌ Ошибки: {len(results['failed'])}")
    print(f"   ⚠️ Пропущено: {len(results['skipped'])}")
    
    return results

# Пример использования
categories_seo_data = {
    3: {
        'yoast_title': 'LLM новости: большие языковые модели | AI Lynx',
        'yoast_description': 'Новости LLM: GPT, Claude, Gemini. Обзоры больших языковых моделей.',
        'yoast_keyword': 'LLM новости'
    },
    4: {
        'yoast_title': 'Машинное обучение: новости ML | AI Lynx',
        'yoast_description': 'Новости машинного обучения и нейронных сетей. Алгоритмы и практика.',
        'yoast_keyword': 'машинное обучение'
    }
}

results = bulk_update_categories_yoast(categories_seo_data)
```

## 5. Валидация SEO данных

```python
def validate_seo_data(title, description, keyword):
    """Валидация SEO данных по лучшим практикам"""
    
    issues = []
    warnings = []
    
    # Проверка заголовка
    if not title:
        issues.append("Отсутствует SEO заголовок")
    elif len(title) < 30:
        warnings.append(f"Заголовок короткий: {len(title)} символов (рекомендуется 30-60)")
    elif len(title) > 60:
        warnings.append(f"Заголовок длинный: {len(title)} символов (рекомендуется 30-60)")
    
    # Проверка описания
    if not description:
        issues.append("Отсутствует мета-описание")
    elif len(description) < 120:
        warnings.append(f"Описание короткое: {len(description)} символов (рекомендуется 120-160)")
    elif len(description) > 160:
        warnings.append(f"Описание длинное: {len(description)} символов (рекомендуется 120-160)")
    
    # Проверка ключевого слова
    if not keyword:
        warnings.append("Отсутствует фокусное ключевое слово")
    elif len(keyword.split()) > 3:
        warnings.append(f"Ключевое слово слишком длинное: {len(keyword.split())} слов")
    
    # Проверка соответствия ключевого слова
    if keyword and title:
        if keyword.lower() not in title.lower():
            warnings.append("Ключевое слово не найдено в заголовке")
    
    if keyword and description:
        if keyword.lower() not in description.lower():
            warnings.append("Ключевое слово не найдено в описании")
    
    return {
        'is_valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'seo_score': max(0, 100 - len(issues) * 30 - len(warnings) * 10)
    }

# Пример использования
validation = validate_seo_data(
    title="Машинное обучение: новости ML | AI Lynx",
    description="Актуальные новости машинного обучения и нейронных сетей.",
    keyword="машинное обучение"
)

print(f"SEO Score: {validation['seo_score']}/100")
for issue in validation['issues']:
    print(f"❌ {issue}")
for warning in validation['warnings']:
    print(f"⚠️ {warning}")
```

## 6. Создание SEO отчета

```python
def generate_seo_report():
    """Создает отчет по SEO оптимизации всех категорий"""
    
    categories = get_all_categories_with_yoast()
    
    report = {
        'total_categories': len(categories),
        'with_yoast_data': 0,
        'without_yoast_data': 0,
        'seo_scores': [],
        'issues': [],
        'recommendations': []
    }
    
    for category in categories:
        # Валидация каждой категории
        validation = validate_seo_data(
            category['yoast_title'],
            category['yoast_description'],
            category['yoast_keyword']
        )
        
        if category['has_yoast_data']:
            report['with_yoast_data'] += 1
        else:
            report['without_yoast_data'] += 1
        
        report['seo_scores'].append({
            'name': category['name'],
            'score': validation['seo_score'],
            'issues': validation['issues'],
            'warnings': validation['warnings']
        })
        
        # Собираем общие проблемы
        report['issues'].extend(validation['issues'])
    
    # Среднее значение SEO score
    if report['seo_scores']:
        avg_score = sum(item['score'] for item in report['seo_scores']) / len(report['seo_scores'])
        report['average_seo_score'] = round(avg_score, 1)
    
    # Рекомендации
    if report['without_yoast_data'] > 0:
        report['recommendations'].append(f"Добавить SEO данные для {report['without_yoast_data']} категорий")
    
    if report['average_seo_score'] < 80:
        report['recommendations'].append("Улучшить качество SEO данных")
    
    return report

# Использование
report = generate_seo_report()

print("📊 SEO Отчет")
print("=" * 50)
print(f"Всего категорий: {report['total_categories']}")
print(f"С SEO данными: {report['with_yoast_data']}")
print(f"Без SEO данных: {report['without_yoast_data']}")
print(f"Средний SEO Score: {report.get('average_seo_score', 0)}/100")

print("\n🔍 Детали по категориям:")
for item in report['seo_scores'][:5]:  # Показываем первые 5
    print(f"  {item['name'][:30]:<30} Score: {item['score']}/100")

print(f"\n💡 Рекомендации:")
for rec in report['recommendations']:
    print(f"  • {rec}")
```

## 7. Резервное копирование и восстановление

```python
def backup_yoast_data():
    """Создает резервную копию всех Yoast SEO данных"""
    
    categories = get_all_categories_with_yoast()
    
    backup_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_categories': len(categories),
        'categories': {}
    }
    
    for category in categories:
        if category['has_yoast_data']:
            backup_data['categories'][category['id']] = {
                'name': category['name'],
                'slug': category['slug'],
                'yoast_title': category['yoast_title'],
                'yoast_description': category['yoast_description'],
                'yoast_keyword': category['yoast_keyword']
            }
    
    # Сохраняем в файл
    filename = f"yoast_backup_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Резервная копия сохранена: {filename}")
    print(f"📊 Категорий с SEO данными: {len(backup_data['categories'])}")
    
    return filename

def restore_yoast_data(backup_file):
    """Восстанавливает Yoast SEO данные из резервной копии"""
    
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Файл {backup_file} не найден")
        return False
    
    categories_to_restore = backup_data.get('categories', {})
    
    print(f"🔄 Восстановление из {backup_file}")
    print(f"📊 Категорий к восстановлению: {len(categories_to_restore)}")
    
    # Преобразуем в формат для массового обновления
    restore_data = {}
    for cat_id, cat_data in categories_to_restore.items():
        restore_data[int(cat_id)] = {
            'yoast_title': cat_data['yoast_title'],
            'yoast_description': cat_data['yoast_description'],
            'yoast_keyword': cat_data['yoast_keyword']
        }
    
    # Выполняем восстановление
    results = bulk_update_categories_yoast(restore_data, delay=0.3)
    
    return len(results['success']) > 0

# Использование
backup_file = backup_yoast_data()
# restore_yoast_data(backup_file)  # При необходимости
```

## Заключение

Эти примеры покрывают основные сценарии работы с Yoast SEO через расширенный WordPress REST API:

- ✅ Проверка доступности полей
- ✅ Массовое обновление с обработкой ошибок  
- ✅ Валидация SEO данных
- ✅ Создание отчетов
- ✅ Резервное копирование

Используйте эти примеры как основу для автоматизации SEO процессов в системе AI News Parser.