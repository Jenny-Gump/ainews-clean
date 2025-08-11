import json
import re

# Загружаем конфигурацию
with open("../services/source_extractors.json", "r") as f:
    config = json.load(f)

# Проверяем Scale AI
source_config = config["extractors"]["scale"]
print(f"🔍 Проверка экстрактора: {source_config['name']}")
print(f"URL: {source_config['url']}")
print(f"Статус: {source_config['status']}")
print(f"Паттерны: {source_config['patterns']}")

# Загружаем контент
with open("content_scale.md", "r") as f:
    content = f.read()

# Применяем паттерны
urls = set()
for pattern in source_config["patterns"]:
    matches = re.findall(pattern, content)
    urls.update(matches)

# Фильтруем по exclude_urls
filtered_urls = []
for url in urls:
    skip = False
    for exclude in source_config.get("exclude_urls", []):
        if exclude in url:
            skip = True
            break
    if not skip:
        filtered_urls.append(url)

print(f"\n✅ Найдено {len(filtered_urls)} URL:")
for i, url in enumerate(filtered_urls[:5], 1):
    print(f"  {i}. {url}")

# Проверяем Anthropic
print("\n" + "="*60)
source_config = config["extractors"]["anthropic"]
print(f"🔍 Проверка экстрактора: {source_config['name']}")
print(f"Статус: {source_config['status']}")

with open("content_anthropic.md", "r") as f:
    content = f.read()

urls = set()
for pattern in source_config["patterns"]:
    # Сложные паттерны требуют особой обработки
    if "\\\\\\\\\\\\\\\\s*\\n" in pattern:
        # Упрощаем для теста
        simple_pattern = r'\]\((https://www\.anthropic\.com/news/[^)]+)\)'
        matches = re.findall(simple_pattern, content)
    else:
        matches = re.findall(pattern, content)
    urls.update(matches)

print(f"✅ Найдено {len(urls)} URL (первые 5):")
for i, url in enumerate(list(urls)[:5], 1):
    print(f"  {i}. {url}")