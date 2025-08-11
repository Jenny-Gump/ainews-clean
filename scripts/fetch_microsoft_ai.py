import requests
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

# Microsoft AI News
source_url = "https://news.microsoft.com/source/topics/ai/"

print(f"Получаю контент с Microsoft AI News...")
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
        with open("content_microsoft_ai.md", "w") as f:
            f.write(markdown)
        
        print(f"✓ Контент сохранен в content_microsoft_ai.md")
        print(f"  Размер: {len(markdown)} символов")
        
        # Проверяем наличие статей
        if "news.microsoft.com" in markdown:
            print("✓ Найдены ссылки на статьи")
    else:
        print(f"✗ Ошибка API: {result}")
else:
    print(f"✗ HTTP Error {response.status_code}")