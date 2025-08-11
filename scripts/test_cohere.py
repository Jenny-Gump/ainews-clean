import re

with open("content_cohere.md", "r") as f:
    content = f.read()

# Паттерн для Cohere - простые ссылки и ссылки с изображениями
patterns = [
    r'\[Read full article\]\((https://cohere\.com/blog/[^)]+)\)',
    r'\[Learn more on the blog\]\((https://cohere\.com/blog/[^)]+)\)',
    r'\]\((https://cohere\.com/blog/[^)]+)\)'
]

print("🧪 ТЕСТ COHERE")
print("=" * 60)

all_urls = set()
for pattern in patterns:
    urls = re.findall(pattern, content)
    for url in urls:
        # Пропускаем авторов и теги
        if '/authors/' in url or '?tag=' in url:
            continue
        all_urls.add(url)

print(f"Найдено {len(all_urls)} уникальных URL статей")

# Для каждого URL ищем заголовок
articles = []
for url in all_urls:
    url_pos = content.find(url)
    if url_pos > 0:
        # Берем 300 символов перед URL
        context = content[max(0, url_pos-300):url_pos]
        
        # Ищем заголовок - это обычно последняя строка перед тегами
        lines = context.split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith('[') and not line.startswith('\![') and not line.startswith('—'):
                # Это вероятно заголовок
                if len(line) > 10 and len(line) < 200:
                    articles.append((line, url))
                    break

# Убираем дубликаты
seen = set()
unique_articles = []
for title, url in articles:
    if url not in seen:
        seen.add(url)
        unique_articles.append((title, url))

print(f"\n✅ Найдено {len(unique_articles)} статей с заголовками:\n")
for i, (title, url) in enumerate(unique_articles[:15], 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")
