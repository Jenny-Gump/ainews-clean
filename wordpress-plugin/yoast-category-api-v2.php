<?php
/**
 * Plugin Name: Yoast Category API Extension V2
 * Description: Улучшенная версия для управления Yoast SEO полями категорий через REST API с принудительной индексацией
 * Version: 2.0
 * Author: AI News Parser System
 */

// Предотвращаем прямой доступ к файлу
if (!defined('ABSPATH')) {
    exit;
}

class YoastCategoryAPIV2 {
    
    public function __construct() {
        add_action('rest_api_init', array($this, 'register_routes'));
    }
    
    /**
     * Регистрация маршрутов REST API
     */
    public function register_routes() {
        // Получение SEO данных категории
        register_rest_route('yoast-category/v2', '/category/(?P<id>\d+)', array(
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
        register_rest_route('yoast-category/v2', '/category/(?P<id>\d+)', array(
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
        register_rest_route('yoast-category/v2', '/categories/bulk', array(
            'methods' => 'POST',
            'callback' => array($this, 'bulk_update_categories'),
            'permission_callback' => array($this, 'check_permissions'),
        ));
        
        // Принудительная очистка кэша
        register_rest_route('yoast-category/v2', '/clear-cache', array(
            'methods' => 'POST',
            'callback' => array($this, 'clear_yoast_cache'),
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
        
        // Также проверяем через Yoast API если доступен
        $yoast_indexable = null;
        if (class_exists('YoastSEO')) {
            try {
                $indexable_repository = YoastSEO()->classes->get('Yoast\WP\SEO\Repositories\Indexable_Repository');
                if ($indexable_repository) {
                    $yoast_indexable = $indexable_repository->find_by_id_and_type($category_id, 'term');
                }
            } catch (Exception $e) {
                // Игнорируем ошибки
            }
        }
        
        return array(
            'category_id' => $category_id,
            'category_name' => $category->name,
            'category_slug' => $category->slug,
            'yoast_title' => $yoast_title,
            'yoast_desc' => $yoast_desc,
            'yoast_keyword' => $yoast_keyword,
            'yoast_canonical' => get_term_meta($category_id, '_yoast_wpseo_canonical', true),
            'yoast_noindex' => get_term_meta($category_id, '_yoast_wpseo_noindex', true),
            'yoast_indexable' => $yoast_indexable ? 'found' : 'not_found',
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
        
        // Принудительно создаем/обновляем Yoast indexable
        $this->force_yoast_indexable_update($category_id, $category->taxonomy);
        
        // Очищаем кеш
        $this->clear_category_cache($category_id);
        
        return array(
            'success' => true,
            'category_id' => $category_id,
            'category_name' => $category->name,
            'updated_fields' => $updated_fields,
            'message' => 'SEO поля категории успешно обновлены',
            'yoast_updated' => 'indexable refreshed'
        );
    }
    
    /**
     * Принудительное обновление Yoast indexable
     */
    private function force_yoast_indexable_update($term_id, $taxonomy) {
        if (!class_exists('YoastSEO')) {
            return false;
        }
        
        try {
            // Получаем репозиторий indexable
            $indexable_repository = YoastSEO()->classes->get('Yoast\WP\SEO\Repositories\Indexable_Repository');
            if (!$indexable_repository) {
                return false;
            }
            
            // Находим существующий indexable или создаем новый
            $indexable = $indexable_repository->find_by_id_and_type($term_id, 'term');
            
            if (!$indexable) {
                // Создаем новый indexable
                $builder = YoastSEO()->classes->get('Yoast\WP\SEO\Builders\Indexable_Term_Builder');
                if ($builder) {
                    $indexable = $builder->build($term_id, (object) get_term($term_id, $taxonomy));
                }
            }
            
            if ($indexable) {
                // Принудительно обновляем поля
                $yoast_title = get_term_meta($term_id, '_yoast_wpseo_title', true);
                $yoast_desc = get_term_meta($term_id, '_yoast_wpseo_metadesc', true);
                $yoast_keyword = get_term_meta($term_id, '_yoast_wpseo_focuskw', true);
                
                if ($yoast_title) {
                    $indexable->title = $yoast_title;
                }
                if ($yoast_desc) {
                    $indexable->description = $yoast_desc;
                }
                if ($yoast_keyword) {
                    $indexable->primary_focus_keyword = $yoast_keyword;
                }
                
                // Сохраняем indexable
                $indexable_repository->save($indexable);
                
                return true;
            }
            
        } catch (Exception $e) {
            error_log('Yoast indexable update error: ' . $e->getMessage());
        }
        
        return false;
    }
    
    /**
     * Очистка кэша категории
     */
    private function clear_category_cache($category_id) {
        // Очищаем WordPress кэш
        clean_term_cache($category_id, 'category');
        
        // Очищаем Yoast кэш если доступен
        if (function_exists('wpseo_flush_cache')) {
            wpseo_flush_cache();
        }
        
        // Принудительно запускаем хуки Yoast
        do_action('wpseo_saved_term', $category_id, 'category');
        
        // Очищаем object cache
        wp_cache_delete($category_id, 'category');
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
            
            // Принудительно обновляем Yoast indexable
            $yoast_updated = $this->force_yoast_indexable_update($category_id, $category->taxonomy);
            
            // Очищаем кэш
            $this->clear_category_cache($category_id);
            
            $results[] = array(
                'category_id' => $category_id,
                'category_name' => $category->name,
                'success' => true,
                'updated_fields' => $updated,
                'yoast_indexable_updated' => $yoast_updated
            );
        }
        
        // Глобальная очистка кэша
        $this->clear_yoast_cache_global();
        
        return array(
            'success' => true,
            'processed' => count($results),
            'results' => $results
        );
    }
    
    /**
     * Очистка кэша Yoast
     */
    public function clear_yoast_cache($request) {
        $this->clear_yoast_cache_global();
        
        return array(
            'success' => true,
            'message' => 'Кэш Yoast очищен'
        );
    }
    
    /**
     * Глобальная очистка кэша Yoast
     */
    private function clear_yoast_cache_global() {
        // Очищаем весь кэш WordPress
        if (function_exists('wp_cache_flush')) {
            wp_cache_flush();
        }
        
        // Очищаем кэш Yoast
        if (function_exists('wpseo_flush_cache')) {
            wpseo_flush_cache();
        }
        
        // Удаляем transients
        global $wpdb;
        $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_wpseo_%'");
        $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_timeout_wpseo_%'");
    }
}

// Инициализация плагина
new YoastCategoryAPIV2();

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