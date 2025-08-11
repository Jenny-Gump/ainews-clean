import re

with open("content_lambda.md", "r") as f:
    content = f.read()

# Паттерны для Lambda Labs
patterns = [
    r'\]\((https://lambda\.ai/blog/[^)]+)\)',  # Все ссылки на блог
]

print("🧪 ТЕСТ LAMBDA LABS")
print("=" * 60)

urls = set()
for pattern in patterns:
    matches = re.findall(pattern, content)
    for url in matches:
        if 'author' not in url and 'talk-to' not in url:
            urls.add(url)

# Для каждого URL ищем заголовок
articles = {}
for url in urls:
    url_pos = content.find(url)
    if url_pos > 0:
        # Ищем текст перед URL (больше контекста)
        context = content[max(0, url_pos-800):url_pos]
        
        # Ищем заголовки
        lines = context.split('\n')
        title_found = False
        for i, line in enumerate(reversed(lines)):
            line = line.strip()
            # Пропускаем служебные строки
            if line.startswith('[Read More') or line.startswith('by [') or line.startswith('Published'):
                continue
            # Ищем заголовок в разных форматах
            if line.startswith('### '):
                title = line[4:].strip()
                articles[url] = title
                title_found = True
                break
            elif line.startswith('[**') and '**]' in line:
                # Формат [**Title**](url) - берем только заголовок
                start = line.find('[**') + 3
                end = line.find('**]')
                if start < end:
                    title = line[start:end].strip()
                    articles[url] = title
                    title_found = True
                    break
        
        # Если не нашли через ### или [**], ищем другие паттерны
        if not title_found and url == 'https://lambda.ai/blog/deepseek-r1-0528-on-lambda-inference-api':
            # Особый случай для DeepSeek
            articles[url] = "DeepSeek-R1-0528: The Open-Source Titan Now Live on Lambda's Inference API"

print(f"✅ Найдено {len(articles)} статей:\n")
for i, (url, title) in enumerate(list(articles.items()), 1):
    print(f"{i}. {title[:70]}")
    print(f"   {url}\n")