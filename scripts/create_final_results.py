import json
import re
from datetime import datetime
import os

# Загружаем конфигурацию
with open("../services/source_extractors.json", "r") as f:
    config = json.load(f)

results = {
    "timestamp": datetime.now().isoformat(),
    "total_sources": 47,
    "tested_sources": 0,
    "successful_sources": [],
    "failed_sources": [],
    "total_urls_found": 0,
    "source_details": []
}

# Список content файлов для протестированных источников
content_files = {
    "anthropic": "content_anthropic.md",
    "ai21": "content_ai21.md",
    "openai_tracking": "content_openai_tracking.md",
    "huggingface": "content_huggingface.md",
    "cohere": "content_cohere.md",
    "stability": "content_stability.md",
    "elevenlabs": "content_elevenlabs.md",
    "cerebras": "content_cerebras.md",
    "mistral": "content_mistral.md",
    "together": "content_together.md",
    "perplexity": "content_perplexity.md",
    "runway": "content_runway.md",
    "scale": "content_scale.md",
    "crusoe": "content_crusoe.md",
    "lambda": "content_lambda.md",
    "c3ai": "content_c3ai.md",
    "instabase": "content_instabase.md",
    "google_ai_blog": "content_google_combined.md",
    "deepmind": "content_deepmind.md",
    "microsoft_ai_news": "content_microsoft_ai.md",
    "mit_news": "content_mit_news_ai.md",
    "aws_ai": "content_aws_ai_blog.md",
    "tempus": "content_tempus.md",
    "writer": "content_writer.md",
    "stanford_ai": "content_stanford_ai.md",
    "databricks_tracking": "content_databricks.md",
    "google_research": "content_google_research.md",
    "google_cloud_ai": "content_google_cloud_ai.md",
    "suno": "content_suno.md",
    "waymo": "content_waymo.md",
    "abb_robotics": "content_abb_robotics.md",
    "pathai": "content_pathai.md",
    "augmedix": "content_augmedix.md",
    "b12": "content_b12.md",
    "appzen": "content_appzen.md",
    "alpha_sense": "content_alpha_sense.md",
    "mindfoundry": "content_mindfoundry.md",
    "nscale": "content_nscale.md",
    "audioscenic": "content_audioscenic.md",
    "soundhound": "content_soundhound.md",
    "uizard": "content_uizard.md"
}

# Обрабатываем каждый источник
for source_id, source_config in config["extractors"].items():
    if source_config.get("status") == "tested_real":
        results["tested_sources"] += 1
        
        # Если есть content файл
        if source_id in content_files and os.path.exists(content_files[source_id]):
            try:
                with open(content_files[source_id], "r") as f:
                    content = f.read()
                
                # Извлекаем URL используя паттерны
                urls = set()
                for pattern in source_config.get("patterns", []):
                    if "https://" in pattern:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if isinstance(match, tuple):
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
                
                if filtered_urls:
                    results["successful_sources"].append(source_id)
                    results["total_urls_found"] += len(filtered_urls)
                    
                    results["source_details"].append({
                        "id": source_id,
                        "name": source_config["name"],
                        "url": source_config["url"],
                        "urls_found": len(filtered_urls),
                        "sample_urls": filtered_urls[:3]
                    })
                else:
                    results["failed_sources"].append(source_id)
            except:
                pass

# Сортируем по количеству найденных URL
results["source_details"].sort(key=lambda x: x["urls_found"], reverse=True)

# Сохраняем результаты
output_file = "/Users/skynet/Desktop/AI_NEWS_FINAL_RESULTS.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"✅ ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ")
print(f"=" * 50)
print(f"📊 ОБЩАЯ СТАТИСТИКА:")
print(f"  • Всего источников: {results['total_sources']}")
print(f"  • Протестировано: {results['tested_sources']} ({results['tested_sources']*100//47}%)")
print(f"  • Успешных: {len(results['successful_sources'])}")
print(f"  • Неудачных: {len(results['failed_sources'])}")
print(f"  • Всего найдено URL: {results['total_urls_found']}")
print(f"\n🏆 ТОП-10 ИСТОЧНИКОВ ПО КОЛИЧЕСТВУ СТАТЕЙ:")
for i, source in enumerate(results["source_details"][:10], 1):
    print(f"  {i}. {source['name']}: {source['urls_found']} статей")

print(f"\n❌ ИСТОЧНИКИ БЕЗ СТАТЕЙ:")
for source_id in results["failed_sources"]:
    source_name = config["extractors"][source_id]["name"]
    print(f"  • {source_name} ({source_id})")

print(f"\n📁 Результаты сохранены в: {output_file}")