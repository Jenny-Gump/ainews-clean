import requests
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

# Doosan Robotics News
source_url = "https://www.doosanrobotics.com/en/about/promotion/news/"

print(f"Получаю контент с Doosan Robotics News...")
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
            with open("content_doosan.md", "w") as f:
                f.write(markdown)
            
            print(f"✓ Контент сохранен в content_doosan.md")
            print(f"  Размер: {len(markdown)} символов")
            
            # Проверяем наличие статей - пробуем разные паттерны
            import re
            patterns = [
                r'https://www\.doosanrobotics\.com/en/about/promotion/news/[^)\s"]+',
                r'https://www\.doosanrobotics\.com/[^)\s"]+/news[^)\s"]*',
                r'href="([^"]+news[^"]+)"',
                r'\[.*?\]\((https://[^)]+)\)'  # Общий паттерн для любых ссылок
            ]
            
            all_urls = set()
            for pattern in patterns:
                found = re.findall(pattern, markdown, re.IGNORECASE)
                all_urls.update(found)
            
            # Фильтруем только релевантные
            news_urls = [u for u in all_urls if 'doosanrobotics.com' in u and any(x in u.lower() for x in ['news', 'press', 'article', 'promotion'])]
            
            print(f"✓ Найдено {len(news_urls)} новостей")
            print(f"  Всего ссылок найдено: {len(all_urls)}")
            
            if news_urls:
                print("Примеры новостей:")
                for url in news_urls[:5]:
                    print(f"  → {url}")
            elif all_urls:
                print("Найдены другие ссылки (не новости):")
                for url in list(all_urls)[:5]:
                    if 'http' in url:
                        print(f"  → {url}")
            
            # Проверяем контент на наличие заголовков статей
            article_titles = re.findall(r'###?\s+(.+)', markdown)
            if article_titles:
                print(f"\nНайдено {len(article_titles)} заголовков:")
                for title in article_titles[:5]:
                    print(f"  • {title}")
                    
        else:
            print(f"✗ Ошибка API: {result}")
    else:
        print(f"✗ HTTP Error {response.status_code}")
except Exception as e:
    print(f"✗ Исключение: {str(e)}")