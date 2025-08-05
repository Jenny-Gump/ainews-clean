<?php
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
        register_rest_route('category-meta/v1', '/update/(?P<id>\d+)', array(
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
                echo '<meta name="description" content="' . esc_attr($meta_description) . '">' . "\n";
            }
        }
    }
}

new CategoryMetaDescriptions();
?>