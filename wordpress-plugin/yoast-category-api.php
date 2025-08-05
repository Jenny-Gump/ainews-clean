<?php
/**
 * Plugin Name: Yoast Category API Extension
 * Description: Добавляет REST API эндпоинты для управления Yoast SEO полями категорий
 * Version: 1.0
 * Author: AI News Parser System
 */

// Предотвращаем прямой доступ к файлу
if (!defined('ABSPATH')) {
    exit;
}

class YoastCategoryAPI {
    
    public function __construct() {
        add_action('rest_api_init', array($this, 'register_routes'));
    }
    
    /**
     * Регистрация маршрутов REST API
     */
    public function register_routes() {
        // Получение SEO данных категории
        register_rest_route('yoast-category/v1', '/category/(?P<id>\d+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_category_seo'),
            'permission_callback' => array($this, 'check_permissions'),
            'args' => array(
                'id' => array(
                    'validate_callback' => function($param, $request, $key) {
                        return is_numeric($param);
                    }
                ),
            ),
        ));
        
        // Обновление SEO данных категории
        register_rest_route('yoast-category/v1', '/category/(?P<id>\d+)', array(
            'methods' => 'POST',
            'callback' => array($this, 'update_category_seo'),
            'permission_callback' => array($this, 'check_permissions'),
            'args' => array(
                'id' => array(
                    'validate_callback' => function($param, $request, $key) {
                        return is_numeric($param);
                    }
                ),
                'yoast_title' => array(
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field',
                ),
                'yoast_desc' => array(
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_textarea_field',
                ),
                'yoast_keyword' => array(
                    'type' => 'string',
                    'sanitize_callback' => 'sanitize_text_field',
                ),
            ),
        ));
        
        // Массовое обновление категорий
        register_rest_route('yoast-category/v1', '/categories/bulk', array(
            'methods' => 'POST',
            'callback' => array($this, 'bulk_update_categories'),
            'permission_callback' => array($this, 'check_permissions'),
        ));
    }
    
    /**
     * Проверка прав доступа
     */
    public function check_permissions() {
        return current_user_can('manage_categories');
    }
    
    /**
     * Получение SEO данных категории
     */
    public function get_category_seo($request) {
        $category_id = $request['id'];
        
        // Проверяем существование категории
        $category = get_term($category_id, 'category');
        if (is_wp_error($category) || !$category) {
            return new WP_Error('category_not_found', 'Категория не найдена', array('status' => 404));
        }
        
        // Получаем Yoast данные
        $yoast_title = get_term_meta($category_id, '_yoast_wpseo_title', true);
        $yoast_desc = get_term_meta($category_id, '_yoast_wpseo_metadesc', true);
        $yoast_keyword = get_term_meta($category_id, '_yoast_wpseo_focuskw', true);
        
        return array(
            'category_id' => $category_id,
            'category_name' => $category->name,
            'category_slug' => $category->slug,
            'yoast_title' => $yoast_title,
            'yoast_desc' => $yoast_desc,
            'yoast_keyword' => $yoast_keyword,
            'yoast_canonical' => get_term_meta($category_id, '_yoast_wpseo_canonical', true),
            'yoast_noindex' => get_term_meta($category_id, '_yoast_wpseo_noindex', true),
        );
    }
    
    /**
     * Обновление SEO данных категории
     */
    public function update_category_seo($request) {
        $category_id = $request['id'];
        
        // Проверяем существование категории
        $category = get_term($category_id, 'category');
        if (is_wp_error($category) || !$category) {
            return new WP_Error('category_not_found', 'Категория не найдена', array('status' => 404));
        }
        
        $updated_fields = array();
        
        // Обновляем Yoast заголовок
        if (!empty($request['yoast_title'])) {
            update_term_meta($category_id, '_yoast_wpseo_title', $request['yoast_title']);
            $updated_fields['yoast_title'] = $request['yoast_title'];
        }
        
        // Обновляем Yoast описание
        if (!empty($request['yoast_desc'])) {
            update_term_meta($category_id, '_yoast_wpseo_metadesc', $request['yoast_desc']);
            $updated_fields['yoast_desc'] = $request['yoast_desc'];
        }
        
        // Обновляем Yoast ключевое слово
        if (!empty($request['yoast_keyword'])) {
            update_term_meta($category_id, '_yoast_wpseo_focuskw', $request['yoast_keyword']);
            $updated_fields['yoast_keyword'] = $request['yoast_keyword'];
        }
        
        // Дополнительные поля
        if (!empty($request['yoast_canonical'])) {
            update_term_meta($category_id, '_yoast_wpseo_canonical', $request['yoast_canonical']);
            $updated_fields['yoast_canonical'] = $request['yoast_canonical'];
        }
        
        if (isset($request['yoast_noindex'])) {
            update_term_meta($category_id, '_yoast_wpseo_noindex', $request['yoast_noindex']);
            $updated_fields['yoast_noindex'] = $request['yoast_noindex'];
        }
        
        // Очищаем кеш Yoast (если есть)
        if (function_exists('YoastSEO')) {
            do_action('wpseo_saved_term', $category_id, 'category');
        }
        
        return array(
            'success' => true,
            'category_id' => $category_id,
            'category_name' => $category->name,
            'updated_fields' => $updated_fields,
            'message' => 'SEO поля категории успешно обновлены'
        );
    }
    
    /**
     * Массовое обновление категорий
     */
    public function bulk_update_categories($request) {
        $categories_data = $request->get_json_params();
        
        if (empty($categories_data) || !is_array($categories_data)) {
            return new WP_Error('invalid_data', 'Неверные данные для обновления', array('status' => 400));
        }
        
        $results = array();
        
        foreach ($categories_data as $cat_data) {
            if (empty($cat_data['category_id'])) {
                continue;
            }
            
            $category_id = intval($cat_data['category_id']);
            $category = get_term($category_id, 'category');
            
            if (is_wp_error($category) || !$category) {
                $results[] = array(
                    'category_id' => $category_id,
                    'success' => false,
                    'error' => 'Категория не найдена'
                );
                continue;
            }
            
            $updated = array();
            
            // Обновляем поля
            if (!empty($cat_data['yoast_title'])) {
                update_term_meta($category_id, '_yoast_wpseo_title', sanitize_text_field($cat_data['yoast_title']));
                $updated['title'] = true;
            }
            
            if (!empty($cat_data['yoast_desc'])) {
                update_term_meta($category_id, '_yoast_wpseo_metadesc', sanitize_textarea_field($cat_data['yoast_desc']));
                $updated['desc'] = true;
            }
            
            if (!empty($cat_data['yoast_keyword'])) {
                update_term_meta($category_id, '_yoast_wpseo_focuskw', sanitize_text_field($cat_data['yoast_keyword']));
                $updated['keyword'] = true;
            }
            
            $results[] = array(
                'category_id' => $category_id,
                'category_name' => $category->name,
                'success' => true,
                'updated_fields' => $updated
            );
        }
        
        return array(
            'success' => true,
            'processed' => count($results),
            'results' => $results
        );
    }
}

// Инициализация плагина
new YoastCategoryAPI();

/**
 * Хук активации плагина
 */
register_activation_hook(__FILE__, function() {
    // Проверяем наличие Yoast SEO
    if (!is_plugin_active('wordpress-seo/wp-seo.php')) {
        deactivate_plugins(plugin_basename(__FILE__));
        wp_die('Этот плагин требует активации Yoast SEO plugin.');
    }
});