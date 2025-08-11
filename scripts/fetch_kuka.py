import requests
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

# KUKA Robotics News
source_url = "https://www.kuka.com/en-us/company/press/news"

print(f"Получаю контент с KUKA Robotics News...")
print(f"URL: {source_url}")

url = "https://api.firecrawl.dev/v1/scrape"
headers = {
    "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "url": source_url,
    "formats": ["markdown"],
    "timeout": 30000
}

try:
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            markdown = result.get("data", {}).get("markdown", "")
            
            # Сохраняем контент
            with open("content_kuka.md", "w") as f:
                f.write(markdown)
            
            print(f"✓ Контент сохранен в content_kuka.md")
            print(f"  Размер: {len(markdown)} символов")
            
            # Проверяем наличие статей
            import re
            patterns = [
                r'https://www\.kuka\.com/en-us/company/press/news/[^)\s"]+',
                r'https://www\.kuka\.com/[^)\s"]+/press-releases/[^)\s"]+'
            ]
            
            urls = set()
            for pattern in patterns:
                found = re.findall(pattern, markdown)
                urls.update(found)
            
            unique_urls = list(urls)
            
            print(f"✓ Найдено {len(unique_urls)} уникальных статей")
            if unique_urls:
                print("Примеры:")
                for url in unique_urls[:3]:
                    print(f"  → ...{url[-50:]}")
        else:
            print(f"✗ Ошибка API: {result}")
    else:
        print(f"✗ HTTP Error {response.status_code}")
except Exception as e:
    print(f"✗ Исключение: {str(e)}")