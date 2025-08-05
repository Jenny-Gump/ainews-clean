# Yoast Category API Extension

Плагин для управления Yoast SEO полями категорий через REST API.

## 🚀 Установка

### Способ 1: Через админку WordPress
1. Заархивируйте файл `yoast-category-api.php` в `yoast-category-api.zip`
2. Войдите в админку WordPress: https://ailynx.ru/wp-admin/
3. Перейдите в **Плагины → Добавить новый → Загрузить плагин**
4. Выберите файл `yoast-category-api.zip`
5. Нажмите **Установить** и затем **Активировать**

### Способ 2: Через FTP/файловый менеджер
1. Создайте папку `/wp-content/plugins/yoast-category-api/`
2. Загрузите файл `yoast-category-api.php` в эту папку
3. В админке WordPress перейдите в **Плагины**
4. Найдите "Yoast Category API Extension" и активируйте

## 📋 Требования
- WordPress 5.0+
- Yoast SEO plugin (активирован)
- Права администратора

## 🔧 API Эндпоинты

### 1. Получение SEO данных категории
```
GET /wp-json/yoast-category/v1/category/{id}
```

**Ответ:**
```json
{
  "category_id": 4,
  "category_name": "Машинное обучение",
  "category_slug": "mashinnoe-obuchenie",
  "yoast_title": "Машинное обучение - ML новости | AI Lynx",
  "yoast_desc": "Актуальные новости машинного обучения...",
  "yoast_keyword": "машинное обучение"
}
```

### 2. Обновление SEO данных категории
```
POST /wp-json/yoast-category/v1/category/{id}
Content-Type: application/json

{
  "yoast_title": "Новый SEO заголовок",
  "yoast_desc": "Новое мета-описание",
  "yoast_keyword": "ключевое слово"
}
```

### 3. Массовое обновление категорий
```
POST /wp-json/yoast-category/v1/categories/bulk
Content-Type: application/json

[
  {
    "category_id": 4,
    "yoast_title": "Заголовок 1",
    "yoast_desc": "Описание 1",
    "yoast_keyword": "ключевое слово 1"
  },
  {
    "category_id": 5,
    "yoast_title": "Заголовок 2", 
    "yoast_desc": "Описание 2",
    "yoast_keyword": "ключевое слово 2"
  }
]
```

## 🔐 Аутентификация

Используйте WordPress Application Password:
```python
import requests
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth('admin', 'tE85 PFT4 Ghq9 nl26 nQlt gBnG')
response = requests.get('https://ailynx.ru/wp-json/yoast-category/v1/category/4', auth=auth)
```

## 🧪 Тестирование

После установки плагина запустите:
```bash
cd "/Users/skynet/Desktop/AI DEV/ainews-clean"
source venv/bin/activate
python scripts/test_yoast_plugin.py
```

## 🛠️ Поддерживаемые поля

- `yoast_title` - SEO заголовок
- `yoast_desc` - Мета-описание  
- `yoast_keyword` - Фокусное ключевое слово
- `yoast_canonical` - Canonical URL
- `yoast_noindex` - Индексация (0/1)

## 🔍 Проверка работы

1. Обновите категорию через API
2. Проверьте в админке: https://ailynx.ru/wp-admin/term.php?taxonomy=category&tag_ID=4
3. Проверьте на фронтенде: https://ailynx.ru/category/novosti/mashinnoe-obuchenie/

## 🐛 Устранение неполадок

### Ошибка 404 "Эндпоинт не найден"
- Убедитесь, что плагин активирован
- Проверьте структуру постоянных ссылок в WordPress

### Ошибка 403 "Недостаточно прав"
- Проверьте Application Password
- Убедитесь, что пользователь имеет права `manage_categories`

### Поля не сохраняются
- Убедитесь, что Yoast SEO активен
- Перезайдите в админку WordPress
- Очистите кеш (если используется)