import requests
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

# Проверим только пагинацию
test_url = "https://lambda.ai/blog?page=2"

print(f"Проверяю Lambda Labs с пагинацией...")
print(f"URL: {test_url}")

url = "https://api.firecrawl.dev/v1/scrape"
headers = {
    "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "url": test_url,
    "formats": ["markdown"],
    "timeout": 30000  # Меньший таймаут
}

try:
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            markdown = result.get("data", {}).get("markdown", "")
            
            # Проверяем, есть ли контент
            print(f"✓ Получено {len(markdown)} символов")
            
            # Ищем статьи
            import re
            pattern = r'https://lambda\.ai/blog/[^)"\s]+'
            urls = re.findall(pattern, markdown)
            article_urls = [u for u in urls if '/author/' not in u and '/tag/' not in u]
            unique_urls = list(set(article_urls))
            
            print(f"✓ Найдено {len(unique_urls)} статей")
            
            # Сравниваем с первой страницей
            with open("content_lambda.md", "r") as f:
                page1 = f.read()
            
            page1_urls = re.findall(pattern, page1)
            page1_articles = [u for u in page1_urls if '/author/' not in u and '/tag/' not in u]
            
            # Есть ли новые статьи?
            new_articles = set(unique_urls) - set(page1_articles)
            if new_articles:
                print(f"✓ Новых статей на странице 2: {len(new_articles)}")
                for url in list(new_articles)[:3]:
                    print(f"  → {url.split('/')[-1]}")
            else:
                print("✗ Страница 2 содержит те же статьи что и страница 1")
                
        else:
            print(f"✗ Ошибка API: {result}")
    else:
        print(f"✗ HTTP Error {response.status_code}")
except Exception as e:
    print(f"✗ Исключение: {str(e)}")