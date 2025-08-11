import requests
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

sources = [
    ("Google AI Blog", "https://blog.google/technology/ai/"),
    ("DeepMind", "https://deepmind.google/discover/blog/"),
    ("Microsoft AI", "https://news.microsoft.com/source/topics/ai/"),
    ("MIT News AI", "https://news.mit.edu/topic/artificial-intelligence2"),
    ("AWS AI Blog", "https://aws.amazon.com/ai/")
]

for name, source_url in sources:
    print(f"\n{'='*60}")
    print(f"Скачиваю {name}...")
    
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
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                markdown = result.get("data", {}).get("markdown", "")
                filename = f"content_{name.lower().replace(' ', '_').replace('-', '_')}.md"
                with open(filename, "w") as f:
                    f.write(markdown)
                print(f"✓ {name}: {len(markdown)} символов сохранено в {filename}")
            else:
                print(f"✗ {name}: Ошибка - {result}")
        else:
            print(f"✗ {name}: HTTP Error {response.status_code}")
    except Exception as e:
        print(f"✗ {name}: Исключение - {str(e)}")