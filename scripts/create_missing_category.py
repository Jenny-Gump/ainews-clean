#!/usr/bin/env python3
"""
Create missing category
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config

config = Config()
auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)

# Сначала найдем ID категории "Новости"
response = requests.get(f"{config.wordpress_api_url}/categories", auth=auth, params={'per_page': 100})
categories = response.json()
news_id = None
for cat in categories:
    if cat['name'] == 'Новости':
        news_id = cat['id']
        break

if news_id:
    # Создаем категорию "Люди"
    data = {
        'name': 'Люди',
        'slug': 'people',  # Используем английский slug
        'description': 'Истории людей, создающих будущее искусственного интеллекта. Интервью с исследователями, предпринимателями и визионерами индустрии.\n\nПортреты лидеров мнений: от пионеров машинного обучения до молодых стартаперов. Карьерные истории, образовательные пути и вдохновляющие примеры успеха в мире AI.',
        'parent': news_id
    }
    
    response = requests.post(f"{config.wordpress_api_url}/categories", json=data, auth=auth)
    
    if response.status_code == 201:
        print(f"✅ Категория 'Люди' создана успешно!")
    else:
        print(f"❌ Ошибка: {response.status_code} - {response.text}")
else:
    print("❌ Не найдена родительская категория 'Новости'")