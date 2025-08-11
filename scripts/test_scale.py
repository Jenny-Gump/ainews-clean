import re

with open("content_scale.md", "r") as f:
    content = f.read()

# Паттерны для Scale AI
patterns = [
    r'Read more\]\((https://scale\.com/blog/[^)]+)\)',  # Read more ссылки
]

print("🧪 ТЕСТ SCALE AI")
print("=" * 60)

urls = set()
for pattern in patterns:
    matches = re.findall(pattern, content)
    # Фильтруем страницы навигации и другие нежелательные URL
    for url in matches:
        if '/pages/' not in url and '/tag/' not in url:
            urls.add(url)

# Для каждого URL ищем заголовок
articles = {}
for url in urls:
    url_pos = content.find(url)
    if url_pos > 0:
        # Ищем текст перед URL
        context = content[max(0, url_pos-500):url_pos]
        # Ищем заголовок в формате **Title**
        title_pattern = r'\*\*([^*]+)\*\*'
        title_matches = re.findall(title_pattern, context)
        if title_matches:
            # Берем последний найденный заголовок
            title = title_matches[-1].replace('\\', '')
            articles[url] = title

print(f"✅ Найдено {len(articles)} статей:\n")
for i, (url, title) in enumerate(list(articles.items()), 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")