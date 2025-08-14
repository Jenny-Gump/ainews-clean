<?php
/**
 * Admin Panel Class
 *
 * @package CodeHighlighterCopy
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Class CHC_Admin
 * 
 * Handles admin panel functionality
 */
class CHC_Admin {
    
    /**
     * Settings page slug
     *
     * @var string
     */
    private $settings_page_slug = 'code-highlighter-copy';
    
    /**
     * Constructor
     */
    public function __construct() {
        $this->init_hooks();
    }
    
    /**
     * Initialize hooks
     */
    private function init_hooks() {
        // Add menu items
        add_action('admin_menu', array($this, 'add_admin_menu'));
        
        // Register settings
        add_action('admin_init', array($this, 'register_settings'));
        
        // AJAX handlers
        add_action('wp_ajax_chc_save_settings', array($this, 'ajax_save_settings'));
        add_action('wp_ajax_chc_reset_settings', array($this, 'ajax_reset_settings'));
        add_action('wp_ajax_chc_clear_cache', array($this, 'ajax_clear_cache'));
        add_action('wp_ajax_chc_test_highlighting', array($this, 'ajax_test_highlighting'));
        add_action('wp_ajax_chc_get_statistics', array($this, 'ajax_get_statistics'));
        add_action('wp_ajax_chc_optimize_database', array($this, 'ajax_optimize_database'));
        
        // Add admin notices
        add_action('admin_notices', array($this, 'admin_notices'));
        
        // Add help tabs
        add_action('load-settings_page_' . $this->settings_page_slug, array($this, 'add_help_tabs'));
        
        // Export/Import handlers
        add_action('admin_post_chc_export_settings', array($this, 'export_settings'));
        add_action('admin_post_chc_import_settings', array($this, 'import_settings'));
    }
    
    /**
     * Add admin menu
     */
    public function add_admin_menu() {
        add_options_page(
            __('Code Highlighter Settings', 'code-highlighter-copy'),
            __('Code Highlighter', 'code-highlighter-copy'),
            'manage_options',
            $this->settings_page_slug,
            array($this, 'render_settings_page')
        );
        
        // Add to Tools menu as well for easier access
        add_management_page(
            __('Code Highlighter Tools', 'code-highlighter-copy'),
            __('Code Highlighter', 'code-highlighter-copy'),
            'manage_options',
            $this->settings_page_slug . '-tools',
            array($this, 'render_tools_page')
        );
    }
    
    /**
     * Register settings
     */
    public function register_settings() {
        // General settings section
        add_settings_section(
            'chc_general_settings',
            __('General Settings', 'code-highlighter-copy'),
            array($this, 'render_general_section'),
            $this->settings_page_slug
        );
        
        // Appearance settings section
        add_settings_section(
            'chc_appearance_settings',
            __('Appearance Settings', 'code-highlighter-copy'),
            array($this, 'render_appearance_section'),
            $this->settings_page_slug
        );
        
        // Advanced settings section
        add_settings_section(
            'chc_advanced_settings',
            __('Advanced Settings', 'code-highlighter-copy'),
            array($this, 'render_advanced_section'),
            $this->settings_page_slug
        );
        
        // Register individual settings
        $this->register_general_settings();
        $this->register_appearance_settings();
        $this->register_advanced_settings();
    }
    
    /**
     * Register general settings
     */
    private function register_general_settings() {
        $settings = array(
            'enable_on_frontend' => array(
                'type' => 'checkbox',
                'label' => __('Enable on Frontend', 'code-highlighter-copy'),
                'description' => __('Enable code highlighting on the frontend of your site.', 'code-highlighter-copy'),
                'default' => true,
            ),
            'enable_in_comments' => array(
                'type' => 'checkbox',
                'label' => __('Enable in Comments', 'code-highlighter-copy'),
                'description' => __('Allow code highlighting in comments.', 'code-highlighter-copy'),
                'default' => false,
            ),
            'auto_detect_language' => array(
                'type' => 'checkbox',
                'label' => __('Auto-detect Language', 'code-highlighter-copy'),
                'description' => __('Automatically detect programming language from code content.', 'code-highlighter-copy'),
                'default' => false,
            ),
        );
        
        foreach ($settings as $key => $setting) {
            register_setting(
                'chc_settings',
                'chc_' . $key,
                array(
                    'type' => $setting['type'] === 'checkbox' ? 'boolean' : 'string',
                    'default' => $setting['default'],
                    'sanitize_callback' => array($this, 'sanitize_' . $setting['type']),
                )
            );
            
            add_settings_field(
                'chc_' . $key,
                $setting['label'],
                array($this, 'render_' . $setting['type'] . '_field'),
                $this->settings_page_slug,
                'chc_general_settings',
                array(
                    'key' => $key,
                    'setting' => $setting,
                )
            );
        }
    }
    
    /**
     * Register appearance settings
     */
    private function register_appearance_settings() {
        $settings = array(
            'theme' => array(
                'type' => 'select',
                'label' => __('Color Theme', 'code-highlighter-copy'),
                'description' => __('Select the color theme for code highlighting.', 'code-highlighter-copy'),
                'options' => $this->get_available_themes(),
                'default' => 'prism-tomorrow',
            ),
            'line_numbers' => array(
                'type' => 'checkbox',
                'label' => __('Show Line Numbers', 'code-highlighter-copy'),
                'description' => __('Display line numbers in code blocks.', 'code-highlighter-copy'),
                'default' => true,
            ),
            'copy_button' => array(
                'type' => 'checkbox',
                'label' => __('Show Copy Button', 'code-highlighter-copy'),
                'description' => __('Display a copy button for code blocks.', 'code-highlighter-copy'),
                'default' => true,
            ),
            'copy_button_text' => array(
                'type' => 'text',
                'label' => __('Copy Button Text', 'code-highlighter-copy'),
                'description' => __('Text to display on the copy button.', 'code-highlighter-copy'),
                'default' => __('Copy', 'code-highlighter-copy'),
            ),
            'copied_text' => array(
                'type' => 'text',
                'label' => __('Copied Confirmation Text', 'code-highlighter-copy'),
                'description' => __('Text to display when code is copied.', 'code-highlighter-copy'),
                'default' => __('Copied!', 'code-highlighter-copy'),
            ),
            'show_language_label' => array(
                'type' => 'checkbox',
                'label' => __('Show Language Label', 'code-highlighter-copy'),
                'description' => __('Display the programming language name.', 'code-highlighter-copy'),
                'default' => true,
            ),
            'copy_button_position' => array(
                'type' => 'select',
                'label' => __('Copy Button Position', 'code-highlighter-copy'),
                'description' => __('Position of the copy button.', 'code-highlighter-copy'),
                'options' => array(
                    'top-right' => __('Top Right', 'code-highlighter-copy'),
                    'top-left' => __('Top Left', 'code-highlighter-copy'),
                    'bottom-right' => __('Bottom Right', 'code-highlighter-copy'),
                    'bottom-left' => __('Bottom Left', 'code-highlighter-copy'),
                ),
                'default' => 'top-right',
            ),
            'fullscreen_mode' => array(
                'type' => 'checkbox',
                'label' => __('Fullscreen Mode', 'code-highlighter-copy'),
                'description' => __('Enable fullscreen mode button.', 'code-highlighter-copy'),
                'default' => false,
            ),
            'font_size' => array(
                'type' => 'number',
                'label' => __('Font Size', 'code-highlighter-copy'),
                'description' => __('Font size for code blocks (in pixels).', 'code-highlighter-copy'),
                'default' => 14,
            ),
            'font_family' => array(
                'type' => 'select',
                'label' => __('Font Family', 'code-highlighter-copy'),
                'description' => __('Font family for code blocks.', 'code-highlighter-copy'),
                'options' => array(
                    'default' => __('System Default', 'code-highlighter-copy'),
                    'Monaco, monospace' => 'Monaco',
                    'Consolas, monospace' => 'Consolas',
                    '"Courier New", monospace' => 'Courier New',
                    '"Source Code Pro", monospace' => 'Source Code Pro',
                    '"Fira Code", monospace' => 'Fira Code',
                    'Menlo, monospace' => 'Menlo',
                    '"JetBrains Mono", monospace' => 'JetBrains Mono',
                ),
                'default' => 'default',
            ),
            'max_height' => array(
                'type' => 'number',
                'label' => __('Max Height', 'code-highlighter-copy'),
                'description' => __('Maximum height before scrollbar (in pixels, 0 for no limit).', 'code-highlighter-copy'),
                'default' => 500,
            ),
            'header_style' => array(
                'type' => 'select',
                'label' => __('Header Style', 'code-highlighter-copy'),
                'description' => __('Style of the code block header.', 'code-highlighter-copy'),
                'options' => array(
                    'gradient' => __('Gradient', 'code-highlighter-copy'),
                    'solid' => __('Solid Color', 'code-highlighter-copy'),
                    'minimal' => __('Minimal', 'code-highlighter-copy'),
                    'none' => __('No Header', 'code-highlighter-copy'),
                ),
                'default' => 'gradient',
            ),
            'border_radius' => array(
                'type' => 'number',
                'label' => __('Border Radius', 'code-highlighter-copy'),
                'description' => __('Border radius for code blocks (in pixels).', 'code-highlighter-copy'),
                'default' => 4,
            ),
        );
        
        foreach ($settings as $key => $setting) {
            register_setting(
                'chc_settings',
                'chc_' . $key,
                array(
                    'type' => $this->get_setting_type($setting['type']),
                    'default' => $setting['default'],
                    'sanitize_callback' => array($this, 'sanitize_' . $setting['type']),
                )
            );
            
            add_settings_field(
                'chc_' . $key,
                $setting['label'],
                array($this, 'render_' . $setting['type'] . '_field'),
                $this->settings_page_slug,
                'chc_appearance_settings',
                array(
                    'key' => $key,
                    'setting' => $setting,
                )
            );
        }
    }
    
    /**
     * Register advanced settings
     */
    private function register_advanced_settings() {
        $settings = array(
            'cache_enabled' => array(
                'type' => 'checkbox',
                'label' => __('Enable Caching', 'code-highlighter-copy'),
                'description' => __('Cache highlighted code blocks for better performance.', 'code-highlighter-copy'),
                'default' => true,
            ),
            'cache_duration' => array(
                'type' => 'number',
                'label' => __('Cache Duration', 'code-highlighter-copy'),
                'description' => __('Cache expiration time in seconds (86400 = 24 hours).', 'code-highlighter-copy'),
                'default' => 86400,
            ),
            'lazy_loading' => array(
                'type' => 'checkbox',
                'label' => __('Lazy Loading', 'code-highlighter-copy'),
                'description' => __('Enable lazy loading for large code blocks.', 'code-highlighter-copy'),
                'default' => true,
            ),
            'minify_assets' => array(
                'type' => 'checkbox',
                'label' => __('Minify Assets', 'code-highlighter-copy'),
                'description' => __('Use minified CSS/JS files.', 'code-highlighter-copy'),
                'default' => false,
            ),
            'enable_shortcuts' => array(
                'type' => 'checkbox',
                'label' => __('Enable Shortcuts', 'code-highlighter-copy'),
                'description' => __('Enable keyboard shortcuts.', 'code-highlighter-copy'),
                'default' => false,
            ),
            'supported_languages' => array(
                'type' => 'multiselect',
                'label' => __('Supported Languages', 'code-highlighter-copy'),
                'description' => __('Select which programming languages to support.', 'code-highlighter-copy'),
                'options' => $this->get_available_languages(),
                'default' => array('markup', 'css', 'javascript', 'php', 'python'),
            ),
            'load_assets' => array(
                'type' => 'select',
                'label' => __('Load Assets', 'code-highlighter-copy'),
                'description' => __('Control when plugin assets are loaded.', 'code-highlighter-copy'),
                'options' => array(
                    'auto' => __('Auto-detect (recommended)', 'code-highlighter-copy'),
                    'always' => __('Always load on all pages', 'code-highlighter-copy'),
                    'posts' => __('Only on posts and pages', 'code-highlighter-copy'),
                    'manual' => __('Manual', 'code-highlighter-copy'),
                ),
                'default' => 'auto',
            ),
            'custom_css' => array(
                'type' => 'textarea',
                'label' => __('Custom CSS', 'code-highlighter-copy'),
                'description' => __('Add custom CSS styles for code blocks.', 'code-highlighter-copy'),
                'default' => '',
            ),
        );
        
        foreach ($settings as $key => $setting) {
            register_setting(
                'chc_settings',
                'chc_' . $key,
                array(
                    'type' => $this->get_setting_type($setting['type']),
                    'default' => $setting['default'],
                    'sanitize_callback' => array($this, 'sanitize_' . $setting['type']),
                )
            );
            
            add_settings_field(
                'chc_' . $key,
                $setting['label'],
                array($this, 'render_' . $setting['type'] . '_field'),
                $this->settings_page_slug,
                'chc_advanced_settings',
                array(
                    'key' => $key,
                    'setting' => $setting,
                )
            );
        }
    }
    
    /**
     * Render settings page
     */
    public function render_settings_page() {
        if (!current_user_can('manage_options')) {
            wp_die(__('You do not have sufficient permissions to access this page.', 'code-highlighter-copy'));
        }
        
        require_once CHC_PLUGIN_DIR . 'admin/views/settings-page.php';
    }
    
    /**
     * Render tools page
     */
    public function render_tools_page() {
        if (!current_user_can('manage_options')) {
            wp_die(__('You do not have sufficient permissions to access this page.', 'code-highlighter-copy'));
        }
        
        require_once CHC_PLUGIN_DIR . 'admin/views/tools-page.php';
    }
    
    /**
     * Render field methods
     */
    public function render_checkbox_field($args) {
        $key = $args['key'];
        $setting = $args['setting'];
        $value = get_option('chc_' . $key, $setting['default']);
        
        printf(
            '<input type="checkbox" id="chc_%1$s" name="chc_%1$s" value="1" %2$s />
            <label for="chc_%1$s">%3$s</label>',
            esc_attr($key),
            checked($value, true, false),
            esc_html($setting['description'])
        );
    }
    
    public function render_text_field($args) {
        $key = $args['key'];
        $setting = $args['setting'];
        $value = get_option('chc_' . $key, $setting['default']);
        
        printf(
            '<input type="text" id="chc_%1$s" name="chc_%1$s" value="%2$s" class="regular-text" />
            <p class="description">%3$s</p>',
            esc_attr($key),
            esc_attr($value),
            esc_html($setting['description'])
        );
    }
    
    public function render_number_field($args) {
        $key = $args['key'];
        $setting = $args['setting'];
        $value = get_option('chc_' . $key, $setting['default']);
        
        printf(
            '<input type="number" id="chc_%1$s" name="chc_%1$s" value="%2$s" class="regular-text" min="0" />
            <p class="description">%3$s</p>',
            esc_attr($key),
            esc_attr($value),
            esc_html($setting['description'])
        );
    }
    
    public function render_select_field($args) {
        $key = $args['key'];
        $setting = $args['setting'];
        $value = get_option('chc_' . $key, $setting['default']);
        
        echo '<select id="chc_' . esc_attr($key) . '" name="chc_' . esc_attr($key) . '">';
        foreach ($setting['options'] as $option_value => $option_label) {
            printf(
                '<option value="%1$s" %2$s>%3$s</option>',
                esc_attr($option_value),
                selected($value, $option_value, false),
                esc_html($option_label)
            );
        }
        echo '</select>';
        echo '<p class="description">' . esc_html($setting['description']) . '</p>';
    }
    
    public function render_multiselect_field($args) {
        $key = $args['key'];
        $setting = $args['setting'];
        $values = get_option('chc_' . $key, $setting['default']);
        
        echo '<select id="chc_' . esc_attr($key) . '" name="chc_' . esc_attr($key) . '[]" multiple="multiple" class="chc-multiselect">';
        foreach ($setting['options'] as $option_value => $option_label) {
            printf(
                '<option value="%1$s" %2$s>%3$s</option>',
                esc_attr($option_value),
                selected(in_array($option_value, (array) $values, true), true, false),
                esc_html($option_label)
            );
        }
        echo '</select>';
        echo '<p class="description">' . esc_html($setting['description']) . '</p>';
    }
    
    public function render_textarea_field($args) {
        $key = $args['key'];
        $setting = $args['setting'];
        $value = get_option('chc_' . $key, $setting['default']);
        
        printf(
            '<textarea id="chc_%1$s" name="chc_%1$s" rows="10" cols="50" class="large-text code">%2$s</textarea>
            <p class="description">%3$s</p>',
            esc_attr($key),
            esc_textarea($value),
            esc_html($setting['description'])
        );
    }
    
    /**
     * Render section descriptions
     */
    public function render_general_section() {
        echo '<p>' . __('Configure general plugin settings.', 'code-highlighter-copy') . '</p>';
    }
    
    public function render_appearance_section() {
        echo '<p>' . __('Customize the appearance of code blocks.', 'code-highlighter-copy') . '</p>';
    }
    
    public function render_advanced_section() {
        echo '<p>' . __('Advanced settings for power users.', 'code-highlighter-copy') . '</p>';
    }
    
    /**
     * Sanitization callbacks
     */
    public function sanitize_checkbox($value) {
        return (bool) $value;
    }
    
    public function sanitize_text($value) {
        // Limit text field length
        $value = sanitize_text_field($value);
        return substr($value, 0, 200); // Max 200 characters for text fields
    }
    
    public function sanitize_number($value) {
        $value = absint($value);
        return min(999999, $value); // Set reasonable max limit
    }
    
    public function sanitize_select($value) {
        // This should validate against allowed options
        // but we're already doing that in sanitize_setting_value
        return sanitize_text_field($value);
    }
    
    public function sanitize_multiselect($value) {
        if (!is_array($value)) {
            return array();
        }
        
        // Limit array size
        $value = array_slice($value, 0, 50); // Max 50 items
        
        return array_map('sanitize_text_field', $value);
    }
    
    public function sanitize_textarea($value) {
        // Remove any potentially dangerous tags and scripts
        $value = wp_kses($value, array(
            'a' => array('href' => array(), 'title' => array()),
            'br' => array(),
            'em' => array(),
            'strong' => array(),
            'code' => array(),
            'pre' => array(),
            'p' => array(),
            'span' => array('style' => array()),
            'div' => array('style' => array())
        ));
        
        // Limit length
        return substr($value, 0, 10000); // Max 10KB
    }
    
    /**
     * AJAX handlers
     */
    public function ajax_save_settings() {
        // Verify nonce
        if (!check_ajax_referer('chc_admin_nonce', 'nonce', false)) {
            wp_send_json_error(__('Security check failed.', 'code-highlighter-copy'), 403);
        }
        
        // Check permissions
        if (!current_user_can('manage_options')) {
            wp_send_json_error(__('Insufficient permissions.', 'code-highlighter-copy'), 403);
        }
        
        // Rate limiting
        $user_id = get_current_user_id();
        $transient_key = 'chc_ajax_limit_' . $user_id;
        $requests = get_transient($transient_key) ?: 0;
        
        if ($requests > 10) { // Max 10 requests per minute
            wp_send_json_error(__('Too many requests. Please wait before trying again.', 'code-highlighter-copy'), 429);
        }
        
        set_transient($transient_key, $requests + 1, 60);
        
        // Process and save settings with proper sanitization
        $settings = isset($_POST['settings']) ? $_POST['settings'] : array();
        
        if (!is_array($settings)) {
            wp_send_json_error(__('Invalid settings format.', 'code-highlighter-copy'), 400);
        }
        
        // Whitelist of allowed settings keys
        $allowed_settings = $this->get_allowed_settings_keys();
        
        foreach ($settings as $key => $value) {
            // Sanitize the key
            $sanitized_key = sanitize_key($key);
            
            // Check if key is in whitelist
            if (!in_array($sanitized_key, $allowed_settings, true)) {
                continue; // Skip non-whitelisted settings
            }
            
            // Sanitize value based on setting type
            $sanitized_value = $this->sanitize_setting_value($sanitized_key, $value);
            
            // Update option with sanitized values
            update_option($sanitized_key, $sanitized_value);
        }
        
        wp_send_json_success(__('Settings saved successfully!', 'code-highlighter-copy'));
    }
    
    public function ajax_reset_settings() {
        // Verify nonce
        if (!check_ajax_referer('chc_admin_nonce', 'nonce', false)) {
            wp_send_json_error(__('Security check failed.', 'code-highlighter-copy'), 403);
        }
        
        // Check permissions
        if (!current_user_can('manage_options')) {
            wp_send_json_error(__('Insufficient permissions.', 'code-highlighter-copy'), 403);
        }
        
        // Rate limiting
        $user_id = get_current_user_id();
        $transient_key = 'chc_reset_limit_' . $user_id;
        $requests = get_transient($transient_key) ?: 0;
        
        if ($requests > 3) { // Max 3 resets per hour
            wp_send_json_error(__('Too many reset attempts. Please wait before trying again.', 'code-highlighter-copy'), 429);
        }
        
        set_transient($transient_key, $requests + 1, HOUR_IN_SECONDS);
        
        // Reset options safely
        chc_reset_options();
        
        // Log the reset action
        if (function_exists('wp_insert_log')) {
            wp_insert_log(array(
                'action' => 'chc_settings_reset',
                'user_id' => $user_id,
                'timestamp' => current_time('mysql')
            ));
        }
        
        wp_send_json_success(__('Settings reset to defaults!', 'code-highlighter-copy'));
    }
    
    public function ajax_clear_cache() {
        // Verify nonce
        if (!check_ajax_referer('chc_admin_nonce', 'nonce', false)) {
            wp_send_json_error(__('Security check failed.', 'code-highlighter-copy'), 403);
        }
        
        // Check permissions
        if (!current_user_can('manage_options')) {
            wp_send_json_error(__('Insufficient permissions.', 'code-highlighter-copy'), 403);
        }
        
        // Rate limiting
        $user_id = get_current_user_id();
        $transient_key = 'chc_cache_clear_limit_' . $user_id;
        $requests = get_transient($transient_key) ?: 0;
        
        if ($requests > 5) { // Max 5 cache clears per hour
            wp_send_json_error(__('Too many cache clear requests. Please wait before trying again.', 'code-highlighter-copy'), 429);
        }
        
        set_transient($transient_key, $requests + 1, HOUR_IN_SECONDS);
        
        // Clear transients and cache safely
        global $wpdb;
        $cleared = $wpdb->query(
            $wpdb->prepare(
                "DELETE FROM {$wpdb->options} WHERE option_name LIKE %s OR option_name LIKE %s",
                '_transient_chc_%',
                '_transient_timeout_chc_%'
            )
        );
        
        wp_cache_flush();
        
        wp_send_json_success(array(
            'message' => __('Cache cleared successfully!', 'code-highlighter-copy'),
            'items_cleared' => $cleared
        ));
    }
    
    public function ajax_test_highlighting() {
        // Verify nonce
        if (!check_ajax_referer('chc_admin_nonce', 'nonce', false)) {
            wp_send_json_error(__('Security check failed.', 'code-highlighter-copy'), 403);
        }
        
        // Check permissions
        if (!current_user_can('edit_posts')) {
            wp_send_json_error(__('Insufficient permissions.', 'code-highlighter-copy'), 403);
        }
        
        // Rate limiting
        $user_id = get_current_user_id();
        $transient_key = 'chc_test_limit_' . $user_id;
        $requests = get_transient($transient_key) ?: 0;
        
        if ($requests > 20) { // Max 20 tests per minute
            wp_send_json_error(__('Too many test requests. Please wait before trying again.', 'code-highlighter-copy'), 429);
        }
        
        set_transient($transient_key, $requests + 1, 60);
        
        // Sanitize inputs
        $code = isset($_POST['code']) ? wp_kses_post(wp_unslash($_POST['code'])) : '';
        $language = isset($_POST['language']) ? sanitize_text_field($_POST['language']) : 'javascript';
        
        // Validate language against whitelist
        $allowed_languages = array_keys($this->get_available_languages());
        if (!in_array($language, $allowed_languages, true)) {
            $language = 'javascript'; // Default to JavaScript if invalid
        }
        
        // Limit code size
        if (strlen($code) > 50000) { // Max 50KB
            wp_send_json_error(__('Code is too large. Maximum 50KB allowed.', 'code-highlighter-copy'), 400);
        }
        
        // Generate preview using proper class loading
        if (!CHC_Loader::class_exists('CHC_Shortcodes')) {
            wp_send_json_error(__('Shortcode class not available.', 'code-highlighter-copy'), 500);
            return;
        }
        
        $shortcode = new CHC_Shortcodes();
        $html = $shortcode->render_code_shortcode(
            array('language' => $language),
            $code
        );
        
        wp_send_json_success($html);
    }
    
    /**
     * Export settings
     */
    public function export_settings() {
        // Verify nonce
        if (!isset($_GET['_wpnonce']) || !wp_verify_nonce($_GET['_wpnonce'], 'chc_export_settings')) {
            wp_die(__('Security check failed.', 'code-highlighter-copy'), 403);
        }
        
        // Check permissions
        if (!current_user_can('manage_options')) {
            wp_die(__('Insufficient permissions.', 'code-highlighter-copy'), 403);
        }
        
        // Rate limiting
        $user_id = get_current_user_id();
        $transient_key = 'chc_export_limit_' . $user_id;
        $requests = get_transient($transient_key) ?: 0;
        
        if ($requests > 10) { // Max 10 exports per hour
            wp_die(__('Too many export requests. Please wait before trying again.', 'code-highlighter-copy'), 429);
        }
        
        set_transient($transient_key, $requests + 1, HOUR_IN_SECONDS);
        
        // Get settings safely
        $settings = chc_get_all_options();
        
        // Sanitize all settings before export
        $sanitized_settings = array();
        foreach ($settings as $key => $value) {
            $sanitized_key = sanitize_key($key);
            $sanitized_settings[$sanitized_key] = $this->sanitize_setting_value($sanitized_key, $value);
        }
        
        $export_data = array(
            'plugin' => 'code-highlighter-copy',
            'version' => CHC_VERSION,
            'settings' => $sanitized_settings,
            'exported' => current_time('mysql'),
            'site_url' => home_url(),
            'hash' => wp_hash(serialize($sanitized_settings))
        );
        
        // Set proper headers
        nocache_headers();
        header('Content-Type: application/json; charset=utf-8');
        header('Content-Disposition: attachment; filename="chc-settings-' . date('Y-m-d-His') . '.json"');
        header('X-Content-Type-Options: nosniff');
        
        echo wp_json_encode($export_data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
        exit;
    }
    
    /**
     * Import settings
     */
    public function import_settings() {
        // Verify nonce
        if (!isset($_POST['_wpnonce']) || !wp_verify_nonce($_POST['_wpnonce'], 'chc_import_settings')) {
            wp_die(__('Security check failed.', 'code-highlighter-copy'), 403);
        }
        
        // Check permissions
        if (!current_user_can('manage_options')) {
            wp_die(__('Insufficient permissions.', 'code-highlighter-copy'), 403);
        }
        
        // Rate limiting
        $user_id = get_current_user_id();
        $transient_key = 'chc_import_limit_' . $user_id;
        $requests = get_transient($transient_key) ?: 0;
        
        if ($requests > 5) { // Max 5 imports per hour
            wp_redirect(add_query_arg('error', 'rate_limit', wp_get_referer()));
            exit;
        }
        
        set_transient($transient_key, $requests + 1, HOUR_IN_SECONDS);
        
        // Validate file upload
        if (empty($_FILES['import_file']['tmp_name'])) {
            wp_redirect(add_query_arg('error', 'no_file', wp_get_referer()));
            exit;
        }
        
        $uploaded_file = $_FILES['import_file'];
        
        // Check file type
        $file_type = wp_check_filetype($uploaded_file['name']);
        if ($file_type['ext'] !== 'json') {
            wp_redirect(add_query_arg('error', 'invalid_type', wp_get_referer()));
            exit;
        }
        
        // Check MIME type
        $finfo = finfo_open(FILEINFO_MIME_TYPE);
        $mime_type = finfo_file($finfo, $uploaded_file['tmp_name']);
        finfo_close($finfo);
        
        if (!in_array($mime_type, array('application/json', 'text/plain'), true)) {
            wp_redirect(add_query_arg('error', 'invalid_mime', wp_get_referer()));
            exit;
        }
        
        // Check file size (max 1MB)
        if ($uploaded_file['size'] > 1048576) {
            wp_redirect(add_query_arg('error', 'file_too_large', wp_get_referer()));
            exit;
        }
        
        // Read and validate JSON
        $file_content = file_get_contents($uploaded_file['tmp_name']);
        if ($file_content === false) {
            wp_redirect(add_query_arg('error', 'read_error', wp_get_referer()));
            exit;
        }
        
        // Decode JSON
        $import_data = json_decode($file_content, true);
        
        // Validate JSON structure
        if (json_last_error() !== JSON_ERROR_NONE) {
            wp_redirect(add_query_arg('error', 'invalid_json', wp_get_referer()));
            exit;
        }
        
        if (!$import_data || !isset($import_data['settings']) || !isset($import_data['plugin'])) {
            wp_redirect(add_query_arg('error', 'invalid_structure', wp_get_referer()));
            exit;
        }
        
        // Verify plugin match
        if ($import_data['plugin'] !== 'code-highlighter-copy') {
            wp_redirect(add_query_arg('error', 'wrong_plugin', wp_get_referer()));
            exit;
        }
        
        // Verify hash if present
        if (isset($import_data['hash'])) {
            $calculated_hash = wp_hash(serialize($import_data['settings']));
            if ($calculated_hash !== $import_data['hash']) {
                wp_redirect(add_query_arg('error', 'hash_mismatch', wp_get_referer()));
                exit;
            }
        }
        
        // Get whitelist of allowed settings
        $allowed_settings = $this->get_allowed_settings_keys();
        
        // Import settings with sanitization
        foreach ($import_data['settings'] as $key => $value) {
            // Sanitize key
            $sanitized_key = sanitize_key($key);
            
            // Skip if not in whitelist
            if (!in_array($sanitized_key, $allowed_settings, true)) {
                continue;
            }
            
            // Add prefix if needed
            if (strpos($sanitized_key, 'chc_') !== 0) {
                $sanitized_key = 'chc_' . $sanitized_key;
            }
            
            // Sanitize value based on type
            $sanitized_value = $this->sanitize_setting_value($sanitized_key, $value);
            
            // Update option
            update_option($sanitized_key, $sanitized_value);
        }
        
        // Log import action
        if (function_exists('wp_insert_log')) {
            wp_insert_log(array(
                'action' => 'chc_settings_import',
                'user_id' => $user_id,
                'timestamp' => current_time('mysql'),
                'source' => isset($import_data['site_url']) ? $import_data['site_url'] : 'unknown'
            ));
        }
        
        wp_redirect(add_query_arg('success', 'imported', wp_get_referer()));
        exit;
    }
    
    /**
     * Add help tabs
     */
    public function add_help_tabs() {
        $screen = get_current_screen();
        
        $screen->add_help_tab(array(
            'id' => 'chc_overview',
            'title' => __('Overview', 'code-highlighter-copy'),
            'content' => $this->get_help_content('overview'),
        ));
        
        $screen->add_help_tab(array(
            'id' => 'chc_shortcodes',
            'title' => __('Shortcodes', 'code-highlighter-copy'),
            'content' => $this->get_help_content('shortcodes'),
        ));
        
        $screen->add_help_tab(array(
            'id' => 'chc_languages',
            'title' => __('Supported Languages', 'code-highlighter-copy'),
            'content' => $this->get_help_content('languages'),
        ));
    }
    
    /**
     * Get help content
     *
     * @param string $tab Tab identifier
     * @return string HTML content
     */
    private function get_help_content($tab) {
        ob_start();
        
        switch ($tab) {
            case 'overview':
                ?>
                <h3><?php _e('Code Highlighter Overview', 'code-highlighter-copy'); ?></h3>
                <p><?php _e('This plugin provides syntax highlighting for code blocks with a convenient copy button.', 'code-highlighter-copy'); ?></p>
                <p><?php _e('Features include:', 'code-highlighter-copy'); ?></p>
                <ul>
                    <li><?php _e('Multiple color themes', 'code-highlighter-copy'); ?></li>
                    <li><?php _e('Line numbers', 'code-highlighter-copy'); ?></li>
                    <li><?php _e('Copy to clipboard functionality', 'code-highlighter-copy'); ?></li>
                    <li><?php _e('Support for many programming languages', 'code-highlighter-copy'); ?></li>
                </ul>
                <?php
                break;
                
            case 'shortcodes':
                ?>
                <h3><?php _e('Using Shortcodes', 'code-highlighter-copy'); ?></h3>
                <p><?php _e('Basic usage:', 'code-highlighter-copy'); ?></p>
                <pre>[code language="javascript"]
// Your code here
[/code]</pre>
                <p><?php _e('With options:', 'code-highlighter-copy'); ?></p>
                <pre>[code language="php" line_numbers="true" copy_button="true" title="Example.php"]
// Your PHP code
[/code]</pre>
                <?php
                break;
                
            case 'languages':
                ?>
                <h3><?php _e('Supported Languages', 'code-highlighter-copy'); ?></h3>
                <p><?php _e('The following programming languages are supported:', 'code-highlighter-copy'); ?></p>
                <ul>
                    <?php
                    foreach ($this->get_available_languages() as $code => $name) {
                        echo '<li><code>' . esc_html($code) . '</code> - ' . esc_html($name) . '</li>';
                    }
                    ?>
                </ul>
                <?php
                break;
        }
        
        return ob_get_clean();
    }
    
    /**
     * Display admin notices
     */
    public function admin_notices() {
        if (!chc_is_settings_page()) {
            return;
        }
        
        // Check for import/export messages
        if (isset($_GET['success'])) {
            $message = '';
            switch ($_GET['success']) {
                case 'imported':
                    $message = __('Settings imported successfully!', 'code-highlighter-copy');
                    break;
            }
            
            if ($message) {
                echo '<div class="notice notice-success is-dismissible"><p>' . esc_html($message) . '</p></div>';
            }
        }
        
        if (isset($_GET['error'])) {
            $message = '';
            switch ($_GET['error']) {
                case 'no_file':
                    $message = __('No file selected for import.', 'code-highlighter-copy');
                    break;
                case 'invalid_file':
                    $message = __('Invalid import file format.', 'code-highlighter-copy');
                    break;
            }
            
            if ($message) {
                echo '<div class="notice notice-error is-dismissible"><p>' . esc_html($message) . '</p></div>';
            }
        }
    }
    
    /**
     * Get setting type for register_setting
     *
     * @param string $type Field type
     * @return string WordPress setting type
     */
    private function get_setting_type($type) {
        switch ($type) {
            case 'checkbox':
                return 'boolean';
            case 'number':
                return 'integer';
            default:
                return 'string';
        }
    }
    
    /**
     * Get available languages
     *
     * @return array
     */
    private function get_available_languages() {
        return array(
            'markup' => __('HTML/XML', 'code-highlighter-copy'),
            'css' => __('CSS', 'code-highlighter-copy'),
            'javascript' => __('JavaScript', 'code-highlighter-copy'),
            'php' => __('PHP', 'code-highlighter-copy'),
            'python' => __('Python', 'code-highlighter-copy'),
            'sql' => __('SQL', 'code-highlighter-copy'),
            'bash' => __('Bash/Shell', 'code-highlighter-copy'),
            'json' => __('JSON', 'code-highlighter-copy'),
            'yaml' => __('YAML', 'code-highlighter-copy'),
            'markdown' => __('Markdown', 'code-highlighter-copy'),
            'java' => __('Java', 'code-highlighter-copy'),
            'c' => __('C', 'code-highlighter-copy'),
            'cpp' => __('C++', 'code-highlighter-copy'),
            'csharp' => __('C#', 'code-highlighter-copy'),
            'go' => __('Go', 'code-highlighter-copy'),
            'rust' => __('Rust', 'code-highlighter-copy'),
            'typescript' => __('TypeScript', 'code-highlighter-copy'),
            'ruby' => __('Ruby', 'code-highlighter-copy'),
            'swift' => __('Swift', 'code-highlighter-copy'),
            'kotlin' => __('Kotlin', 'code-highlighter-copy'),
        );
    }
    
    /**
     * Get available themes
     *
     * @return array
     */
    private function get_available_themes() {
        return array(
            'prism' => __('Default', 'code-highlighter-copy'),
            'prism-tomorrow' => __('Tomorrow Night', 'code-highlighter-copy'),
            'prism-okaidia' => __('Okaidia', 'code-highlighter-copy'),
            'prism-twilight' => __('Twilight', 'code-highlighter-copy'),
            'prism-coy' => __('Coy', 'code-highlighter-copy'),
            'prism-solarized' => __('Solarized Light', 'code-highlighter-copy'),
            'prism-dark' => __('Dark', 'code-highlighter-copy'),
            'prism-funky' => __('Funky', 'code-highlighter-copy'),
        );
    }
    
    /**
     * AJAX handler for getting statistics
     */
    public function ajax_get_statistics() {
        // Verify nonce
        if (!check_ajax_referer('chc_admin_nonce', 'nonce', false)) {
            wp_send_json_error(__('Security check failed.', 'code-highlighter-copy'), 403);
        }
        
        // Check permissions
        if (!current_user_can('manage_options')) {
            wp_send_json_error(__('Insufficient permissions.', 'code-highlighter-copy'), 403);
        }
        
        // Rate limiting
        $user_id = get_current_user_id();
        $transient_key = 'chc_stats_limit_' . $user_id;
        $requests = get_transient($transient_key) ?: 0;
        
        if ($requests > 30) { // Max 30 requests per minute
            wp_send_json_error(__('Too many requests. Please wait before trying again.', 'code-highlighter-copy'), 429);
        }
        
        set_transient($transient_key, $requests + 1, 60)
        
        global $wpdb;
        
        $stats = array();
        
        // Get total code blocks (search for shortcodes in posts)
        $code_blocks_query = "
            SELECT COUNT(*) as total 
            FROM {$wpdb->posts} 
            WHERE post_status = 'publish' 
            AND (post_content LIKE '%[code%' OR post_content LIKE '%<pre%' OR post_content LIKE '%```%')
        ";
        $total_blocks = $wpdb->get_var($code_blocks_query);
        $stats['total_blocks'] = intval($total_blocks);
        
        // Get language usage statistics
        $languages = array();
        $lang_patterns = array(
            'php' => '[code language="php"',
            'javascript' => '[code language="javascript"',
            'python' => '[code language="python"',
            'css' => '[code language="css"',
            'html' => '[code language="html"',
            'sql' => '[code language="sql"',
            'bash' => '[code language="bash"',
            'java' => '[code language="java"',
        );
        
        foreach ($lang_patterns as $lang => $pattern) {
            $count_query = $wpdb->prepare(
                "SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_status = 'publish' AND post_content LIKE %s",
                '%' . $wpdb->esc_like($pattern) . '%'
            );
            $count = $wpdb->get_var($count_query);
            if ($count > 0) {
                $languages[$lang] = intval($count);
            }
        }
        
        arsort($languages);
        $stats['languages'] = array_slice($languages, 0, 5); // Top 5 languages
        
        // Get cache size
        $cache_size = $this->get_cache_size();
        $stats['cache_size'] = $this->format_bytes($cache_size);
        
        // Get plugin usage duration
        $first_install = get_option('chc_first_install_date', current_time('timestamp'));
        $days_active = floor((current_time('timestamp') - $first_install) / DAY_IN_SECONDS);
        $stats['days_active'] = $days_active;
        
        // Get posts with code blocks
        $posts_with_code = $wpdb->get_var("
            SELECT COUNT(DISTINCT ID) 
            FROM {$wpdb->posts} 
            WHERE post_status = 'publish' 
            AND (post_content LIKE '%[code%' OR post_content LIKE '%<pre%')
        ");
        $stats['posts_with_code'] = intval($posts_with_code);
        
        wp_send_json_success($stats);
    }
    
    /**
     * AJAX handler for database optimization
     */
    public function ajax_optimize_database() {
        // Verify nonce
        if (!check_ajax_referer('chc_admin_nonce', 'nonce', false)) {
            wp_send_json_error(__('Security check failed.', 'code-highlighter-copy'), 403);
        }
        
        // Check permissions
        if (!current_user_can('manage_options')) {
            wp_send_json_error(__('Insufficient permissions.', 'code-highlighter-copy'), 403);
        }
        
        // Rate limiting - very restrictive for database operations
        $user_id = get_current_user_id();
        $transient_key = 'chc_optimize_limit_' . $user_id;
        $requests = get_transient($transient_key) ?: 0;
        
        if ($requests > 1) { // Max 1 optimization per hour
            wp_send_json_error(__('Database optimization can only be performed once per hour.', 'code-highlighter-copy'), 429);
        }
        
        set_transient($transient_key, $requests + 1, HOUR_IN_SECONDS)
        
        global $wpdb;
        
        // Clean up old transients safely with prepared statement
        $deleted_transients = $wpdb->query(
            $wpdb->prepare(
                "DELETE FROM {$wpdb->options} 
                WHERE option_name LIKE %s 
                OR option_name LIKE %s",
                '_transient_chc_%',
                '_transient_timeout_chc_%'
            )
        );
        
        // Clean up orphaned postmeta safely
        $deleted_meta = $wpdb->query(
            $wpdb->prepare(
                "DELETE pm FROM {$wpdb->postmeta} pm
                LEFT JOIN {$wpdb->posts} p ON p.ID = pm.post_id
                WHERE p.ID IS NULL
                AND pm.meta_key LIKE %s",
                '_chc_%'
            )
        );
        
        // Optimize tables
        $wpdb->query("OPTIMIZE TABLE {$wpdb->options}");
        $wpdb->query("OPTIMIZE TABLE {$wpdb->postmeta}");
        
        // Clear object cache
        wp_cache_flush();
        
        // Update optimization date
        update_option('chc_last_optimization', current_time('mysql'));
        
        // Log optimization action
        if (function_exists('wp_insert_log')) {
            wp_insert_log(array(
                'action' => 'chc_database_optimization',
                'user_id' => $user_id,
                'timestamp' => current_time('mysql'),
                'transients_deleted' => $deleted_transients,
                'meta_deleted' => $deleted_meta
            ));
        }
        
        wp_send_json_success(array(
            'message' => __('Database optimized successfully!', 'code-highlighter-copy'),
            'cleaned_transients' => $deleted_transients,
            'cleaned_meta' => $deleted_meta,
            'last_optimization' => current_time('mysql'),
        ));
    }
    
    /**
     * Get cache size
     *
     * @return int Size in bytes
     */
    private function get_cache_size() {
        global $wpdb;
        
        $cache_size = $wpdb->get_var("
            SELECT SUM(LENGTH(option_value)) 
            FROM {$wpdb->options} 
            WHERE option_name LIKE '_transient_chc_%'
        ");
        
        return intval($cache_size);
    }
    
    /**
     * Format bytes to human readable
     *
     * @param int $bytes
     * @return string
     */
    private function format_bytes($bytes) {
        $units = array('B', 'KB', 'MB', 'GB');
        $i = 0;
        
        while ($bytes >= 1024 && $i < count($units) - 1) {
            $bytes /= 1024;
            $i++;
        }
        
        return round($bytes, 2) . ' ' . $units[$i];
    }
    
    /**
     * Get allowed settings keys whitelist
     *
     * @return array
     */
    private function get_allowed_settings_keys() {
        return array(
            'chc_enable_on_frontend',
            'chc_enable_in_comments',
            'chc_auto_detect_language',
            'chc_theme',
            'chc_line_numbers',
            'chc_copy_button',
            'chc_copy_button_text',
            'chc_copied_text',
            'chc_show_language_label',
            'chc_copy_button_position',
            'chc_fullscreen_mode',
            'chc_font_size',
            'chc_font_family',
            'chc_max_height',
            'chc_header_style',
            'chc_border_radius',
            'chc_cache_enabled',
            'chc_cache_duration',
            'chc_lazy_loading',
            'chc_minify_assets',
            'chc_enable_shortcuts',
            'chc_supported_languages',
            'chc_load_assets',
            'chc_custom_css',
            'chc_default_theme'
        );
    }
    
    /**
     * Sanitize setting value based on type
     *
     * @param string $key Setting key
     * @param mixed $value Setting value
     * @return mixed Sanitized value
     */
    private function sanitize_setting_value($key, $value) {
        // Define setting types
        $boolean_settings = array(
            'chc_enable_on_frontend',
            'chc_enable_in_comments',
            'chc_auto_detect_language',
            'chc_line_numbers',
            'chc_copy_button',
            'chc_show_language_label',
            'chc_fullscreen_mode',
            'chc_cache_enabled',
            'chc_lazy_loading',
            'chc_minify_assets',
            'chc_enable_shortcuts'
        );
        
        $integer_settings = array(
            'chc_font_size',
            'chc_max_height',
            'chc_border_radius',
            'chc_cache_duration'
        );
        
        $select_settings = array(
            'chc_theme' => $this->get_available_themes(),
            'chc_copy_button_position' => array(
                'top-right' => true,
                'top-left' => true,
                'bottom-right' => true,
                'bottom-left' => true
            ),
            'chc_font_family' => array(
                'default' => true,
                'Monaco, monospace' => true,
                'Consolas, monospace' => true,
                '"Courier New", monospace' => true,
                '"Source Code Pro", monospace' => true,
                '"Fira Code", monospace' => true,
                'Menlo, monospace' => true,
                '"JetBrains Mono", monospace' => true
            ),
            'chc_header_style' => array(
                'gradient' => true,
                'solid' => true,
                'minimal' => true,
                'none' => true
            ),
            'chc_load_assets' => array(
                'auto' => true,
                'always' => true,
                'posts' => true,
                'manual' => true
            )
        );
        
        $multiselect_settings = array(
            'chc_supported_languages' => $this->get_available_languages()
        );
        
        // Sanitize based on type
        if (in_array($key, $boolean_settings, true)) {
            return (bool) $value;
        } elseif (in_array($key, $integer_settings, true)) {
            $int_value = absint($value);
            
            // Apply specific constraints
            if ($key === 'chc_font_size') {
                return max(8, min(32, $int_value)); // 8-32px
            } elseif ($key === 'chc_max_height') {
                return min(2000, $int_value); // Max 2000px
            } elseif ($key === 'chc_border_radius') {
                return min(50, $int_value); // Max 50px
            } elseif ($key === 'chc_cache_duration') {
                return max(0, min(604800, $int_value)); // Max 1 week
            }
            
            return $int_value;
        } elseif (isset($select_settings[$key])) {
            // Validate against allowed options
            if (isset($select_settings[$key][$value])) {
                return sanitize_text_field($value);
            }
            // Return default if invalid
            return array_key_first($select_settings[$key]);
        } elseif (isset($multiselect_settings[$key])) {
            if (!is_array($value)) {
                return array();
            }
            
            $sanitized = array();
            $allowed = array_keys($multiselect_settings[$key]);
            
            foreach ($value as $item) {
                if (in_array($item, $allowed, true)) {
                    $sanitized[] = sanitize_text_field($item);
                }
            }
            
            return $sanitized;
        } elseif ($key === 'chc_custom_css') {
            // Sanitize CSS - remove scripts and dangerous properties
            $value = strip_tags($value);
            $value = preg_replace('#<script[^>]*>.*?</script>#is', '', $value);
            $value = preg_replace('#javascript:#i', '', $value);
            $value = preg_replace('#expression\s*\(#i', '', $value);
            $value = preg_replace('#@import#i', '', $value);
            
            return sanitize_textarea_field($value);
        } elseif (in_array($key, array('chc_copy_button_text', 'chc_copied_text'), true)) {
            // Text fields - limit length
            $value = sanitize_text_field($value);
            return substr($value, 0, 50); // Max 50 characters
        } else {
            // Default text sanitization
            return sanitize_text_field($value);
        }
    }
}