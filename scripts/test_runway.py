import re

with open("content_runway.md", "r") as f:
    content = f.read()

# Паттерны для Runway
patterns = [
    r'\]\((https://runwayml\.com/research/[^)]+)\)',  # Простые ссылки
]

print("🧪 ТЕСТ RUNWAY")
print("=" * 60)

urls = set()
for pattern in patterns:
    matches = re.findall(pattern, content)
    urls.update(matches)

# Для каждого URL ищем заголовок
articles = {}
for url in urls:
    url_pos = content.find(url)
    if url_pos > 0:
        # Ищем текст перед URL
        context = content[max(0, url_pos-300):url_pos]
        # Различные паттерны заголовков
        lines = context.split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith('[') and not line.startswith('\!') and len(line) > 5:
                # Убираем escape символы
                title = line.replace('\\\\', '').replace('\\', '')
                if len(title) < 200:
                    articles[url] = title
                    break

print(f"✅ Найдено {len(articles)} статей:\n")
for i, (url, title) in enumerate(list(articles.items())[:20], 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")
