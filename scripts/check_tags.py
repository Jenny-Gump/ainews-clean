#!/usr/bin/env python3
"""Скрипт для проверки тегов на дубли и отсутствующие описания"""

import json
from collections import Counter

# Загружаем все теги
all_tags = []
for i in range(1, 4):
    try:
        with open(f'/tmp/tags_page{i}.json', 'r') as f:
            tags = json.load(f)
            if tags:
                all_tags.extend(tags)
    except:
        pass

print(f"📊 Всего тегов на сайте: {len(all_tags)}")
print("=" * 60)

# Проверка на дубли по имени
names = [tag['name'] for tag in all_tags]
name_counts = Counter(names)
duplicates = {name: count for name, count in name_counts.items() if count > 1}

if duplicates:
    print("\n❌ НАЙДЕНЫ ДУБЛИ ТЕГОВ:")
    print("-" * 40)
    for name, count in duplicates.items():
        print(f"  • {name}: {count} раз")
        # Найдем ID дублей
        duplicate_tags = [tag for tag in all_tags if tag['name'] == name]
        for tag in duplicate_tags:
            print(f"    - ID: {tag['id']}, Slug: {tag['slug']}")
else:
    print("\n✅ Дублей тегов не найдено")

# Проверка на отсутствующие описания
tags_without_description = []
for tag in all_tags:
    if not tag.get('description') or tag['description'].strip() == '':
        tags_without_description.append(tag)

print(f"\n📝 ТЕГИ БЕЗ ОПИСАНИЯ: {len(tags_without_description)}")
if tags_without_description:
    print("-" * 40)
    # Сортируем по имени для удобства
    tags_without_description.sort(key=lambda x: x['name'])
    for tag in tags_without_description[:50]:  # Показываем первые 50
        print(f"  • {tag['name']} (ID: {tag['id']}, Slug: {tag['slug']})")
    
    if len(tags_without_description) > 50:
        print(f"  ... и еще {len(tags_without_description) - 50} тегов")

# Проверка на похожие имена (возможные дубли)
print("\n🔍 ПОХОЖИЕ ТЕГИ (возможные дубли):")
print("-" * 40)
similar_found = False
for i, tag1 in enumerate(all_tags):
    for tag2 in all_tags[i+1:]:
        name1 = tag1['name'].lower().replace(' ', '').replace('-', '').replace('.', '')
        name2 = tag2['name'].lower().replace(' ', '').replace('-', '').replace('.', '')
        # Проверяем очень похожие названия
        if name1 == name2 and tag1['name'] != tag2['name']:
            print(f"  • '{tag1['name']}' и '{tag2['name']}'")
            similar_found = True
        # Проверяем вариации типа GPT-4o и GPT-4.0
        elif (name1.replace('gpt4o', 'gpt40') == name2.replace('gpt4o', 'gpt40') or
              name1.replace('gpt5', 'gpt50') == name2.replace('gpt5', 'gpt50')):
            if tag1['name'] != tag2['name']:
                print(f"  • '{tag1['name']}' и '{tag2['name']}'")
                similar_found = True

if not similar_found:
    print("  Похожих тегов не найдено")

# Статистика по категориям тегов
print("\n📈 СТАТИСТИКА ПО КАТЕГОРИЯМ:")
print("-" * 40)
categories = {
    'Компании': ['OpenAI', 'Google', 'Meta', 'Microsoft', 'Anthropic', 'xAI', 'DeepSeek', 'Alibaba', 'NVIDIA'],
    'Модели GPT': ['GPT-', 'o1', 'o3', 'o4'],
    'Модели Claude': ['Claude'],
    'Модели Gemini': ['Gemini'],
    'Модели Llama': ['Llama', 'Nemotron'],
    'Модели Grok': ['Grok'],
    'Другие модели': ['Phi', 'Qwen', 'DeepSeek', 'Magistral', 'Kimi']
}

for category, keywords in categories.items():
    count = sum(1 for tag in all_tags if any(kw in tag['name'] for kw in keywords))
    print(f"  {category}: {count}")

print("\n" + "=" * 60)
print("✅ Проверка завершена!")