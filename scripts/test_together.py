import re

with open("content_together.md", "r") as f:
    content = f.read()

# Паттерны для Together AI
patterns = [
    r'\]\((https://www\.together\.ai/blog/[^)]+)\)',  # Простые ссылки
    r'\*\*([^*]+)\*\*[^\]]*\]\((https://www\.together\.ai/blog/[^)]+)\)'  # С заголовками
]

print("🧪 ТЕСТ TOGETHER AI")
print("=" * 60)

articles = {}
for pattern in patterns:
    matches = re.findall(pattern, content)
    for match in matches:
        if isinstance(match, tuple):
            if len(match) == 2:
                title, url = match
                articles[url] = title.strip()
        else:
            url = match
            # Ищем заголовок перед URL
            url_pos = content.find(url)
            if url_pos > 0:
                context = content[max(0, url_pos-300):url_pos]
                title_match = re.search(r'\*\*([^*]+)\*\*', context)
                if title_match:
                    articles[url] = title_match.group(1).strip()

print(f"✅ Найдено {len(articles)} статей:\n")
for i, (url, title) in enumerate(list(articles.items())[:20], 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")
