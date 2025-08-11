import re

with open("content_stability.md", "r") as f:
    content = f.read()

# Паттерны для Stability AI
patterns = [
    r'# \[([^\]]+)\]\((https://stability\.ai/news/[^)]+)\)',  # Заголовки
    r'\[Read More\]\((https://stability\.ai/news/[^)]+)\)'     # Read More ссылки
]

print("🧪 ТЕСТ STABILITY AI")
print("=" * 60)

articles = {}
for pattern in patterns:
    matches = re.findall(pattern, content)
    for match in matches:
        if len(match) == 2:  # Заголовок + URL
            title, url = match
            articles[url] = title
        else:  # Только URL
            url = match
            if url not in articles:
                articles[url] = "Title not found"

# Фильтруем
filtered = {}
for url, title in articles.items():
    # Пропускаем категории и теги
    if '?category=' in url or '?tags=' in url or '?sort=' in url:
        continue
    filtered[url] = title

print(f"✅ Найдено {len(filtered)} статей:\n")
for i, (url, title) in enumerate(list(filtered.items())[:20], 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")
