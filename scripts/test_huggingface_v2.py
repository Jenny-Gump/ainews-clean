import re

with open("content_huggingface.md", "r") as f:
    content = f.read()

# Паттерн для Hugging Face - заголовок и URL разделены метаданными
pattern = r'\[\*\*([^*]+)\*\*[^\]]*\]\((https://huggingface\.co/blog/[^)]+)\)'

print("🧪 ТЕСТИРОВАНИЕ HUGGING FACE")
print("=" * 60)

matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))
print(f"Найдено совпадений: {len(matches)}")

unique_articles = {}
for match in matches:
    title = match.group(1).strip().replace('\\', '')
    url = match.group(2)
    
    # Фильтруем медиа и служебные страницы
    if any(ext in url for ext in ['.gif', '.png', '.jpg', '/assets/', '/community']):
        continue
        
    if url not in unique_articles:
        unique_articles[url] = title

print(f"\n✅ Найдено {len(unique_articles)} уникальных статей:")
for i, (url, title) in enumerate(list(unique_articles.items())[:15], 1):
    print(f"{i}. {title[:60]}")
    print(f"   {url}")
