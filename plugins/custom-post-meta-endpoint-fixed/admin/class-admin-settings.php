<?php

/**
 * Класс администрирования плагина
 */

if (!defined('ABSPATH')) {
    exit;
}

class Post_Meta_Endpoint_Admin_Settings
{
    
    public function __construct()
    {
        add_action('admin_menu', [$this, 'add_admin_menu']);
        add_action('admin_init', [$this, 'init_settings']);
    }
    
    /**
     * Добавляем страницу в админ меню
     */
    public function add_admin_menu()
    {
        add_options_page(
            'Custom Post Meta Endpoint',
            'Post Meta API',
            'manage_options',
            'post-meta-endpoint',
            [$this, 'settings_page']
        );
    }
    
    /**
     * Инициализация настроек
     */
    public function init_settings()
    {
        register_setting('post_meta_endpoint_settings', 'post_meta_endpoint_api_key');
        
        add_settings_section(
            'post_meta_endpoint_main',
            'Основные настройки',
            null,
            'post-meta-endpoint'
        );
        
        add_settings_field(
            'api_key',
            'API Ключ',
            [$this, 'api_key_field'],
            'post-meta-endpoint',
            'post_meta_endpoint_main'
        );
    }
    
    /**
     * Поле для API ключа
     */
    public function api_key_field()
    {
        $api_key = get_option('post_meta_endpoint_api_key', '');
        echo '<input type="text" name="post_meta_endpoint_api_key" value="' . esc_attr($api_key) . '" class="regular-text" />';
        echo '<p class="description">API ключ для доступа к эндпоинту создания постов</p>';
        
        if (empty($api_key)) {
            echo '<p><button type="button" class="button" onclick="generateApiKey()">Генерировать новый ключ</button></p>';
            echo '<script>
            function generateApiKey() {
                var key = Math.random().toString(36).substr(2) + Math.random().toString(36).substr(2);
                document.querySelector("input[name=\'post_meta_endpoint_api_key\']").value = key;
            }
            </script>';
        }
    }
    
    /**
     * Страница настроек
     */
    public function settings_page()
    {
        ?>
        <div class="wrap">
            <h1>Custom Post Meta Endpoint (No Limits)</h1>
            
            <form method="post" action="options.php">
                <?php
                settings_fields('post_meta_endpoint_settings');
                do_settings_sections('post-meta-endpoint');
                submit_button();
                ?>
            </form>
            
            <div class="card">
                <h2>Информация об API</h2>
                <p><strong>Эндпоинт для создания постов:</strong> <code><?php echo rest_url('custom-post-meta/v1/posts'); ?></code></p>
                <p><strong>Метод:</strong> POST</p>
                <p><strong>Заголовки:</strong> Content-Type: application/json, X-API-Key: [ваш_ключ]</p>
                
                <h3>Параметры (все необязательные, кроме title):</h3>
                <ul>
                    <li><strong>title</strong> - Заголовок поста (обязательно)</li>
                    <li><strong>content</strong> - Содержимое поста (HTML)</li>
                    <li><strong>excerpt</strong> - Краткое описание</li>
                    <li><strong>slug</strong> - URL слаг</li>
                    <li><strong>status</strong> - Статус: draft, publish, private, pending</li>
                    <li><strong>categories</strong> - Массив ID категорий</li>
                    <li><strong>tags</strong> - Массив названий тегов</li>
                </ul>
                
                <h3>SEO поля (БЕЗ ОГРАНИЧЕНИЙ НА ДЛИНУ):</h3>
                <ul>
                    <li><strong>seo_title</strong> - SEO заголовок</li>
                    <li><strong>seo_description</strong> - SEO описание</li>
                    <li><strong>focus_keyword</strong> - Ключевое слово</li>
                    <li><strong>canonical_url</strong> - Канонический URL</li>
                    <li><strong>og_title, og_description, og_image</strong> - Open Graph</li>
                    <li><strong>twitter_title, twitter_description</strong> - Twitter Cards</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>Пример запроса</h2>
                <pre><code>{
    "title": "Тестовая статья",
    "content": "&lt;p&gt;Содержимое статьи&lt;/p&gt;",
    "status": "publish",
    "seo_title": "Очень длинный SEO заголовок без ограничений",
    "seo_description": "Очень длинное SEO описание без ограничений",
    "categories": [1, 5],
    "tags": ["тег1", "тег2"]
}</code></pre>
            </div>
        </div>
        <?php
    }
}