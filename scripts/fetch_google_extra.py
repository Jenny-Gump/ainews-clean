import requests
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

# Дополнительные разделы Google
google_sections = [
    ("Google Gemini", "https://blog.google/products/gemini/"),
    ("Google Research", "https://blog.google/technology/research/"),
    ("Google Developers", "https://blog.google/technology/developers/"),
    ("Google DeepMind", "https://blog.google/technology/google-deepmind/")
]

url = "https://api.firecrawl.dev/v1/scrape"
headers = {
    "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}",
    "Content-Type": "application/json"
}

all_urls = []

for name, section_url in google_sections:
    print(f"\nПроверяю {name}...")
    print(f"URL: {section_url}")
    
    data = {
        "url": section_url,
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
                # Ищем ссылки на статьи
                pattern = r'https://blog\.google/[^)"\s]+'
                urls = re.findall(pattern, markdown)
                # Фильтруем только статьи (не навигацию)
                article_urls = [u for u in urls if not any(skip in u for skip in ['/page/', '/tag/', '/category/', '#', 'newsletter', 'subscribe'])]
                unique_urls = list(set(article_urls))
                
                print(f"✓ Найдено {len(unique_urls)} уникальных статей")
                all_urls.extend(unique_urls)
                
                # Показываем примеры
                for url in unique_urls[:3]:
                    print(f"  → {url}")
            else:
                print(f"✗ Ошибка: {result}")
        else:
            print(f"✗ HTTP Error {response.status_code}")
    except Exception as e:
        print(f"✗ Исключение: {str(e)}")

print(f"\n📊 ИТОГО ПО GOOGLE:")
print(f"Всего уникальных статей: {len(set(all_urls))}")