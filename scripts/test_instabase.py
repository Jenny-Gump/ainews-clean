import re

with open("content_instabase.md", "r") as f:
    content = f.read()

# Паттерны для Instabase
patterns = [
    r'\]\((https://instabase\.com/blog/[^)]+)\)',  # Все ссылки на блог
]

print("🧪 ТЕСТ INSTABASE")
print("=" * 60)

urls = set()
for pattern in patterns:
    matches = re.findall(pattern, content)
    for url in matches:
        if '/page/' not in url and '/category/' not in url:
            urls.add(url)

# Для каждого URL ищем заголовок
articles = {}
for url in urls:
    url_pos = content.find(url)
    if url_pos > 0:
        # Ищем текст перед URL
        context = content[max(0, url_pos-500):url_pos]
        
        # Ищем заголовки
        lines = context.split('\n')
        for line in reversed(lines):
            line = line.strip()
            # Пропускаем служебные строки
            if line.startswith('[') or line.startswith('!') or 'Read' in line:
                continue
            # Ищем заголовок
            if line.startswith('### '):
                title = line[4:].strip()
                articles[url] = title
                break
            elif line.startswith('## '):
                title = line[3:].strip()
                articles[url] = title  
                break
            elif line and len(line) > 10 and len(line) < 200:
                # Проверяем, что это похоже на заголовок
                if not any(skip in line.lower() for skip in ['posted', 'by ', 'date', 'min read']):
                    articles[url] = line
                    break

print(f"✅ Найдено {len(articles)} статей:\n")
for i, (url, title) in enumerate(list(articles.items()), 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")