import re
import json

# Загружаем конфигурацию
with open("../services/source_extractors.json", "r") as f:
    config = json.load(f)

# Читаем контент
with open("content_huggingface.md", "r") as f:
    content = f.read()

hf_config = config["extractors"]["huggingface"]
patterns = hf_config["patterns"]
exclude_urls = hf_config["exclude_urls"]

print("🧪 РЕАЛЬНЫЙ ТЕСТ HUGGING FACE")
print("=" * 60)

# Ищем URL
url_pattern = patterns[0]
urls = re.findall(url_pattern, content)

print(f"Найдено {len(urls)} URL")

# Фильтруем и извлекаем заголовки
articles = []
for url in urls:
    # Проверяем исключения
    skip = False
    for exclude in exclude_urls:
        if exclude.endswith('$'):
            # Это regex для расширений файлов
            if re.search(exclude, url):
                skip = True
                break
        elif exclude in url:
            skip = True
            break
    
    if skip:
        continue
    
    # Ищем заголовок перед URL
    url_pos = content.find(url)
    if url_pos > 0:
        context = content[max(0, url_pos-500):url_pos]
        
        # Используем паттерн для заголовка
        title_match = re.search(r'\*\*([^*]+)\*\*', context)
        if title_match:
            title = title_match.group(1).strip()
            articles.append((title, url))

# Убираем дубликаты
seen = set()
unique_articles = []
for title, url in articles:
    if url not in seen:
        seen.add(url)
        unique_articles.append((title, url))

print(f"\n✅ Найдено {len(unique_articles)} уникальных статей:\n")
for i, (title, url) in enumerate(unique_articles[:15], 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}")
