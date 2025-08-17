#!/usr/bin/env python3
"""Скрипт для исправления проблем с тегами"""

import requests
import time

# WordPress API настройки
WP_URL = "https://ailynx.ru/wp-json/wp/v2"
WP_USER = "admin"
WP_PASS = "tE85 PFT4 Ghq9 nl26 nQlt gBnG"

# 1. УДАЛЕНИЕ ДУБЛИКАТОВ
print("🗑️ УДАЛЕНИЕ ДУБЛИКАТОВ ТЕГОВ")
print("-" * 50)

# ID тегов для удаления (дубликаты)
duplicates_to_delete = [
    303,  # Джеффри Хинтон (оставляем 75)
    293,  # Илон Маск (оставляем 43)
    291,  # Китай (оставляем 245)
    288,  # Сэм Альтман (оставляем 42)
    289,  # Sam Altman (еще один дубликат)
    286,  # Солнечное затмение (нерелевантный)
]

for tag_id in duplicates_to_delete:
    response = requests.delete(
        f"{WP_URL}/tags/{tag_id}?force=true",
        auth=(WP_USER, WP_PASS)
    )
    if response.status_code == 200:
        print(f"✅ Удален тег ID {tag_id}")
    else:
        print(f"❌ Ошибка удаления тега ID {tag_id}: {response.status_code}")
    time.sleep(0.5)

print("\n" + "=" * 50)

# 2. ДОБАВЛЕНИЕ ОПИСАНИЙ
print("\n📝 ДОБАВЛЕНИЕ ОПИСАНИЙ ДЛЯ ТЕГОВ")
print("-" * 50)

# Описания для тегов
tag_descriptions = {
    "AGI": "Artificial General Intelligence - искусственный общий интеллект, способный выполнять любые интеллектуальные задачи как человек",
    "BERT": "Языковая модель от Google для глубокого понимания контекста в естественном языке",
    "Blue Origin": "Аэрокосмическая компания Джеффа Безоса, разрабатывающая технологии для космического туризма",
    "Booking.com": "Крупнейший мировой сервис онлайн-бронирования отелей и путешествий",
    "ByteDance": "Китайская технологическая компания, создатель TikTok и AI-платформ",
    "Character.AI": "Платформа для создания и общения с AI-персонажами на основе нейросетей",
    "Chrome": "Веб-браузер от Google с интегрированными AI-функциями",
    "Databricks": "Унифицированная платформа для обработки больших данных и машинного обучения",
    "Dropbox": "Облачное хранилище с AI-функциями для организации и поиска файлов",
    "Dроны": "Беспилотные летательные аппараты с AI-управлением",
    "Expedia": "Международная платформа для планирования путешествий с AI-рекомендациями",
    "GeForce NOW": "Облачный игровой сервис от NVIDIA с поддержкой AI-технологий",
    "GoPro": "Производитель экшн-камер с AI-обработкой видео",
    "Kaspersky": "Российская компания по кибербезопасности с AI-защитой",
    "MIT": "Массачусетский технологический институт - ведущий центр исследований ИИ",
    "Meta": "Материнская компания Facebook, Instagram, WhatsApp, разработчик метавселенной",
    "Nscale": "Платформа для эффективного масштабирования и развертывания ML-моделей",
    "Reinforcement learning": "Обучение с подкреплением - метод машинного обучения через взаимодействие со средой",
    "Starlink": "Глобальная спутниковая сеть интернета от SpaceX",
    "Tencent": "Китайский технологический гигант, создатель WeChat и игровых платформ",
    "TensorFlow": "Open-source фреймворк от Google для машинного обучения и нейросетей",
    "VR": "Виртуальная реальность - технология погружения в цифровые миры",
    "YouTube": "Видеохостинг Google с AI-алгоритмами рекомендаций и модерации",
    "iOS": "Мобильная операционная система Apple с интегрированными AI-функциями",
    "ИИ": "Искусственный интеллект - технология создания интеллектуальных машин и программ"
}

# Получаем все теги для поиска по имени
response = requests.get(
    f"{WP_URL}/tags?per_page=100",
    auth=(WP_USER, WP_PASS)
)
all_tags = response.json()

# Добавляем теги со второй страницы
response2 = requests.get(
    f"{WP_URL}/tags?per_page=100&page=2",
    auth=(WP_USER, WP_PASS)
)
if response2.status_code == 200:
    all_tags.extend(response2.json())

# Добавляем теги с третьей страницы
response3 = requests.get(
    f"{WP_URL}/tags?per_page=100&page=3",
    auth=(WP_USER, WP_PASS)
)
if response3.status_code == 200:
    all_tags.extend(response3.json())

# Обновляем описания
updated = 0
for tag_name, description in tag_descriptions.items():
    # Ищем тег по имени
    tag = next((t for t in all_tags if t['name'] == tag_name), None)
    
    if tag:
        # Обновляем описание
        response = requests.post(
            f"{WP_URL}/tags/{tag['id']}",
            auth=(WP_USER, WP_PASS),
            json={"description": description}
        )
        
        if response.status_code == 200:
            print(f"✅ Обновлен тег '{tag_name}' (ID: {tag['id']})")
            updated += 1
        else:
            print(f"❌ Ошибка обновления '{tag_name}': {response.status_code}")
    else:
        print(f"⚠️ Тег '{tag_name}' не найден")
    
    time.sleep(0.5)

print("\n" + "=" * 50)
print(f"✅ ИТОГИ:")
print(f"  • Удалено дубликатов: {len(duplicates_to_delete)}")
print(f"  • Добавлено описаний: {updated}")
print("🎉 Исправление завершено!")