import re

# Читаем контент
with open("content_huggingface.md", "r") as f:
    content = f.read()

# Новые паттерны для Hugging Face
patterns = [
    # Основной паттерн - ищет статьи с заголовками
    r'\[\*\*([^*]+)\*\*[^\]]*\]\((https://huggingface\.co/blog/[^)]+)\)',
    # Запасной паттерн для ссылок без bold заголовка
    r'\[([^\]]+)\]\((https://huggingface\.co/blog/[^)]+)\)'
]

print("🧪 ТЕСТИРОВАНИЕ ПАТТЕРНОВ HUGGING FACE")
print("=" * 60)

all_matches = []
for i, pattern in enumerate(patterns, 1):
    print(f"\n📋 Паттерн {i}: {pattern[:50]}...")
    matches = list(re.finditer(pattern, content, re.IGNORECASE | re.DOTALL))
    
    print(f"   Найдено: {len(matches)} совпадений")
    
    for j, match in enumerate(matches[:5], 1):
        title = match.group(1).strip()
        url = match.group(2)
        
        # Фильтруем изображения и служебные ссылки
        if any(url.endswith(ext) for ext in ['.gif', '.png', '.jpg', '.jpeg']):
            continue
        if '/community' in url or '/assets/' in url:
            continue
            
        # Очищаем заголовок
        title = title.replace('\\n', ' ').replace('\\\\', '').strip()
        
        print(f"   {j}. {title[:60]}...")
        print(f"      URL: {url}")
        all_matches.append((title, url))

# Уникальные URL
unique_urls = {}
for title, url in all_matches:
    if url not in unique_urls:
        unique_urls[url] = title

print(f"\n📊 ИТОГО")
print(f"Уникальных статей: {len(unique_urls)}")
print(f"\n✅ Примеры найденных статей:")
for i, (url, title) in enumerate(list(unique_urls.items())[:10], 1):
    print(f"{i}. {title[:60]}...")
    print(f"   {url}")
