<?php
/*
Plugin Name: Custom Post Meta Endpoint Enhanced
Description: REST API для создания постов и управления Yoast SEO мета-данными категорий и тегов
Version: 2.0.0
Author: Modified with Category & Tag SEO support
*/

// Блокируем прямой доступ
defined('ABSPATH') or exit;

// Добавляем хук для инициализации API
add_action('rest_api_init', 'custom_post_meta_register_routes');

function custom_post_meta_register_routes() {
    // Существующий эндпоинт для создания постов
    register_rest_route('custom-post-meta/v1', '/posts', array(
        'methods' => 'POST',
        'callback' => 'custom_post_meta_create_post',
        'permission_callback' => 'custom_post_meta_check_permission'
    ));
    
    // Новый эндпоинт для обновления мета-данных категорий
    register_rest_route('custom-post-meta/v1', '/categories/(?P<id>\d+)', array(
        'methods' => 'PUT',
        'callback' => 'custom_post_meta_update_category',
        'permission_callback' => 'custom_post_meta_check_permission',
        'args' => array(
            'id' => array(
                'validate_callback' => function($param, $request, $key) {
                    return is_numeric($param);
                }
            ),
        )
    ));
    
    // Новый эндпоинт для обновления мета-данных тегов
    register_rest_route('custom-post-meta/v1', '/tags/(?P<id>\d+)', array(
        'methods' => 'PUT',
        'callback' => 'custom_post_meta_update_tag',
        'permission_callback' => 'custom_post_meta_check_permission',
        'args' => array(
            'id' => array(
                'validate_callback' => function($param, $request, $key) {
                    return is_numeric($param);
                }
            ),
        )
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

// Создание поста (оригинальная функция)
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

// Новая функция: обновление мета-данных категории
function custom_post_meta_update_category($request) {
    $category_id = $request['id'];
    $params = $request->get_params();
    
    // Проверяем, существует ли категория
    $category = get_term($category_id, 'category');
    if (is_wp_error($category) || !$category) {
        return new WP_Error('category_not_found', 'Category not found', array('status' => 404));
    }
    
    $updated_fields = array();
    
    // Обновляем Yoast SEO поля для категории
    if (!empty($params['seo_title'])) {
        $meta_key = 'wpseo_title';
        $meta_value = sanitize_text_field($params['seo_title']);
        update_term_meta($category_id, $meta_key, $meta_value);
        $updated_fields['seo_title'] = $meta_value;
    }
    
    if (!empty($params['seo_description'])) {
        $meta_key = 'wpseo_desc';
        $meta_value = sanitize_textarea_field($params['seo_description']);
        update_term_meta($category_id, $meta_key, $meta_value);
        $updated_fields['seo_description'] = $meta_value;
    }
    
    if (!empty($params['focus_keyword'])) {
        $meta_key = 'wpseo_focuskw';
        $meta_value = sanitize_text_field($params['focus_keyword']);
        update_term_meta($category_id, $meta_key, $meta_value);
        $updated_fields['focus_keyword'] = $meta_value;
    }
    
    // Обновляем обычное описание категории если передано
    if (!empty($params['description'])) {
        wp_update_term($category_id, 'category', array(
            'description' => sanitize_textarea_field($params['description'])
        ));
        $updated_fields['description'] = sanitize_textarea_field($params['description']);
    }
    
    if (empty($updated_fields)) {
        return new WP_Error('no_data', 'No valid data provided for update', array('status' => 400));
    }
    
    // Возвращаем результат
    return rest_ensure_response(array(
        'success' => true,
        'category_id' => $category_id,
        'category_name' => $category->name,
        'category_url' => get_term_link($category_id, 'category'),
        'updated_fields' => $updated_fields
    ));
}

// Новая функция: обновление мета-данных тега
function custom_post_meta_update_tag($request) {
    $tag_id = $request['id'];
    $params = $request->get_params();
    
    // Проверяем, существует ли тег
    $tag = get_term($tag_id, 'post_tag');
    if (is_wp_error($tag) || !$tag) {
        return new WP_Error('tag_not_found', 'Tag not found', array('status' => 404));
    }
    
    $updated_fields = array();
    
    // Обновляем Yoast SEO поля для тега
    if (!empty($params['seo_title'])) {
        $meta_key = 'wpseo_title';
        $meta_value = sanitize_text_field($params['seo_title']);
        update_term_meta($tag_id, $meta_key, $meta_value);
        $updated_fields['seo_title'] = $meta_value;
    }
    
    if (!empty($params['seo_description'])) {
        $meta_key = 'wpseo_desc';
        $meta_value = sanitize_textarea_field($params['seo_description']);
        update_term_meta($tag_id, $meta_key, $meta_value);
        $updated_fields['seo_description'] = $meta_value;
    }
    
    if (!empty($params['focus_keyword'])) {
        $meta_key = 'wpseo_focuskw';
        $meta_value = sanitize_text_field($params['focus_keyword']);
        update_term_meta($tag_id, $meta_key, $meta_value);
        $updated_fields['focus_keyword'] = $meta_value;
    }
    
    // Обновляем обычное описание тега если передано
    if (!empty($params['description'])) {
        wp_update_term($tag_id, 'post_tag', array(
            'description' => sanitize_textarea_field($params['description'])
        ));
        $updated_fields['description'] = sanitize_textarea_field($params['description']);
    }
    
    if (empty($updated_fields)) {
        return new WP_Error('no_data', 'No valid data provided for update', array('status' => 400));
    }
    
    // Возвращаем результат
    return rest_ensure_response(array(
        'success' => true,
        'tag_id' => $tag_id,
        'tag_name' => $tag->name,
        'tag_url' => get_term_link($tag_id, 'post_tag'),
        'updated_fields' => $updated_fields
    ));
}

// Добавляем страницу настроек
add_action('admin_menu', 'custom_post_meta_admin_menu');

function custom_post_meta_admin_menu() {
    add_options_page(
        'Custom Post Meta API Enhanced',
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
        <h1>Custom Post Meta API Enhanced</h1>
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
            <h2>📝 API Эндпоинты</h2>
            
            <h3>1. Создание поста</h3>
            <p><strong>URL:</strong> <code><?php echo rest_url('custom-post-meta/v1/posts'); ?></code></p>
            <p><strong>Метод:</strong> POST</p>
            <p><strong>Заголовки:</strong> Content-Type: application/json, X-API-Key: <?php echo esc_html($api_key); ?></p>
            
            <h4>Пример запроса:</h4>
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

            <h3>2. Обновление категории</h3>
            <p><strong>URL:</strong> <code><?php echo rest_url('custom-post-meta/v1/categories/{id}'); ?></code></p>
            <p><strong>Метод:</strong> PUT</p>
            <p><strong>Заголовки:</strong> Content-Type: application/json, X-API-Key: <?php echo esc_html($api_key); ?></p>
            
            <h4>Пример запроса:</h4>
            <pre>{
    "seo_title": "SEO заголовок для категории",
    "seo_description": "SEO описание для категории - любой длины без ограничений",
    "focus_keyword": "ключевое слово категории",
    "description": "Обычное описание категории"
}</pre>

            <h3>3. Обновление тега</h3>
            <p><strong>URL:</strong> <code><?php echo rest_url('custom-post-meta/v1/tags/{id}'); ?></code></p>
            <p><strong>Метод:</strong> PUT</p>
            <p><strong>Заголовки:</strong> Content-Type: application/json, X-API-Key: <?php echo esc_html($api_key); ?></p>
            
            <h4>Пример запроса:</h4>
            <pre>{
    "seo_title": "SEO заголовок для тега",
    "seo_description": "SEO описание для тега - любой длины без ограничений",
    "focus_keyword": "ключевое слово тега",
    "description": "Обычное описание тега"
}</pre>

            <h3>📋 Примеры использования CURL</h3>
            
            <h4>Обновить категорию "Разработка" (ID: 131):</h4>
            <pre>curl -X PUT "<?php echo rest_url('custom-post-meta/v1/categories/131'); ?>" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <?php echo esc_html($api_key); ?>" \
  -d '{
    "seo_title": "AI в разработке | AI LYNX",
    "seo_description": "Новости разработки с AI: кодинг-ассистенты, GitHub Copilot, инструменты программирования с ИИ. DevTools, фреймворки машинного обучения и автоматизация разработки.",
    "focus_keyword": "AI разработка"
  }'</pre>

            <h4>Обновить тег "OpenAI" (найти ID через /wp-json/wp/v2/tags):</h4>
            <pre>curl -X PUT "<?php echo rest_url('custom-post-meta/v1/tags/1'); ?>" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <?php echo esc_html($api_key); ?>" \
  -d '{
    "seo_title": "OpenAI новости | AI LYNX",
    "seo_description": "Последние новости OpenAI: GPT модели, ChatGPT обновления, исследования в области ИИ, корпоративные решения и разработка AGI.",
    "focus_keyword": "OpenAI"
  }'</pre>
        </div>
    </div>
    <?php
}