import requests
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

# OpenEvidence Announcements
source_url = "https://www.openevidence.com/announcements"

print(f"Получаю контент с OpenEvidence Announcements...")
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
            with open("content_openevidence.md", "w") as f:
                f.write(markdown)
            
            print(f"✓ Контент сохранен в content_openevidence.md")
            print(f"  Размер: {len(markdown)} символов")
            
            # Проверяем наличие анонсов - пробуем разные паттерны
            import re
            patterns = [
                r'https://www\.openevidence\.com/announcements/[^)\s"]+',
                r'href="([^"]+/announcements/[^"]+)"',
                r'\[.*?\]\((https://[^)]+)\)'  # Общий паттерн для любых ссылок
            ]
            
            all_urls = set()
            for pattern in patterns:
                found = re.findall(pattern, markdown, re.IGNORECASE)
                all_urls.update(found)
            
            # Фильтруем только релевантные
            announcement_urls = [u for u in all_urls if 'openevidence.com' in u and '/announcements/' in u and u != source_url]
            
            print(f"✓ Найдено {len(announcement_urls)} анонсов")
            print(f"  Всего ссылок найдено: {len(all_urls)}")
            
            if announcement_urls:
                print("Примеры анонсов:")
                for url in announcement_urls[:5]:
                    print(f"  → {url}")
            elif all_urls:
                print("Найдены другие ссылки:")
                for url in list(all_urls)[:5]:
                    if 'http' in url:
                        print(f"  → {url}")
            
            # Проверяем контент на наличие заголовков или дат
            if 'announcement' in markdown.lower() or 'news' in markdown.lower():
                print("✓ Страница содержит контент об анонсах")
                
            # Ищем заголовки
            headings = re.findall(r'#{1,3}\s+(.+)', markdown)
            if headings:
                print(f"\nНайдено заголовков: {len(headings)}")
                for heading in headings[:5]:
                    print(f"  • {heading}")
                    
        else:
            print(f"✗ Ошибка API: {result}")
    else:
        print(f"✗ HTTP Error {response.status_code}")
except Exception as e:
    print(f"✗ Исключение: {str(e)}")