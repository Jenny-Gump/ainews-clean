import requests
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

# Попробуем разные варианты URL для Lambda
lambda_urls = [
    ("Lambda Blog Page 2", "https://lambda.ai/blog?page=2"),
    ("Lambda Blog Page 3", "https://lambda.ai/blog?page=3"),
    ("Lambda Blog Archive", "https://lambda.ai/blog/archive"),
    ("Lambda Blog All", "https://lambda.ai/blog/all"),
    ("Lambda GPU Cloud Category", "https://lambda.ai/blog/category/gpu-cloud"),
    ("Lambda Announcements", "https://lambda.ai/blog/category/announcements"),
]

url = "https://api.firecrawl.dev/v1/scrape"
headers = {
    "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}",
    "Content-Type": "application/json"
}

all_urls = []

for name, lambda_url in lambda_urls:
    print(f"\nПроверяю {name}...")
    print(f"URL: {lambda_url}")
    
    data = {
        "url": lambda_url,
        "formats": ["markdown"],
        "timeout": 60000
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                markdown = result.get("data", {}).get("markdown", "")
                
                # Сохраняем контент
                filename = f"content_{name.lower().replace(' ', '_')}.md"
                with open(filename, "w") as f:
                    f.write(markdown)
                
                # Считаем статьи
                import re
                pattern = r'https://lambda\.ai/blog/[^)"\s]+'
                urls = re.findall(pattern, markdown)
                # Фильтруем
                article_urls = [u for u in urls if not any(skip in u for skip in ['/author/', '/tag/', '/category/', '#', '?'])]
                unique_urls = list(set(article_urls))
                
                print(f"✓ Найдено {len(unique_urls)} уникальных статей")
                all_urls.extend(unique_urls)
                
                # Показываем примеры
                for url in unique_urls[:3]:
                    slug = url.split('/')[-1]
                    print(f"  → .../{slug}")
            else:
                print(f"✗ Ошибка: {result}")
        else:
            print(f"✗ HTTP Error {response.status_code}")
    except Exception as e:
        print(f"✗ Исключение: {str(e)}")

print(f"\n📊 ИТОГО ПО LAMBDA LABS:")
print(f"Всего уникальных статей: {len(set(all_urls))}")