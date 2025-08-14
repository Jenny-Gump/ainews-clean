# 🛠️ Инструкции по настройке парсинга URL - Change Tracking

**Версия**: 1.0  
**Создано**: 2025-08-11  
**Назначение**: Точные инструкции для модификации настроек извлечения URL из источников

---

## ⚠️ КРИТИЧЕСКИ ВАЖНО

**НИКОГДА НЕ ИСПОЛЬЗУЙ УНИВЕРСАЛЬНЫЕ ПАТТЕРНЫ В ОБЩЕМ ЭКСТРАКТОРЕ!**

❌ **НЕПРАВИЛЬНО**: Добавлять общие паттерны в основной `url_extractor.py`  
✅ **ПРАВИЛЬНО**: Использовать индивидуальную обработку для каждого проблемного источника

---

## 📋 Архитектурные принципы

### 1. Индивидуальный подход
- Каждый источник имеет уникальную структуру markdown
- Универсальные решения НЕ РАБОТАЮТ
- Источники требуют специфичной обработки

### 2. Правильная иерархия решений
1. **Общий экстрактор** - стандартные markdown паттерны
2. **Специальные методы** - для источников с особой структурой
3. **Индивидуальные конфигурации** - через `source_extractors_complete.json`

---

## 🔧 Как правильно добавлять обработку источников

### Шаг 1: Диагностика проблемы
```bash
# Проверить что источник возвращает 0 URL
python core/main.py --change-tracking --scan --limit 1 --source "problem_source.com"

# Посмотреть статистику
python core/main.py --change-tracking --stats
```

### Шаг 2: Анализ контента
```python
# Получить markdown контент источника для анализа
from change_tracking.monitor import ChangeMonitor
monitor = ChangeMonitor()
result = await monitor.scan_webpage("https://problem_source.com/news")
print("Content sample:", result.get('content', '')[:500])
```

### Шаг 3: Определить тип проблемы

#### Тип А: Escape-последовательности (`\\\\\\\\`)
**Симптомы**: Контент содержит `текст\\\\\\\\еще текст\\\\\\\\дата](url)`

**Решение**: Добавить домен в `escape_sources` в `url_extractor.py:259-261`

```python
escape_sources = [
    'deepmind.google', 'new.abb.com', 'scale.com', 'stability.ai', 'waymo.com',
    'NEW_DOMAIN.com'  # Добавить новый домен
]
```

#### Тип Б: Нестандартная структура markdown
**Симптомы**: Ссылки в необычном формате

**Решение**: Создать новый метод типа `_extract_custom_format_links()` в `url_extractor.py`

#### Тип В: Нужны специфичные паттерны
**Решение**: Добавить в `source_extractors_complete.json`

---

## 📂 Где НЕ НАДО вносить изменения

### ❌ ЗАПРЕЩЕНО модифицировать:

1. **Основные паттерны экстрактора**
   - `url_extractor.py` - общие `markdown_link_patterns`
   - `url_extractor.py` - общие `domain_patterns`
   - `url_extractor.py` - общие `exclude_patterns`

2. **Универсальные методы**
   - `_extract_all_links()` - НЕ добавлять туда специфичную логику
   - `_is_article_url()` - НЕ добавлять частные случаи

---

## ✅ Где ПРАВИЛЬНО вносить изменения

### 1. Для escape-источников
**Файл**: `url_extractor.py`  
**Место**: Строки 259-261, список `escape_sources`
**Метод**: Используется существующий `_extract_escape_links()`

### 2. Для источников с кастомной структурой
**Файл**: `url_extractor.py`  
**Место**: Создать новый метод типа `_extract_CUSTOM_links()`
**Интеграция**: Добавить условие в `extract_urls_from_content()` после строки 264

Пример:
```python
# В extract_urls_from_content() после escape_sources
custom_sources = ['example.com', 'another.com']

if any(domain in source_page_url for domain in custom_sources):
    found_urls.extend(self._extract_custom_links(markdown_content, source_page_url, source_domain))
```

### 3. Для тонкой настройки
**Файл**: `services/source_extractors_complete.json`  
**Назначение**: Индивидуальные паттерны для конкретных источников (пока не используется в коде)

---

## 🎯 Процедура исправления источников

### 1. Подготовка
```bash
# Создать backup
backup_dir="backups/url_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p $backup_dir
cp change_tracking/url_extractor.py $backup_dir/
```

### 2. Анализ источника
- Получить образец markdown контента
- Определить формат ссылок
- Выбрать подходящий тип решения

### 3. Внесение изменений
- Добавить домен в соответствующий список
- ИЛИ создать специальный метод
- Обновить интеграцию в `extract_urls_from_content()`

### 4. Тестирование
```bash
# Протестировать конкретный источник
python core/main.py --change-tracking --scan --limit 1 --source "fixed_source.com"

# Проверить что URL извлекаются
python core/main.py --change-tracking --stats
```

### 5. Документирование
- Обновить `change_tracking/README.md`
- Зафиксировать в changelog
- Отметить в данном файле

---

## 📊 Примеры успешных исправлений

### DeepMind (escape-формат)
**Проблема**: `0 → 8 URL`  
**Решение**: Добавлен в `escape_sources`
**Результат**: ✅ Работает

### ABB Robotics (escape-формат)  
**Проблема**: `0 → 16 URL`  
**Решение**: Добавлен в `escape_sources`  
**Результат**: ✅ Работает

### Scale AI (escape-формат)
**Проблема**: `0 → 26 URL`  
**Решение**: Добавлен в `escape_sources`
**Результат**: ✅ Работает

---

## 🚨 Частые ошибки и как их избежать

### Ошибка 1: Модификация общего экстрактора
```python
# ❌ НЕПРАВИЛЬНО
def _extract_all_links(self, content: str):
    # Добавление специфичной логики для одного источника
    if 'special_domain.com' in content:
        # специальная обработка
```

```python
# ✅ ПРАВИЛЬНО  
escape_sources = [
    'deepmind.google', 'new.abb.com', 'special_domain.com'
]

if any(domain in source_page_url for domain in escape_sources):
    found_urls.extend(self._extract_escape_links(...))
```

### Ошибка 2: Изменение универсальных паттернов
```python
# ❌ НЕПРАВИЛЬНО - добавление в общие паттерны
self.markdown_link_patterns = [
    r'\\[([^\\]]*)\\]\\((https?://[^)]+)\\)',
    r'SPECIAL_PATTERN_FOR_ONE_SITE',  # НЕ ДЕЛАЙ ТАК!
]
```

### Ошибка 3: Игнорирование индивидуальной структуры
- Каждый источник уникален
- Один паттерн НЕ решит проблему для всех
- Нужен анализ каждого источника отдельно

---

## 📝 Отчетность

### После каждого исправления записывать:
1. **Источник**: Какой домен исправлялся
2. **Проблема**: Что было не так (0 URL, неправильные URL, etc.)
3. **Решение**: Какой метод использовался
4. **Результат**: Сколько URL стало извлекаться
5. **Файлы**: Какие файлы модифицировались

### Пример записи:
```
Источник: crusoe.ai
Проблема: 0 URL из-за нестандартного пути /resources/blog/
Решение: Обновлен domain_patterns в url_extractor.py:58
Результат: 0 → 12 URL
Файлы: change_tracking/url_extractor.py
```

---

## 🔄 Следующие задачи

### Оставшиеся источники (23 из 28):
Требуют индивидуального анализа и исправления:
- ai21, appzen, audioscenic, augmedix, b12, c3ai, cerebras
- cloudflare, cohere, crusoe, cursor, doosan_robotics, elevenlabs  
- fanuc, instabase, kinova, lambda, manus, mindfoundry, mistral
- nscale, pathai, suno, tempus, together, uizard

### Методология:
1. Анализировать по одному
2. Определять тип проблемы
3. Применять соответствующее решение
4. Тестировать и документировать
5. Переходить к следующему

---

**ПОМНИ: Индивидуальный подход - это ЕДИНСТВЕННЫЙ правильный способ!**