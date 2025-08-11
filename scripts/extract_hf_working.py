import re

with open("content_huggingface.md", "r") as f:
    content = f.read()

# Ищем все URL блогов HF (они в конце блоков)
url_pattern = r'\]\((https://huggingface\.co/blog/[^)]+)\)'
urls = re.findall(url_pattern, content)

print(f"Найдено {len(urls)} ссылок на блог")

# Для каждого URL ищем заголовок перед ним
articles = []
for url in urls:
    # Пропускаем медиа
    if any(skip in url for skip in ['.gif', '.png', '.jpg', '/assets/', '/community']):
        continue
    
    # Ищем текст перед этим URL
    url_pos = content.find(url)
    if url_pos > 0:
        # Берем 500 символов перед URL
        context = content[max(0, url_pos-500):url_pos]
        
        # Ищем заголовок в формате **Title**
        title_match = re.search(r'\*\*([^*]+)\*\*', context)
        if title_match:
            title = title_match.group(1).strip()
            articles.append((title, url))

# Убираем дубликаты
seen = set()
unique_articles = []
for title, url in articles:
    if url not in seen:
        seen.add(url)
        unique_articles.append((title, url))

print(f"\n✅ Найдено {len(unique_articles)} уникальных статей:\n")
for i, (title, url) in enumerate(unique_articles[:20], 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")
