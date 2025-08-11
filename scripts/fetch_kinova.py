import requests
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

# Kinova Robotics Press
source_url = "https://www.kinovarobotics.com/press"

print(f"Получаю контент с Kinova Robotics Press...")
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
            with open("content_kinova.md", "w") as f:
                f.write(markdown)
            
            print(f"✓ Контент сохранен в content_kinova.md")
            print(f"  Размер: {len(markdown)} символов")
            
            # Проверяем наличие статей - пробуем разные паттерны
            import re
            patterns = [
                r'https://www\.kinovarobotics\.com/press/[^)\s"]+',
                r'https://www\.kinovarobotics\.com/[^)\s"]+/news[^)\s"]*',
                r'href="([^"]+)"[^>]*>.*?Press Release',
                r'\[.*?\]\((https://[^)]+)\)'  # Общий паттерн для любых ссылок
            ]
            
            all_urls = set()
            for pattern in patterns:
                found = re.findall(pattern, markdown, re.IGNORECASE)
                all_urls.update(found)
            
            # Фильтруем только релевантные
            press_urls = [u for u in all_urls if 'kinovarobotics.com' in u and any(x in u.lower() for x in ['press', 'news', 'article', 'blog'])]
            
            print(f"✓ Найдено {len(press_urls)} пресс-релизов")
            print(f"  Всего ссылок найдено: {len(all_urls)}")
            
            if press_urls:
                print("Примеры пресс-релизов:")
                for url in press_urls[:3]:
                    print(f"  → {url}")
            elif all_urls:
                print("Найдены другие ссылки (не пресс-релизы):")
                for url in list(all_urls)[:3]:
                    print(f"  → {url}")
        else:
            print(f"✗ Ошибка API: {result}")
    else:
        print(f"✗ HTTP Error {response.status_code}")
except Exception as e:
    print(f"✗ Исключение: {str(e)}")