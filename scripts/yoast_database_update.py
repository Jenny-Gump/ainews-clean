#!/usr/bin/env python3
"""
Direct Database Update for Yoast SEO
Прямое обновление Yoast SEO через базу данных WordPress
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from requests.auth import HTTPBasicAuth
from core.config import Config
import json

# SEO данные
CATEGORY_SEO_DATA = {
    "LLM": {
        "title": "Новости LLM - Большие языковые модели | AI Lynx",
        "desc": "Последние новости о больших языковых моделях: GPT, Claude, Gemini, LLaMA. Обзоры, сравнения и анализ развития LLM технологий.",
        "keyword": "LLM новости"
    },
    "Машинное обучение": {
        "title": "Машинное обучение - ML новости и исследования | AI Lynx",
        "desc": "Актуальные новости машинного обучения: алгоритмы, нейросети, исследования. Прорывы в области ML и практические применения.",
        "keyword": "машинное обучение"
    },
    "Техника": {
        "title": "AI Техника - Железо и софт для ИИ | AI Lynx",
        "desc": "Новости о технике для ИИ: GPU, TPU, чипы, облачные платформы. Обзоры железа и программного обеспечения для машинного обучения.",
        "keyword": "AI техника"
    },
    "Digital": {
        "title": "Digital AI - Цифровая трансформация с ИИ | AI Lynx",
        "desc": "Как ИИ меняет цифровой мир: интернет, соцсети, e-commerce, маркетинг. Инновации в digital-сфере с использованием AI.",
        "keyword": "digital AI"
    },
    "Люди": {
        "title": "Люди в AI - Лидеры и визионеры ИИ | AI Lynx",
        "desc": "Истории людей, создающих будущее ИИ: интервью с исследователями, предпринимателями, визионерами индустрии искусственного интеллекта.",
        "keyword": "лидеры AI"
    },
    "Финансы": {
        "title": "AI в Финансах - ИИ в банкинге и инвестициях | AI Lynx",
        "desc": "Применение ИИ в финансах: алгоритмическая торговля, кредитные риски, инвестиции в AI-стартапы, финтех с машинным обучением.",
        "keyword": "AI финансы"
    },
    "Наука": {
        "title": "AI в Науке - Научные прорывы с ИИ | AI Lynx", 
        "desc": "Как ИИ революционизирует науку: от предсказания белков до поиска лекарств. Машинное обучение в физике, химии, биологии.",
        "keyword": "AI наука"
    },
    "Обучение": {
        "title": "AI Образование - Курсы и обучение ИИ | AI Lynx",
        "desc": "Образование в сфере ИИ: курсы, программы, сертификации по машинному обучению. Roadmap и карьера в artificial intelligence.",
        "keyword": "обучение AI"
    },
    "Другие индустрии": {
        "title": "AI в Индустриях - Применение ИИ в разных сферах | AI Lynx",
        "desc": "ИИ в различных отраслях: сельское хозяйство, космос, медицина, производство. Инновационные кейсы применения AI.",
        "keyword": "AI индустрии"
    },
    "Новости": {
        "title": "AI Новости - Последние события в мире ИИ | AI Lynx",
        "desc": "Свежие новости искусственного интеллекта: прорывы, исследования, релизы. Будьте в курсе развития AI технологий.",
        "keyword": "AI новости"
    }
}


def create_database_plugin():
    """Создание плагина для прямой работы с БД"""
    
    plugin_code = '''<?php
/**
 * Plugin Name: Yoast Direct Database Update
 * Description: Прямое обновление Yoast SEO через базу данных
 * Version: 1.0
 */

if (!defined('ABSPATH')) {
    exit;
}

class YoastDirectDBUpdate {
    
    public function __construct() {
        add_action('rest_api_init', array($this, 'register_routes'));
    }
    
    public function register_routes() {
        // Обновление через прямое обращение к БД
        register_rest_route('yoast-db/v1', '/update-category/(?P<id>\\d+)', array(
            'methods' => 'POST',
            'callback' => array($this, 'update_category_direct'),
            'permission_callback' => function() {
                return current_user_can('manage_categories');
            }
        ));
        
        // Массовое обновление
        register_rest_route('yoast-db/v1', '/bulk-update', array(
            'methods' => 'POST',
            'callback' => array($this, 'bulk_update_direct'),
            'permission_callback' => function() {
                return current_user_can('manage_categories');
            }
        ));
        
        // Проверка таблиц Yoast
        register_rest_route('yoast-db/v1', '/check-tables', array(
            'methods' => 'GET',
            'callback' => array($this, 'check_yoast_tables'),
            'permission_callback' => function() {
                return current_user_can('manage_categories');
            }
        ));
    }
    
    public function check_yoast_tables() {
        global $wpdb;
        
        $tables = array();
        
        // Проверяем основные таблицы Yoast
        $yoast_tables = array(
            'yoast_indexable',
            'yoast_indexable_hierarchy', 
            'yoast_migrations',
            'yoast_primary_term'
        );
        
        foreach ($yoast_tables as $table) {
            $full_table_name = $wpdb->prefix . $table;
            $exists = $wpdb->get_var("SHOW TABLES LIKE '$full_table_name'") == $full_table_name;
            $tables[$table] = $exists;
            
            if ($exists) {
                $count = $wpdb->get_var("SELECT COUNT(*) FROM $full_table_name");
                $tables[$table . '_count'] = $count;
            }
        }
        
        // Проверяем termmeta
        $termmeta_yoast = $wpdb->get_results("
            SELECT meta_key, COUNT(*) as count 
            FROM {$wpdb->termmeta} 
            WHERE meta_key LIKE '_yoast_wpseo_%' 
            GROUP BY meta_key
        ");
        
        return array(
            'yoast_tables' => $tables,
            'termmeta_yoast' => $termmeta_yoast,
            'wp_prefix' => $wpdb->prefix
        );
    }
    
    public function update_category_direct($request) {
        global $wpdb;
        
        $category_id = intval($request['id']);
        $data = $request->get_json_params();
        
        if (!$data) {
            return new WP_Error('no_data', 'Нет данных для обновления');
        }
        
        $results = array();
        
        // 1. Обновляем termmeta (стандартный способ)
        if (!empty($data['title'])) {
            update_term_meta($category_id, '_yoast_wpseo_title', sanitize_text_field($data['title']));
            $results['termmeta_title'] = 'updated';
        }
        
        if (!empty($data['desc'])) {
            update_term_meta($category_id, '_yoast_wpseo_metadesc', sanitize_textarea_field($data['desc']));
            $results['termmeta_desc'] = 'updated';
        }
        
        if (!empty($data['keyword'])) {
            update_term_meta($category_id, '_yoast_wpseo_focuskw', sanitize_text_field($data['keyword']));
            $results['termmeta_keyword'] = 'updated';
        }
        
        // 2. Проверяем/создаем запись в yoast_indexable
        $indexable_table = $wpdb->prefix . 'yoast_indexable';
        
        if ($wpdb->get_var("SHOW TABLES LIKE '$indexable_table'") == $indexable_table) {
            // Ищем существующую запись
            $existing = $wpdb->get_row($wpdb->prepare("
                SELECT * FROM $indexable_table 
                WHERE object_type = 'term' AND object_id = %d
            ", $category_id));
            
            $indexable_data = array(
                'object_type' => 'term',
                'object_id' => $category_id,
                'object_sub_type' => 'category',
                'permalink' => get_term_link($category_id),
                'title' => !empty($data['title']) ? $data['title'] : null,
                'description' => !empty($data['desc']) ? $data['desc'] : null,
                'primary_focus_keyword' => !empty($data['keyword']) ? $data['keyword'] : null,
                'is_robots_noindex' => 0,
                'is_robots_nofollow' => 0,
                'is_robots_noarchive' => null,
                'is_robots_noimageindex' => null,
                'is_robots_nosnippet' => null,
                'updated_at' => current_time('mysql', 1),
                'blog_id' => get_current_blog_id(),
                'language' => get_locale(),
                'region' => null,
                'schema_page_type' => null,
                'schema_article_type' => null,
                'has_public_posts' => null,
                'number_of_pages' => null,
                'open_graph_image' => null,
                'open_graph_image_id' => null,
                'open_graph_image_source' => null,
                'open_graph_image_meta' => null,
                'twitter_image' => null,
                'twitter_image_id' => null,
                'twitter_image_source' => null,
                'canonical' => null,
                'primary_focus_keyword_score' => null,
                'readability_score' => null,
                'link_count' => null,
                'incoming_link_count' => null,
                'prominent_words_version' => null,
                'created_at' => current_time('mysql', 1),
                'author_id' => null,
                'post_parent' => null,
                'breadcrumb_title' => null,
                'open_graph_title' => null,
                'open_graph_description' => null,
                'twitter_title' => null,
                'twitter_description' => null,
                'meta_robots_noindex' => null,
                'meta_robots_nofollow' => null,
                'meta_robots_adv' => null,
                'bct_title' => null,
                'bct_description' => null,
                'estimated_reading_time_minutes' => null,
                'version' => 1
            );
            
            if ($existing) {
                // Обновляем существующую запись
                $where = array('object_type' => 'term', 'object_id' => $category_id);
                $updated = $wpdb->update($indexable_table, $indexable_data, $where);
                $results['indexable'] = $updated !== false ? 'updated' : 'failed';
            } else {
                // Создаем новую запись
                $inserted = $wpdb->insert($indexable_table, $indexable_data);
                $results['indexable'] = $inserted !== false ? 'created' : 'failed';
            }
        } else {
            $results['indexable'] = 'table_not_found';
        }
        
        // 3. Очищаем кеши
        clean_term_cache($category_id);
        wp_cache_flush();
        
        // 4. Запускаем хуки WordPress
        do_action('edited_term', $category_id, '', 'category');
        do_action('edited_category', $category_id);
        
        return array(
            'success' => true,
            'category_id' => $category_id,
            'results' => $results
        );
    }
    
    public function bulk_update_direct($request) {
        $categories_data = $request->get_json_params();
        
        if (empty($categories_data)) {
            return new WP_Error('no_data', 'Нет данных для обновления');
        }
        
        $results = array();
        
        foreach ($categories_data as $cat_data) {
            if (empty($cat_data['category_id'])) continue;
            
            $fake_request = new WP_REST_Request('POST');
            $fake_request->set_param('id', $cat_data['category_id']);
            $fake_request->set_body(json_encode($cat_data));
            
            $result = $this->update_category_direct($fake_request);
            $results[] = $result;
        }
        
        return array(
            'success' => true,
            'processed' => count($results),
            'results' => $results
        );
    }
}

new YoastDirectDBUpdate();
?>'''
    
    return plugin_code


def create_db_plugin_file():
    """Создание файла плагина для БД"""
    plugin_code = create_database_plugin()
    
    plugin_path = "/Users/skynet/Desktop/AI DEV/ainews-clean/wordpress-plugin/yoast-db-direct.php"
    
    with open(plugin_path, 'w', encoding='utf-8') as f:
        f.write(plugin_code)
    
    print(f'✅ Создан плагин: {plugin_path}')
    return plugin_path


def test_db_plugin():
    """Тестирование плагина БД"""
    config = Config()
    auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
    
    print('🔍 Тестирование плагина прямого доступа к БД...')
    
    # Проверяем доступность
    response = requests.get('https://ailynx.ru/wp-json/yoast-db/v1/check-tables', auth=auth)
    
    if response.status_code == 200:
        data = response.json()
        print('✅ Плагин БД работает!')
        print(f'📊 Yoast таблицы: {data.get("yoast_tables")}')
        print(f'📋 Termmeta записи: {len(data.get("termmeta_yoast", []))}')
        
        # Тестируем обновление одной категории
        test_data = {
            'title': 'ТЕСТ БД - Машинное обучение | AI Lynx',
            'desc': 'Тестовое описание через прямой доступ к базе данных',
            'keyword': 'тест машинное обучение БД'
        }
        
        update_response = requests.post(
            'https://ailynx.ru/wp-json/yoast-db/v1/update-category/4',
            json=test_data,
            auth=auth
        )
        
        if update_response.status_code == 200:
            result = update_response.json()
            print('✅ Обновление через БД успешно!')
            print(f'📋 Результаты: {result.get("results")}')
            return True
        else:
            print(f'❌ Ошибка обновления через БД: {update_response.status_code}')
            print(f'   Ответ: {update_response.text[:200]}')
    else:
        print('❌ Плагин БД не найден или не активен')
    
    return False


def main():
    print('🗄️  Прямое обновление Yoast через базу данных')
    print('=' * 60)
    
    # Создаем плагин
    plugin_path = create_db_plugin_file()
    
    print('\n📦 Установка плагина:')
    print('1. Загрузите файл yoast-db-direct.php в WordPress')
    print('2. Активируйте плагин "Yoast Direct Database Update"')
    print('3. Запустите тест: python scripts/yoast_database_update.py')
    
    # Создаем ZIP
    import zipfile
    zip_path = plugin_path.replace('.php', '.zip')
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        zipf.write(plugin_path, 'yoast-db-direct.php')
    
    print(f'\n📦 ZIP файл создан: {zip_path}')
    
    # Пробуем протестировать если плагин уже активен
    print('\n🧪 Проверяем, активен ли плагин...')
    if test_db_plugin():
        print('\n🎉 Плагин работает! Можно использовать для массового обновления')
    else:
        print('\n💡 Сначала активируйте плагин в WordPress')


if __name__ == "__main__":
    main()