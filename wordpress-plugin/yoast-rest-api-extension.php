<?php
/**
 * Plugin Name: Yoast REST API Extension
 * Description: Расширяет WordPress REST API для работы с полями Yoast SEO категорий
 * Version: 1.0
 * Based on: https://developer.yoast.com/customization/apis/rest-api/
 */

if (!defined('ABSPATH')) {
    exit;
}

class YoastRestAPIExtension {
    
    public function __construct() {
        add_action('rest_api_init', array($this, 'register_yoast_fields'));
    }
    
    /**
     * Регистрация Yoast полей в REST API
     */
    public function register_yoast_fields() {
        // Добавляем поддержку для категорий
        $this->register_category_fields();
        
        // Добавляем поддержку для постов (опционально)
        $this->register_post_fields();
    }
    
    /**
     * Регистрация полей для категорий
     */
    private function register_category_fields() {
        // Yoast SEO Title
        register_rest_field('category', 'yoast_title', array(
            'get_callback' => array($this, 'get_category_yoast_title'),
            'update_callback' => array($this, 'update_category_yoast_title'),
            'schema' => array(
                'type' => 'string',
                'description' => 'Yoast SEO Title for category',
                'context' => array('view', 'edit')
            ),
        ));
        
        // Yoast Meta Description
        register_rest_field('category', 'yoast_description', array(
            'get_callback' => array($this, 'get_category_yoast_description'),
            'update_callback' => array($this, 'update_category_yoast_description'),
            'schema' => array(
                'type' => 'string',
                'description' => 'Yoast SEO Meta Description for category',
                'context' => array('view', 'edit')
            ),
        ));
        
        // Yoast Focus Keyword
        register_rest_field('category', 'yoast_keyword', array(
            'get_callback' => array($this, 'get_category_yoast_keyword'),
            'update_callback' => array($this, 'update_category_yoast_keyword'),
            'schema' => array(
                'type' => 'string',
                'description' => 'Yoast SEO Focus Keyword for category',
                'context' => array('view', 'edit')
            ),
        ));
        
        // Yoast Canonical URL
        register_rest_field('category', 'yoast_canonical', array(
            'get_callback' => array($this, 'get_category_yoast_canonical'),
            'update_callback' => array($this, 'update_category_yoast_canonical'),
            'schema' => array(
                'type' => 'string',
                'description' => 'Yoast SEO Canonical URL for category',
                'context' => array('view', 'edit')
            ),
        ));
    }
    
    /**
     * Регистрация полей для постов (опционально)
     */
    private function register_post_fields() {
        register_rest_field('post', 'yoast_title', array(
            'get_callback' => array($this, 'get_post_yoast_title'),
            'update_callback' => array($this, 'update_post_yoast_title'),
            'schema' => array(
                'type' => 'string',
                'description' => 'Yoast SEO Title for post',
                'context' => array('view', 'edit')
            ),
        ));
        
        register_rest_field('post', 'yoast_description', array(
            'get_callback' => array($this, 'get_post_yoast_description'),
            'update_callback' => array($this, 'update_post_yoast_description'),
            'schema' => array(
                'type' => 'string',
                'description' => 'Yoast SEO Meta Description for post',
                'context' => array('view', 'edit')
            ),
        ));
        
        register_rest_field('post', 'yoast_keyword', array(
            'get_callback' => array($this, 'get_post_yoast_keyword'),
            'update_callback' => array($this, 'update_post_yoast_keyword'),
            'schema' => array(
                'type' => 'string',
                'description' => 'Yoast SEO Focus Keyword for post',
                'context' => array('view', 'edit')
            ),
        ));
    }
    
    // ====== CATEGORY CALLBACKS ======
    
    public function get_category_yoast_title($term) {
        return get_term_meta($term['id'], '_yoast_wpseo_title', true);
    }
    
    public function update_category_yoast_title($value, $term) {
        if (!current_user_can('manage_categories')) {
            return false;
        }
        return update_term_meta($term->term_id, '_yoast_wpseo_title', sanitize_text_field($value));
    }
    
    public function get_category_yoast_description($term) {
        return get_term_meta($term['id'], '_yoast_wpseo_metadesc', true);
    }
    
    public function update_category_yoast_description($value, $term) {
        if (!current_user_can('manage_categories')) {
            return false;
        }
        return update_term_meta($term->term_id, '_yoast_wpseo_metadesc', sanitize_textarea_field($value));
    }
    
    public function get_category_yoast_keyword($term) {
        return get_term_meta($term['id'], '_yoast_wpseo_focuskw', true);
    }
    
    public function update_category_yoast_keyword($value, $term) {
        if (!current_user_can('manage_categories')) {
            return false;
        }
        return update_term_meta($term->term_id, '_yoast_wpseo_focuskw', sanitize_text_field($value));
    }
    
    public function get_category_yoast_canonical($term) {
        return get_term_meta($term['id'], '_yoast_wpseo_canonical', true);
    }
    
    public function update_category_yoast_canonical($value, $term) {
        if (!current_user_can('manage_categories')) {
            return false;
        }
        return update_term_meta($term->term_id, '_yoast_wpseo_canonical', esc_url_raw($value));
    }
    
    // ====== POST CALLBACKS ======
    
    public function get_post_yoast_title($post) {
        return get_post_meta($post['id'], '_yoast_wpseo_title', true);
    }
    
    public function update_post_yoast_title($value, $post) {
        if (!current_user_can('edit_post', $post->ID)) {
            return false;
        }
        return update_post_meta($post->ID, '_yoast_wpseo_title', sanitize_text_field($value));
    }
    
    public function get_post_yoast_description($post) {
        return get_post_meta($post['id'], '_yoast_wpseo_metadesc', true);
    }
    
    public function update_post_yoast_description($value, $post) {
        if (!current_user_can('edit_post', $post->ID)) {
            return false;
        }
        return update_post_meta($post->ID, '_yoast_wpseo_metadesc', sanitize_textarea_field($value));
    }
    
    public function get_post_yoast_keyword($post) {
        return get_post_meta($post['id'], '_yoast_wpseo_focuskw', true);
    }
    
    public function update_post_yoast_keyword($value, $post) {
        if (!current_user_can('edit_post', $post->ID)) {
            return false;
        }
        return update_post_meta($post->ID, '_yoast_wpseo_focuskw', sanitize_text_field($value));
    }
}

// Инициализация плагина
new YoastRestAPIExtension();

/**
 * Хук активации плагина
 */
register_activation_hook(__FILE__, function() {
    // Проверяем наличие Yoast SEO
    if (!is_plugin_active('wordpress-seo/wp-seo.php')) {
        deactivate_plugins(plugin_basename(__FILE__));
        wp_die('Этот плагин требует активации Yoast SEO plugin.');
    }
    
    // Очищаем кэш rewrite rules
    flush_rewrite_rules();
});

/**
 * Debug функция для проверки мета-полей категории
 */
function debug_category_yoast_fields($category_id) {
    if (!current_user_can('manage_options')) {
        return;
    }
    
    $fields = array(
        '_yoast_wpseo_title' => get_term_meta($category_id, '_yoast_wpseo_title', true),
        '_yoast_wpseo_metadesc' => get_term_meta($category_id, '_yoast_wpseo_metadesc', true),
        '_yoast_wpseo_focuskw' => get_term_meta($category_id, '_yoast_wpseo_focuskw', true),
        '_yoast_wpseo_canonical' => get_term_meta($category_id, '_yoast_wpseo_canonical', true),
    );
    
    return $fields;
}
?>