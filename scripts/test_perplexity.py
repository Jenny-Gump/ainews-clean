import re

with open("content_perplexity.md", "r") as f:
    content = f.read()

# Паттерны для Perplexity
patterns = [
    r'### \[([^\]]+)\]\((https://www\.perplexity\.ai/hub/blog/[^)]+)\)',  # Заголовки h3
    r'\*\*([^*]+)\*\*[^\]]*\]\((https://www\.perplexity\.ai/hub/blog/[^)]+)\)',  # Bold заголовки
    r'\[READ MORE\]\((https://www\.perplexity\.ai/hub/blog/[^)]+)\)'  # Read more ссылки
]

print("🧪 ТЕСТ PERPLEXITY")
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
            if url not in articles:
                articles[url] = "Title not found"

print(f"✅ Найдено {len(articles)} статей:\n")
for i, (url, title) in enumerate(list(articles.items())[:20], 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")
