import re

with open("content_cohere.md", "r") as f:
    lines = f.readlines()

print("🧪 АНАЛИЗ COHERE")
print("=" * 60)

# Ищем статьи по паттерну: заголовок, теги, Read full article
articles = []
for i in range(len(lines)):
    if "Read full article" in lines[i] and "cohere.com/blog/" in lines[i]:
        # Извлекаем URL
        url_match = re.search(r'\((https://cohere\.com/blog/[^)]+)\)', lines[i])
        if url_match:
            url = url_match.group(1)
            
            # Пропускаем авторов
            if '/authors/' in url:
                continue
                
            # Ищем заголовок выше (обычно 2-4 строки выше)
            title = None
            for j in range(i-1, max(0, i-10), -1):
                line = lines[j].strip()
                # Пропускаем пустые строки, теги и метаданные
                if (line and 
                    not line.startswith('[') and 
                    not line.startswith('\![') and
                    not '—' in line and
                    not 'https://' in line and
                    len(line) > 10 and len(line) < 150):
                    title = line
                    break
            
            if title:
                articles.append((title, url))

# Убираем дубликаты
seen = set()
unique_articles = []
for title, url in articles:
    if url not in seen:
        seen.add(url)
        unique_articles.append((title, url))

print(f"✅ Найдено {len(unique_articles)} уникальных статей:\n")
for i, (title, url) in enumerate(unique_articles[:20], 1):
    print(f"{i}. {title}")
    print(f"   {url}\n")
