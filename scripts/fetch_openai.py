import requests
import json
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.config import Config

config = Config()

# Firecrawl scrape request
url = "https://api.firecrawl.dev/v1/scrape"
headers = {
    "Authorization": f"Bearer {config.FIRECRAWL_API_KEY}",
    "Content-Type": "application/json"
}
data = {
    "url": "https://openai.com/news/",
    "formats": ["markdown"],
    "timeout": 60000
}

print("Fetching OpenAI news page...")
response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    result = response.json()
    if result.get("success"):
        markdown = result.get("data", {}).get("markdown", "")
        # Save to file
        with open("content_openai_tracking.md", "w") as f:
            f.write(markdown)
        print(f"✓ Content saved: {len(markdown)} characters")
        # Show first 2000 chars
        print("\n=== FIRST 2000 CHARACTERS ===")
        print(markdown[:2000])
    else:
        print(f"✗ Failed: {result}")
else:
    print(f"✗ HTTP Error {response.status_code}: {response.text}")
