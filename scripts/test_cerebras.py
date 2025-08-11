import re

with open("content_cerebras.md", "r") as f:
    content = f.read()

# Паттерн для Cerebras - заголовок и URL вместе
pattern = r'\*\*([^*]+)\*\*\]\((https://www\.cerebras\.ai/blog/[^)]+)\)'

print("🧪 ТЕСТ CEREBRAS")
print("=" * 60)

matches = re.findall(pattern, content)

# Убираем дубликаты
articles = {}
for title, url in matches:
    if url not in articles:
        articles[url] = title.strip()

print(f"✅ Найдено {len(articles)} статей:\n")
for i, (url, title) in enumerate(list(articles.items())[:20], 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")
