import re
import os

results = {}

# Google AI Blog
if os.path.exists("content_google_ai_blog.md"):
    with open("content_google_ai_blog.md", "r") as f:
        content = f.read()
    urls = re.findall(r'https://blog\.google/technology/ai/[^)"\s]+', content)
    results["Google AI Blog"] = len(set(urls))

# DeepMind
if os.path.exists("content_deepmind.md"):
    with open("content_deepmind.md", "r") as f:
        content = f.read()
    urls = re.findall(r'https://deepmind\.google/discover/blog/[^)"\s]+', content)
    results["DeepMind"] = len(set(urls))

# Microsoft AI
if os.path.exists("content_microsoft_ai.md"):
    with open("content_microsoft_ai.md", "r") as f:
        content = f.read()
    urls = re.findall(r'https://news\.microsoft\.com/[^)"\s]+', content)
    results["Microsoft AI"] = len(set(urls))

# MIT News
if os.path.exists("content_mit_news_ai.md"):
    with open("content_mit_news_ai.md", "r") as f:
        content = f.read()
    urls = re.findall(r'https://news\.mit\.edu/[^)"\s]+', content)
    results["MIT News AI"] = len(set(urls))

# AWS AI
if os.path.exists("content_aws_ai_blog.md"):
    with open("content_aws_ai_blog.md", "r") as f:
        content = f.read()
    urls = re.findall(r'https://aws\.amazon\.com/[^)"\s]+', content)
    # Фильтруем только блог статьи
    blog_urls = [u for u in urls if '/blogs/' in u or '/blog/' in u]
    results["AWS AI Blog"] = len(set(blog_urls))

print("📊 РЕЗУЛЬТАТЫ BATCH 2:")
print("=" * 60)
total = 0
for source, count in results.items():
    print(f"• {source}: {count} статей найдено")
    total += count
print(f"\n✅ ВСЕГО: {total} статей")