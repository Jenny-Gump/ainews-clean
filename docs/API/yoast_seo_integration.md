# Yoast SEO Integration API

Руководство по работе с Yoast SEO полями через WordPress REST API в системе AI News Parser.

## Обзор

Yoast SEO по умолчанию НЕ предоставляет возможность изменения SEO полей через WordPress REST API. Для решения этой проблемы создан плагин **Yoast REST API Extension**, который расширяет стандартный WordPress REST API.

## Установка

### 1. Плагин Yoast REST API Extension

```bash
# Файл находится в:
/wordpress-plugin/yoast-rest-api-extension.zip

# Установка:
1. Загрузить ZIP в WordPress админку
2. Активировать плагин
3. Убедиться что Yoast SEO активен
```

### 2. Проверка установки

```python
# Скрипт для проверки
python scripts/test_yoast_rest_extension.py
```

## API Endpoints

### Категории с Yoast полями

После установки плагина стандартные endpoints категорий расширяются:

```
GET  /wp-json/wp/v2/categories/{id}
POST /wp-json/wp/v2/categories/{id}
```

#### Новые поля:

| Поле | Тип | Описание | Yoast Meta Key |
|------|-----|----------|----------------|
| `yoast_title` | string | SEO заголовок | `_yoast_wpseo_title` |
| `yoast_description` | string | Мета-описание | `_yoast_wpseo_metadesc` |
| `yoast_keyword` | string | Ключевое слово | `_yoast_wpseo_focuskw` |
| `yoast_canonical` | string | Канонический URL | `_yoast_wpseo_canonical` |

## Примеры использования

### Получение категории с Yoast полями

```python
import requests
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth('username', 'app_password')
response = requests.get(
    'https://ailynx.ru/wp-json/wp/v2/categories/4',
    auth=auth
)

data = response.json()
print(f"SEO Title: {data.get('yoast_title')}")
print(f"Meta Description: {data.get('yoast_description')}")
print(f"Focus Keyword: {data.get('yoast_keyword')}")
```

### Обновление Yoast SEO полей

```python
seo_data = {
    'yoast_title': 'Машинное обучение: новости ML | AI Lynx',
    'yoast_description': 'Актуальные новости машинного обучения, алгоритмы, нейросети. Практические применения ML в бизнесе и науке.',
    'yoast_keyword': 'машинное обучение'
}

response = requests.post(
    'https://ailynx.ru/wp-json/wp/v2/categories/4',
    json=seo_data,
    auth=auth
)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Обновлено: {result.get('yoast_title')}")
```

### Массовое обновление

```python
# Данные для всех категорий
CATEGORIES_SEO = {
    3: {  # LLM
        'yoast_title': 'LLM новости: большие языковые модели | AI Lynx',
        'yoast_description': 'Новости LLM: GPT, Claude, Gemini. Обзоры и анализ больших языковых моделей.',
        'yoast_keyword': 'LLM новости'
    },
    4: {  # Машинное обучение
        'yoast_title': 'Машинное обучение: новости ML | AI Lynx',
        'yoast_description': 'Новости машинного обучения, алгоритмы, нейросети, практические применения.',
        'yoast_keyword': 'машинное обучение'
    }
    # ... остальные категории
}

# Обновление всех категорий
for cat_id, seo_data in CATEGORIES_SEO.items():
    response = requests.post(
        f'https://ailynx.ru/wp-json/wp/v2/categories/{cat_id}',
        json=seo_data,
        auth=auth
    )
    print(f"Категория {cat_id}: {response.status_code}")
```

## Техническая реализация

### Регистрация полей в REST API

Плагин использует `register_rest_field()` для расширения API:

```php
register_rest_field('category', 'yoast_title', array(
    'get_callback' => 'get_category_yoast_title',
    'update_callback' => 'update_category_yoast_title',
    'schema' => array(
        'type' => 'string',
        'description' => 'Yoast SEO Title for category'
    ),
));
```

### Callback функции

```php
public function get_category_yoast_title($term) {
    return get_term_meta($term['id'], '_yoast_wpseo_title', true);
}

public function update_category_yoast_title($value, $term) {
    if (!current_user_can('manage_categories')) {
        return false;
    }
    return update_term_meta($term->term_id, '_yoast_wpseo_title', sanitize_text_field($value));
}
```

## Готовые скрипты

### 1. Тестирование плагина
```bash
python scripts/test_yoast_rest_extension.py
```

### 2. Массовое обновление
```bash
python scripts/update_all_categories_yoast.py
```

### 3. Проверка результатов
```bash
python scripts/check_yoast_seo_results.py
```

## Структура мета-полей Yoast

### Основные поля категорий

| Meta Key | Описание | Тип данных |
|----------|----------|------------|
| `_yoast_wpseo_title` | SEO заголовок | string |
| `_yoast_wpseo_metadesc` | Мета-описание | string |
| `_yoast_wpseo_focuskw` | Ключевое слово | string |
| `_yoast_wpseo_canonical` | Канонический URL | string |
| `_yoast_wpseo_noindex` | No-index флаг | string |
| `_yoast_wpseo_bctitle` | Breadcrumb title | string |

### Дополнительные поля (для постов)

| Meta Key | Описание |
|----------|----------|
| `_yoast_wpseo_opengraph-title` | Open Graph заголовок |
| `_yoast_wpseo_opengraph-description` | Open Graph описание |
| `_yoast_wpseo_twitter-title` | Twitter заголовок |
| `_yoast_wpseo_twitter-description` | Twitter описание |

## Ограничения и особенности

### 1. Права доступа
- Требуются права `manage_categories` для изменения категорий
- Требуются права `edit_post` для изменения постов

### 2. Валидация данных
- `yoast_title`: sanitize_text_field()
- `yoast_description`: sanitize_textarea_field()
- `yoast_canonical`: esc_url_raw()

### 3. Совместимость
- Требует активный Yoast SEO
- Работает с WordPress 5.0+
- Совместим с Yoast SEO 15.0+

## Отладка

### Проверка мета-полей в БД

```sql
SELECT * FROM wp_termmeta 
WHERE meta_key LIKE '_yoast_wpseo_%' 
AND term_id = 4;
```

### Debug функция

```php
function debug_category_yoast_fields($category_id) {
    $fields = array(
        'title' => get_term_meta($category_id, '_yoast_wpseo_title', true),
        'description' => get_term_meta($category_id, '_yoast_wpseo_metadesc', true),
        'keyword' => get_term_meta($category_id, '_yoast_wpseo_focuskw', true)
    );
    return $fields;
}
```

### Логирование в Python

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# В коде
logger.debug(f"Updating category {cat_id} with data: {seo_data}")
logger.info(f"Response: {response.status_code}")
```

## Частые проблемы

### 1. Поля не отображаются в API ответе
**Причина**: Плагин не активирован
**Решение**: Активировать `yoast-rest-api-extension.php`

### 2. Ошибка 403 при обновлении
**Причина**: Недостаточно прав
**Решение**: Проверить права пользователя API

### 3. Поля не сохраняются
**Причина**: Yoast SEO не активен
**Решение**: Активировать Yoast SEO плагин

### 4. Мета-теги не появляются на фронтенде
**Причина**: Кэш Yoast не обновлен
**Решение**: Очистить кэш или пересохранить категорию в админке

## Заключение

Расширение Yoast REST API позволяет:
- ✅ Программно управлять SEO полями категорий
- ✅ Массово обновлять мета-данные
- ✅ Интегрировать с внешними системами
- ✅ Автоматизировать SEO оптимизацию

Плагин полностью совместим с официальной документацией Yoast и следует лучшим практикам WordPress разработки.