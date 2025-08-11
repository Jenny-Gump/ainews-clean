import requests
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

url = "https://api.firecrawl.dev/v1/scrape"
headers = {
    "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}",
    "Content-Type": "application/json"
}
data = {
    "url": "https://lambda.ai/blog",
    "formats": ["markdown"],
    "timeout": 60000
}

print("Скачиваю Lambda Labs Blog...")
response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        markdown = result.get("data", {}).get("markdown", "")
        with open("content_lambda.md", "w") as f:
            f.write(markdown)
        print(f"✓ Контент сохранен: {len(markdown)} символов")
        
        # Быстрый анализ
        if 'lambda.ai/blog' in markdown or 'lambdalabs.com' in markdown:
            print("✓ Найдены URL блога")
    else:
        print(f"✗ Ошибка: {result}")
else:
    print(f"✗ HTTP Error {response.status_code}: {response.text}")