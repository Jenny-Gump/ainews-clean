<?php
/*
Plugin Name: Custom Post Meta Endpoint (No Limits)
Description: REST API для создания WordPress постов с полной поддержкой Yoast SEO мета-полей без ограничений длины
Version: 2.7.0
Author: Gleb Kochergin aka asafeeson.dev (modified)
Author URI: https://asafeeson.dev
Plugin URI: https://asafeeson.dev
Text Domain: custom-post-meta-endpoint
*/

// Предотвращаем прямой доступ
if (!defined('ABSPATH')) {
    exit;
}

// Определяем константы плагина
define('POST_META_ENDPOINT_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('POST_META_ENDPOINT_PLUGIN_URL', plugin_dir_url(__FILE__));
define('POST_META_ENDPOINT_VERSION', '2.7.0');

/**
 * Главный класс плагина
 */
class Custom_Post_Meta_Endpoint_Plugin
{

    private static $instance = null;

    public static function get_instance()
    {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    private function __construct()
    {
        $this->load_dependencies();
        $this->init_hooks();
    }

    /**
     * Загружаем зависимости
     */
    private function load_dependencies()
    {
        $files = [
            'includes/class-validator.php',
            'includes/class-seo-meta.php',
            'includes/class-api-handler.php'
        ];
        
        foreach ($files as $file) {
            $file_path = POST_META_ENDPOINT_PLUGIN_DIR . $file;
            if (file_exists($file_path)) {
                require_once $file_path;
            } else {
                add_action('admin_notices', function() use ($file) {
                    echo '<div class="notice notice-error"><p>Custom Post Meta Endpoint: Файл ' . esc_html($file) . ' не найден!</p></div>';
                });
                return;
            }
        }

        // Загружаем админку только в админ панели
        if (is_admin()) {
            $admin_file = POST_META_ENDPOINT_PLUGIN_DIR . 'admin/class-admin-settings.php';
            if (file_exists($admin_file)) {
                require_once $admin_file;
            }
        }
    }

    /**
     * Инициализируем хуки
     */
    private function init_hooks()
    {
        add_action('init', [$this, 'check_dependencies']);
        add_action('plugins_loaded', [$this, 'init_components']);
    }

    /**
     * Проверяем зависимости
     */
    public function check_dependencies()
    {
        if (!defined('WPSEO_VERSION')) {
            add_action('admin_notices', function () {
                echo '<div class="notice notice-info"><p>Custom Post Meta Endpoint работает лучше с плагином Yoast SEO!</p></div>';
            });
        }
    }

    /**
     * Инициализируем компоненты
     */
    public function init_components()
    {
        // Инициализируем API обработчик
        if (class_exists('Post_Meta_Endpoint_API_Handler')) {
            new Post_Meta_Endpoint_API_Handler();
        }

        // Инициализируем админку
        if (is_admin() && class_exists('Post_Meta_Endpoint_Admin_Settings')) {
            new Post_Meta_Endpoint_Admin_Settings();
        }
    }
}

// Инициализируем плагин
Custom_Post_Meta_Endpoint_Plugin::get_instance();

/**
 * Хук активации плагина
 */
register_activation_hook(__FILE__, function () {
    // Обновляем правила перезаписи URL
    flush_rewrite_rules();
});

/**
 * Хук деактивации плагина
 */
register_deactivation_hook(__FILE__, function () {
    // Очищаем правила перезаписи URL
    flush_rewrite_rules();
});