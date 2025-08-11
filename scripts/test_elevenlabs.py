import re

with open("content_elevenlabs.md", "r") as f:
    content = f.read()

# Паттерны для ElevenLabs
patterns = [
    r'\[\*\*([^*]+)\*\*\]\((https://elevenlabs\.io/blog/[^)]+)\)',  # Bold заголовки
    r'\[Read article\]\((https://elevenlabs\.io/blog/[^)]+)\)'      # Read article ссылки
]

print("🧪 ТЕСТ ELEVENLABS")
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
                # Ищем заголовок рядом
                url_pos = content.find(url)
                if url_pos > 0:
                    context = content[max(0, url_pos-200):url_pos]
                    title_match = re.search(r'## ([^\n]+)', context)
                    if title_match:
                        articles[url] = title_match.group(1)

# Фильтруем
filtered = {}
for url, title in articles.items():
    if '?category=' in url:
        continue
    filtered[url] = title

print(f"✅ Найдено {len(filtered)} статей:\n")
for i, (url, title) in enumerate(list(filtered.items())[:15], 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")
