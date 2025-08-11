import requests
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

# Suno AI Blog
source_url = "https://suno.com/blog"

print(f"Получаю контент с Suno AI Blog...")
print(f"URL: {source_url}")

url = "https://api.firecrawl.dev/v1/scrape"
headers = {
    "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "url": source_url,
    "formats": ["markdown"],
    "timeout": 60000
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        markdown = result.get("data", {}).get("markdown", "")
        
        # Сохраняем контент
        with open("content_suno.md", "w") as f:
            f.write(markdown)
        
        print(f"✓ Контент сохранен в content_suno.md")
        print(f"  Размер: {len(markdown)} символов")
        
        # Проверяем наличие статей
        import re
        pattern = r'https://suno\.com/blog/[^)\s"]+'
        urls = re.findall(pattern, markdown)
        unique_urls = list(set(urls))
        
        print(f"✓ Найдено {len(unique_urls)} уникальных статей")
        if unique_urls:
            print("Примеры:")
            for url in unique_urls[:3]:
                slug = url.split('/')[-1]
                title = slug.replace('-', ' ').title()
                print(f"  → {title[:50]}...")
    else:
        print(f"✗ Ошибка API: {result}")
else:
    print(f"✗ HTTP Error {response.status_code}")