import re

with open("content_mistral.md", "r") as f:
    content = f.read()

# Паттерны для Mistral
patterns = [
    r'\]\((https://mistral\.ai/news/[^)]+)\)',  # Простые ссылки
    r'\*\*([^*]+)\*\*[^\]]*\]\((https://mistral\.ai/news/[^)]+)\)'  # С заголовками
]

print("🧪 ТЕСТ MISTRAL AI")
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
            # Ищем заголовок рядом
            url_pos = content.find(url)
            if url_pos > 0:
                context = content[max(0, url_pos-200):url_pos]
                title_match = re.search(r'\*\*([^*]+)\*\*', context)
                if title_match:
                    articles[url] = title_match.group(1).strip()

print(f"✅ Найдено {len(articles)} статей:\n")
for i, (url, title) in enumerate(list(articles.items()), 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")
