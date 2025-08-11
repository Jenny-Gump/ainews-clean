import re

with open("content_crusoe.md", "r") as f:
    content = f.read()

# Паттерны для Crusoe AI
patterns = [
    r'\]\((https://www\.crusoe\.ai/resources/blog/[^)]+)\)',  # Новый формат URL
]

print("🧪 ТЕСТ CRUSOE AI")
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
        
        # Ищем заголовки в формате ### Title или просто Title
        lines = context.split('\n')
        for line in reversed(lines):
            line = line.strip()
            # Пропускаем служебные строки
            if line.startswith('[Read more') or line.startswith('Arrow Right'):
                continue
            # Ищем заголовок
            if line.startswith('### '):
                title = line[4:].strip()
                articles[url] = title
                break
            elif line and not line.startswith('[') and not line.startswith('!') and not line.startswith('#') and len(line) > 10:
                # Обычный заголовок без ###
                title = line.strip()
                if len(title) < 200 and 'Crusoe' in title or 'AI' in title or 'Cloud' in title:
                    articles[url] = title
                    break

print(f"✅ Найдено {len(articles)} статей:\n")
for i, (url, title) in enumerate(list(articles.items())[:20], 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")