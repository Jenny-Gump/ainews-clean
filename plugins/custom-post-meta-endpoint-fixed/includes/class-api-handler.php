<?php

/**
 * Класс для обработки REST API запросов
 */

if (!defined('ABSPATH')) {
    exit;
}

class Post_Meta_Endpoint_API_Handler
{
    
    /**
     * Конструктор
     */
    public function __construct()
    {
        add_action('rest_api_init', [$this, 'register_routes']);
    }
    
    /**
     * Регистрация маршрутов API
     */
    public function register_routes()
    {
        $namespace = 'custom-post-meta/v1';
        
        // Создание поста
        register_rest_route($namespace, '/posts', [
            'methods' => 'POST',
            'callback' => [$this, 'create_post'],
            'permission_callback' => [$this, 'check_permission'],
            'args' => Post_Meta_Endpoint_Validator::get_create_args()
        ]);
        
        // Обновление поста
        register_rest_route($namespace, '/posts/(?P<id>\d+)', [
            'methods' => 'PUT',
            'callback' => [$this, 'update_post'],
            'permission_callback' => [$this, 'check_permission'],
            'args' => Post_Meta_Endpoint_Validator::get_update_args()
        ]);
    }
    
    /**
     * Проверка прав доступа через API ключ
     */
    public function check_permission($request)
    {
        $api_key = $request->get_header('X-API-Key');
        
        if (empty($api_key)) {
            return new WP_Error('no_api_key', 'API key required', ['status' => 401]);
        }
        
        $stored_key = get_option('post_meta_endpoint_api_key');
        
        if ($api_key !== $stored_key) {
            return new WP_Error('invalid_api_key', 'Invalid API key', ['status' => 401]);
        }
        
        return true;
    }
    
    /**
     * Создание нового поста
     */
    public function create_post($request)
    {
        $params = $request->get_params();
        
        // Валидация параметров
        $validation = Post_Meta_Endpoint_Validator::validate_all_params($params);
        if ($validation !== true) {
            return new WP_Error('validation_failed', implode('; ', $validation), ['status' => 400]);
        }
        
        // Подготовка данных поста
        $post_data = [
            'post_title' => $params['title'],
            'post_content' => $params['content'] ?? '',
            'post_excerpt' => $params['excerpt'] ?? '',
            'post_status' => $params['status'] ?? 'draft',
            'post_type' => $params['post_type'] ?? 'post',
            'post_author' => $params['author'] ?? get_current_user_id()
        ];
        
        if (!empty($params['slug'])) {
            $post_data['post_name'] = $params['slug'];
        }
        
        // Создание поста
        $post_id = wp_insert_post($post_data, true);
        
        if (is_wp_error($post_id)) {
            return $post_id;
        }
        
        // Установка категорий
        if (!empty($params['categories'])) {
            wp_set_post_categories($post_id, $params['categories']);
        }
        
        // Установка тегов
        if (!empty($params['tags'])) {
            wp_set_post_tags($post_id, $params['tags']);
        }
        
        // Сохранение SEO мета-полей
        Post_Meta_Endpoint_SEO_Meta::save_seo_meta($post_id, $params);
        
        // Возвращаем созданный пост
        return rest_ensure_response([
            'success' => true,
            'post_id' => $post_id,
            'post_url' => get_permalink($post_id),
            'edit_url' => get_edit_post_link($post_id, 'raw')
        ]);
    }
    
    /**
     * Обновление существующего поста
     */
    public function update_post($request)
    {
        $post_id = $request->get_param('id');
        $params = $request->get_params();
        
        // Проверка существования поста
        if (!get_post($post_id)) {
            return new WP_Error('post_not_found', 'Post not found', ['status' => 404]);
        }
        
        // Валидация параметров
        $validation = Post_Meta_Endpoint_Validator::validate_all_params($params);
        if ($validation !== true) {
            return new WP_Error('validation_failed', implode('; ', $validation), ['status' => 400]);
        }
        
        // Подготовка данных для обновления
        $post_data = ['ID' => $post_id];
        
        if (isset($params['title'])) {
            $post_data['post_title'] = $params['title'];
        }
        if (isset($params['content'])) {
            $post_data['post_content'] = $params['content'];
        }
        if (isset($params['excerpt'])) {
            $post_data['post_excerpt'] = $params['excerpt'];
        }
        if (isset($params['status'])) {
            $post_data['post_status'] = $params['status'];
        }
        if (isset($params['slug'])) {
            $post_data['post_name'] = $params['slug'];
        }
        if (isset($params['author'])) {
            $post_data['post_author'] = $params['author'];
        }
        
        // Обновление поста
        $result = wp_update_post($post_data, true);
        
        if (is_wp_error($result)) {
            return $result;
        }
        
        // Обновление категорий
        if (isset($params['categories'])) {
            wp_set_post_categories($post_id, $params['categories']);
        }
        
        // Обновление тегов
        if (isset($params['tags'])) {
            wp_set_post_tags($post_id, $params['tags']);
        }
        
        // Обновление SEO мета-полей
        Post_Meta_Endpoint_SEO_Meta::save_seo_meta($post_id, $params);
        
        return rest_ensure_response([
            'success' => true,
            'post_id' => $post_id,
            'post_url' => get_permalink($post_id),
            'edit_url' => get_edit_post_link($post_id, 'raw')
        ]);
    }
}