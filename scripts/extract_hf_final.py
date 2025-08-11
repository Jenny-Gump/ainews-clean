import re

with open("content_huggingface.md", "r") as f:
    content = f.read()

# Комплексный паттерн для многострочной структуры HF
# Ищем блоки вида: [**Title** \\ ... ](url)
pattern = r'\[\*\*([^*]+?)\*\*[^]]*?\]\((https://huggingface\.co/blog/[^)]+)\)'

print("🧪 ФИНАЛЬНЫЙ ТЕСТ HUGGING FACE")
print("=" * 60)

matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))

unique_articles = {}
for match in matches:
    title = match.group(1).strip()
    url = match.group(2)
    
    # Пропускаем медиа и служебные страницы
    if any(skip in url for skip in ['.gif', '.png', '.jpg', '/assets/', '/community']):
        continue
    
    # Очищаем заголовок
    title = re.sub(r'\\+', '', title).strip()
    title = re.sub(r'\s+', ' ', title)
    
    if url not in unique_articles:
        unique_articles[url] = title

print(f"✅ Найдено {len(unique_articles)} уникальных статей:\n")
for i, (url, title) in enumerate(list(unique_articles.items())[:20], 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")
