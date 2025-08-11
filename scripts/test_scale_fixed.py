import re

with open("content_scale.md", "r") as f:
    content = f.read()

# Простой поиск всех URL блога
all_urls = re.findall(r'https://scale\.com/blog/[^)]+', content)

# Уникальные URL без навигации
unique_urls = set()
for url in all_urls:
    if '/pages/' not in url and '/tag/' not in url:
        unique_urls.add(url)

print("🧪 ТЕСТ SCALE AI (ИСПРАВЛЕННЫЙ)")
print("=" * 60)
print(f"Найдено {len(unique_urls)} уникальных статей:\n")

# Для каждого URL ищем заголовок
articles = {}
for url in sorted(unique_urls):
    url_pos = content.find(url)
    if url_pos > 0:
        # Ищем текст перед URL (увеличенный контекст)
        context = content[max(0, url_pos-800):url_pos]
        
        # Различные паттерны заголовков
        title = None
        
        # Паттерн 1: **Title**
        title_pattern = r'\*\*([^*]+)\*\*'
        title_matches = re.findall(title_pattern, context)
        if title_matches:
            # Берем последний найденный заголовок
            raw_title = title_matches[-1]
            # Убираем escape символы
            title = raw_title.replace('\\', '')
            
        if title and len(title) < 200:
            articles[url] = title

print(f"✅ Статьи с заголовками: {len(articles)}\n")
for i, (url, title) in enumerate(list(articles.items()), 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")