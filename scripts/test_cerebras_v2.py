import re

with open("content_cerebras.md", "r") as f:
    content = f.read()

# Несколько паттернов для Cerebras
patterns = [
    r'\*\*([^*]+)\*\*[^\]]*\]\((https://www\.cerebras\.ai/blog/[^)]+)\)',
    r'\]\((https://www\.cerebras\.ai/blog/[^)]+)\)'
]

print("🧪 ТЕСТ CEREBRAS V2")
print("=" * 60)

urls = set()
for pattern in patterns:
    matches = re.findall(pattern, content)
    for match in matches:
        if isinstance(match, tuple):
            url = match[1] if len(match) > 1 else match[0]
        else:
            url = match
        urls.add(url)

# Для каждого URL ищем заголовок
articles = {}
for url in urls:
    url_pos = content.find(url)
    if url_pos > 0:
        context = content[max(0, url_pos-200):url_pos]
        # Ищем заголовок
        title_match = re.search(r'\*\*([^*]+)\*\*', context)
        if title_match:
            articles[url] = title_match.group(1).strip()

print(f"✅ Найдено {len(articles)} статей:\n")
for i, (url, title) in enumerate(list(articles.items())[:25], 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")
