import re

with open("content_perplexity.md", "r") as f:
    content = f.read()

# Исправленный паттерн для Perplexity
patterns = [
    r'\]\((https://www\.perplexity\.ai/hub/blog/[^)]+)\)',  # Все ссылки на блог
]

print("🧪 ТЕСТ PERPLEXITY (ИСПРАВЛЕННЫЙ)")
print("=" * 60)

urls = set()
for pattern in patterns:
    matches = re.findall(pattern, content)
    urls.update(matches)

print(f"✅ Найдено {len(urls)} статей")
print("\nПримеры URL:")
for i, url in enumerate(list(urls)[:10], 1):
    # Извлекаем slug
    slug = url.split('/')[-1]
    print(f"  {i}. .../{slug}")