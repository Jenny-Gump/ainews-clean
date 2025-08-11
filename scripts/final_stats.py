import json

# Загружаем результаты
with open("/Users/skynet/Desktop/parsed_urls_results.json", "r") as f:
    results = json.load(f)

print("📊 ФИНАЛЬНАЯ СТАТИСТИКА ПАРСИНГА")
print("=" * 70)
print(f"Дата проверки: {results['timestamp']}")
print(f"Источников проверено: {results['total_sources_checked']}")
print(f"Источников с данными: {len(results['sources'])}")

total_urls = 0
top_sources = []

print("\n📈 ТОП-10 ИСТОЧНИКОВ ПО КОЛИЧЕСТВУ URL:")
print("-" * 70)

# Сортируем по количеству URL
sorted_sources = sorted(results['sources'], key=lambda x: x['urls_found'], reverse=True)

for i, source in enumerate(sorted_sources[:10], 1):
    total_urls += source['urls_found']
    print(f"{i:2}. {source['name']:<25} | {source['urls_found']:3} статей")
    
    # Показываем примеры URL для топ-3
    if i <= 3 and source['sample_urls']:
        for j, url in enumerate(source['sample_urls'][:2], 1):
            # Извлекаем только последнюю часть URL
            url_slug = url.split('/')[-1][:50]
            print(f"     → {url_slug}...")

print("\n📉 ИСТОЧНИКИ С МАЛЫМ КОЛИЧЕСТВОМ URL:")
print("-" * 70)
for source in sorted_sources[-5:]:
    print(f"  • {source['name']:<25} | {source['urls_found']:3} статей")
    total_urls += source['urls_found'] if source not in sorted_sources[:10] else 0

# Считаем общее количество URL
total_all = sum(s['urls_found'] for s in results['sources'])

print("\n✅ ИТОГОВЫЕ ПОКАЗАТЕЛИ:")
print("-" * 70)
print(f"Всего найдено URL: {total_all}")
print(f"Среднее на источник: {total_all // len(results['sources']) if results['sources'] else 0} статей")

# Проверяем качество данных
print("\n🔍 КАЧЕСТВО ДАННЫХ:")
print("-" * 70)
sources_with_many = len([s for s in results['sources'] if s['urls_found'] > 20])
sources_with_few = len([s for s in results['sources'] if s['urls_found'] < 5])
print(f"Источников с >20 URL: {sources_with_many}")
print(f"Источников с <5 URL: {sources_with_few}")

# Проверяем конфигурацию
with open("../services/source_extractors.json", "r") as f:
    config = json.load(f)

tested_real = sum(1 for e in config['extractors'].values() if e.get('status') == 'tested_real')
configured = sum(1 for e in config['extractors'].values() if e.get('status') == 'configured')

print(f"\nСтатус в конфигурации:")
print(f"  • tested_real: {tested_real} источников")
print(f"  • configured: {configured} источников")
print(f"  • всего: {len(config['extractors'])} источников")