#!/usr/bin/env python3
"""
Add Meta Descriptions to Categories
Добавление мета-описаний к категориям через custom fields
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
import time

# Мета-описания для категорий
META_DESCRIPTIONS = {
    3: "Актуальные новости больших языковых моделей (LLM) - GPT, Claude, Gemini. Обзоры, сравнения и анализ развития AI технологий обработки текста.",  # LLM
    4: "Новости машинного обучения и нейронных сетей. Алгоритмы, исследования, практические применения ML в бизнесе и науке.",  # Машинное обучение
    5: "Новости AI техники и железа: GPU, TPU, чипы для нейросетей. Обзоры оборудования, облачных платформ и инструментов разработки.",  # AI Техника
    6: "AI в цифровом мире: интернет, соцсети, e-commerce, маркетинг. Персонализация, рекомендации, автоматизация digital-процессов.",  # Digital AI
    7: "AI в финансах: алготрейдинг, анализ рисков, банковская автоматизация. Инвестиции в AI-стартапы и финтех решения.",  # AI в Финансах
    8: "AI в науке: предсказание белков, поиск лекарств, автоматизация экспериментов. Машинное обучение в физике, химии, биологии.",  # AI в Науке
    9: "AI образование: курсы машинного обучения, сертификации, карьера в ИИ. Как стать AI-инженером и data scientist.",  # AI Образование
    10: "AI в различных индустриях: сельское хозяйство, медицина, производство, логистика. Умные города и промышленная автоматизация.",  # AI в Индустриях
    11: "Люди в AI индустрии: интервью с экспертами, истории успеха, карьерные пути. Этика ИИ и влияние на рынок труда.",  # Люди в AI
    2: "Последние новости искусственного интеллекта: прорывы в исследованиях, релизы AI-продуктов, тренды развития индустрии."  # AI Новости
}

def create_meta_plugin():
    """Создание плагина для мета-описаний"""
    plugin_code = '''<?php
/**
 * Plugin Name: Category Meta Descriptions
 * Description: Добавляет мета-описания для категорий
 * Version: 1.0
 */

if (!defined('ABSPATH')) {
    exit;
}

class CategoryMetaDescriptions {
    
    public function __construct() {
        add_action('rest_api_init', array($this, 'register_routes'));
        add_action('wp_head', array($this, 'add_category_meta_description'));
    }
    
    public function register_routes() {
        register_rest_route('category-meta/v1', '/update/(?P<id>\\d+)', array(
            'methods' => 'POST',
            'callback' => array($this, 'update_category_meta'),
            'permission_callback' => function() {
                return current_user_can('manage_categories');
            }
        ));
    }
    
    public function update_category_meta($request) {
        $category_id = intval($request['id']);
        $meta_description = sanitize_textarea_field($request->get_param('meta_description'));
        
        if (!$meta_description) {
            return new WP_Error('no_description', 'Мета-описание не указано');
        }
        
        // Сохраняем мета-описание
        update_term_meta($category_id, 'meta_description', $meta_description);
        
        return array(
            'success' => true,
            'category_id' => $category_id,
            'meta_description' => $meta_description,
            'message' => 'Мета-описание обновлено'
        );
    }
    
    public function add_category_meta_description() {
        if (is_category()) {
            $category_id = get_queried_object_id();
            $meta_description = get_term_meta($category_id, 'meta_description', true);
            
            if ($meta_description) {
                echo '<meta name="description" content="' . esc_attr($meta_description) . '">' . "\\n";
            }
        }
    }
}

new CategoryMetaDescriptions();
?>'''
    
    plugin_path = "/Users/skynet/Desktop/AI DEV/ainews-clean/wordpress-plugin/category-meta-descriptions.php"
    
    with open(plugin_path, 'w', encoding='utf-8') as f:
        f.write(plugin_code)
    
    print(f'✅ Создан плагин мета-описаний: {plugin_path}')
    return plugin_path

def add_meta_descriptions():
    """Добавление мета-описаний через плагин"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('📝 Добавление мета-описаний к категориям')
    print('=' * 50)
    
    success_count = 0
    
    for cat_id, meta_desc in META_DESCRIPTIONS.items():
        print(f'\n🔄 Обновляем категорию ID {cat_id}...')
        
        try:
            response = requests.post(
                f'https://ailynx.ru/wp-json/category-meta/v1/update/{cat_id}',
                json={'meta_description': meta_desc},
                auth=auth
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f'✅ Успешно: {meta_desc[:60]}...')
                success_count += 1
            else:
                print(f'❌ Ошибка {response.status_code}: {response.text[:100]}')
                
            time.sleep(0.2)
            
        except Exception as e:
            print(f'❌ Исключение: {e}')
    
    print(f'\n📊 Результат: {success_count}/{len(META_DESCRIPTIONS)} мета-описаний добавлено')
    return success_count > 0

def test_meta_plugin():
    """Тест плагина мета-описаний"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('\n🧪 Тестирование плагина мета-описаний...')
    
    # Тестируем на категории "Машинное обучение" (ID: 4)
    test_description = "ТЕСТ: Новости машинного обучения и нейронных сетей для проверки плагина."
    
    response = requests.post(
        'https://ailynx.ru/wp-json/category-meta/v1/update/4',
        json={'meta_description': test_description},
        auth=auth
    )
    
    if response.status_code == 200:
        result = response.json()
        print('✅ Плагин мета-описаний работает!')
        print(f'   Результат: {result.get("message")}')
        return True
    else:
        print(f'❌ Плагин не работает: {response.status_code}')
        print('💡 Нужно установить и активировать плагин category-meta-descriptions.php')
        return False

def main():
    print('📝 Добавление мета-описаний к категориям')
    print('=' * 60)
    
    # Создаем плагин
    plugin_path = create_meta_plugin()
    
    print('\n💡 Инструкции по установке:')
    print('1. Загрузите category-meta-descriptions.php в WordPress')
    print('2. Активируйте плагин "Category Meta Descriptions"')
    print('3. Запустите этот скрипт повторно для добавления мета-описаний')
    
    # Тестируем плагин
    print('\n🔍 Проверяем, активен ли плагин...')
    
    if test_meta_plugin():
        print('\n🚀 Плагин работает! Добавляем все мета-описания...')
        if add_meta_descriptions():
            print('\n✅ Мета-описания успешно добавлены!')
            print('\n🔗 Проверьте результат на страницах категорий:')
            print('   https://ailynx.ru/category/machine-learning/')
            print('   https://ailynx.ru/category/llm-news/')
            print('   https://ailynx.ru/category/ai-hardware/')
        else:
            print('\n❌ Ошибка при добавлении мета-описаний')
    else:
        print('\n⏳ Сначала установите и активируйте плагин')

if __name__ == "__main__":
    main()