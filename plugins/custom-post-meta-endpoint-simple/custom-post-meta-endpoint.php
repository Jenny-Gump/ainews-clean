<?php
/*
Plugin Name: Custom Post Meta Endpoint Simple
Description: Простой REST API для создания постов с SEO полями без ограничений
Version: 1.0.0
Author: Modified
*/

// Блокируем прямой доступ
defined('ABSPATH') or exit;

// Добавляем хук для инициализации API
add_action('rest_api_init', 'custom_post_meta_register_routes');

function custom_post_meta_register_routes() {
    register_rest_route('custom-post-meta/v1', '/posts', array(
        'methods' => 'POST',
        'callback' => 'custom_post_meta_create_post',
        'permission_callback' => 'custom_post_meta_check_permission'
    ));
}

// Проверка API ключа
function custom_post_meta_check_permission($request) {
    $api_key = $request->get_header('X-API-Key');
    $stored_key = get_option('custom_post_meta_api_key', 'bmgiwSmJgRPoXyDX7zNoVv4Vr8Xt1qwI');
    
    if ($api_key !== $stored_key) {
        return new WP_Error('invalid_key', 'Invalid API key', array('status' => 401));
    }
    
    return true;
}

// Создание поста
function custom_post_meta_create_post($request) {
    $params = $request->get_params();
    
    // Проверяем обязательное поле title
    if (empty($params['title'])) {
        return new WP_Error('missing_title', 'Title is required', array('status' => 400));
    }
    
    // Создаем пост
    $post_data = array(
        'post_title' => sanitize_text_field($params['title']),
        'post_content' => wp_kses_post($params['content'] ?? ''),
        'post_excerpt' => sanitize_textarea_field($params['excerpt'] ?? ''),
        'post_status' => sanitize_key($params['status'] ?? 'draft'),
        'post_type' => 'post'
    );
    
    if (!empty($params['slug'])) {
        $post_data['post_name'] = sanitize_title($params['slug']);
    }
    
    // Вставляем пост
    $post_id = wp_insert_post($post_data);
    
    if (is_wp_error($post_id)) {
        return $post_id;
    }
    
    // Устанавливаем категории
    if (!empty($params['categories']) && is_array($params['categories'])) {
        wp_set_post_categories($post_id, array_map('intval', $params['categories']));
    }
    
    // Устанавливаем теги
    if (!empty($params['tags']) && is_array($params['tags'])) {
        wp_set_post_tags($post_id, array_map('sanitize_text_field', $params['tags']));
    }
    
    // Сохраняем SEO поля БЕЗ ОГРАНИЧЕНИЙ
    if (!empty($params['seo_title'])) {
        update_post_meta($post_id, '_yoast_wpseo_title', sanitize_text_field($params['seo_title']));
    }
    
    if (!empty($params['seo_description'])) {
        update_post_meta($post_id, '_yoast_wpseo_metadesc', sanitize_textarea_field($params['seo_description']));
    }
    
    if (!empty($params['focus_keyword'])) {
        update_post_meta($post_id, '_yoast_wpseo_focuskw', sanitize_text_field($params['focus_keyword']));
    }
    
    // Возвращаем результат
    return rest_ensure_response(array(
        'success' => true,
        'post_id' => $post_id,
        'post_url' => get_permalink($post_id),
        'edit_url' => get_edit_post_link($post_id, 'raw')
    ));
}

// Добавляем страницу настроек
add_action('admin_menu', 'custom_post_meta_admin_menu');

function custom_post_meta_admin_menu() {
    add_options_page(
        'Custom Post Meta API',
        'Post Meta API',
        'manage_options',
        'custom-post-meta',
        'custom_post_meta_settings_page'
    );
}

function custom_post_meta_settings_page() {
    if (isset($_POST['api_key'])) {
        update_option('custom_post_meta_api_key', sanitize_text_field($_POST['api_key']));
        echo '<div class="notice notice-success"><p>API ключ сохранен!</p></div>';
    }
    
    $api_key = get_option('custom_post_meta_api_key', 'bmgiwSmJgRPoXyDX7zNoVv4Vr8Xt1qwI');
    ?>
    <div class="wrap">
        <h1>Custom Post Meta API</h1>
        <form method="post">
            <table class="form-table">
                <tr>
                    <th>API Ключ</th>
                    <td>
                        <input type="text" name="api_key" value="<?php echo esc_attr($api_key); ?>" class="regular-text" />
                        <p class="description">Ключ для доступа к API</p>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
        
        <div class="card">
            <h2>Информация об API</h2>
            <p><strong>Эндпоинт:</strong> <code><?php echo rest_url('custom-post-meta/v1/posts'); ?></code></p>
            <p><strong>Метод:</strong> POST</p>
            <p><strong>Заголовки:</strong> Content-Type: application/json, X-API-Key: <?php echo esc_html($api_key); ?></p>
            
            <h3>Пример запроса:</h3>
            <pre>{
    "title": "Заголовок статьи",
    "content": "&lt;p&gt;Содержимое&lt;/p&gt;",
    "status": "publish",
    "seo_title": "Любой длинный SEO заголовок без ограничений",
    "seo_description": "Любое длинное SEO описание без ограничений",
    "focus_keyword": "ключевое слово",
    "categories": [1, 5],
    "tags": ["тег1", "тег2"]
}</pre>
        </div>
    </div>
    <?php
}