import json
import re
from datetime import datetime

# Загружаем конфигурацию
with open("../services/source_extractors.json", "r") as f:
    config = json.load(f)

results = {
    "timestamp": datetime.now().isoformat(),
    "total_sources_checked": 22,
    "sources": []
}

# Обрабатываем каждый протестированный источник
tested_sources = [
    ("anthropic", "content_anthropic.md"),
    ("ai21", "content_ai21.md"),
    ("openai_tracking", "content_openai_tracking.md"),
    ("huggingface", "content_huggingface.md"),
    ("cohere", "content_cohere.md"),
    ("stability", "content_stability.md"),
    ("elevenlabs", "content_elevenlabs.md"),
    ("cerebras", "content_cerebras.md"),
    ("mistral", "content_mistral.md"),
    ("together", "content_together.md"),
    ("perplexity", "content_perplexity.md"),
    ("runway", "content_runway.md"),
    ("scale", "content_scale.md"),
    ("crusoe", "content_crusoe.md"),
    ("lambda", "content_lambda.md"),
    ("c3ai", "content_c3ai.md"),
    ("instabase", "content_instabase.md"),
    ("google_ai_blog", "content_google_combined.md"),
    ("deepmind", "content_deepmind.md"),
    ("microsoft_ai_news", "content_microsoft_ai.md"),
    ("mit_news", "content_mit_news_ai.md"),
    ("aws_ai", "content_aws_ai_blog.md")
]

for source_id, content_file in tested_sources:
    if source_id not in config["extractors"]:
        continue
    
    source_config = config["extractors"][source_id]
    if source_config.get("status") != "tested_real":
        continue
    
    try:
        with open(content_file, "r") as f:
            content = f.read()
    except:
        continue
    
    # Извлекаем URL используя паттерны
    urls = set()
    for pattern in source_config.get("patterns", []):
        # Упрощаем паттерн для поиска
        if "https://" in pattern:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    # Берем URL из кортежа
                    url = next((m for m in match if "https://" in m), None)
                    if url:
                        urls.add(url)
                elif "https://" in match:
                    urls.add(match)
    
    # Фильтруем по exclude_urls
    filtered_urls = []
    for url in urls:
        skip = False
        for exclude in source_config.get("exclude_urls", []):
            if exclude in url:
                skip = True
                break
        if not skip:
            filtered_urls.append(url)
    
    results["sources"].append({
        "id": source_id,
        "name": source_config["name"],
        "url": source_config["url"],
        "urls_found": len(filtered_urls),
        "sample_urls": filtered_urls[:5],
        "all_urls": filtered_urls
    })

# Сохраняем результаты
output_file = "/Users/skynet/Desktop/parsed_urls_results.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"✅ Результаты сохранены в: {output_file}")
print(f"\n📊 СТАТИСТИКА:")
print(f"Проверено источников: {len(results['sources'])}")
total_urls = sum(s["urls_found"] for s in results["sources"])
print(f"Всего найдено URL: {total_urls}")
print("\nПо источникам:")
for source in results["sources"]:
    print(f"  • {source['name']}: {source['urls_found']} статей")
