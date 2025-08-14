<?php
/**
 * Helper Functions
 *
 * @package CodeHighlighterCopy
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Get plugin option with fallback
 *
 * @param string $option Option name (without prefix)
 * @param mixed $default Default value
 * @return mixed Option value
 */
function chc_get_option($option, $default = null) {
    return get_option('chc_' . $option, $default);
}

/**
 * Update plugin option
 *
 * @param string $option Option name (without prefix)
 * @param mixed $value Option value
 * @return bool Success status
 */
function chc_update_option($option, $value) {
    return update_option('chc_' . $option, $value);
}

/**
 * Delete plugin option
 *
 * @param string $option Option name (without prefix)
 * @return bool Success status
 */
function chc_delete_option($option) {
    return delete_option('chc_' . $option);
}

/**
 * Check if code highlighting is enabled
 *
 * @return bool
 */
function chc_is_enabled() {
    // Check global enable status
    if (!chc_get_option('enable_on_frontend', true)) {
        return false;
    }
    
    // Check if on frontend
    if (!is_admin() && !chc_get_option('enable_on_frontend', true)) {
        return false;
    }
    
    // Allow filtering
    return apply_filters('chc_is_enabled', true);
}

/**
 * Get all plugin options
 *
 * @return array
 */
function chc_get_all_options() {
    global $wpdb;
    
    $options = array();
    $results = $wpdb->get_results(
        $wpdb->prepare(
            "SELECT option_name, option_value 
             FROM {$wpdb->options} 
             WHERE option_name LIKE %s
             LIMIT 100",
            'chc_%'
        ),
        ARRAY_A
    );
    
    foreach ($results as $row) {
        $key = str_replace('chc_', '', $row['option_name']);
        $options[$key] = maybe_unserialize($row['option_value']);
    }
    
    return $options;
}

/**
 * Reset all plugin options to defaults
 *
 * @return bool
 */
function chc_reset_options() {
    // Get all plugin options
    $options = chc_get_all_options();
    
    // Delete all options
    foreach (array_keys($options) as $option) {
        chc_delete_option($option);
    }
    
    // Recreate default options using the new API
    $plugin = chc_get_plugin_instance();
    if ($plugin && method_exists($plugin, 'activate')) {
        $plugin->activate();
    }
    
    return true;
}

/**
 * Log debug message
 *
 * @param string $message Message to log
 * @param string $level Log level (info, warning, error)
 */
function chc_log($message, $level = 'info') {
    if (!defined('WP_DEBUG') || !WP_DEBUG) {
        return;
    }
    
    $prefix = '[Code Highlighter] [' . strtoupper($level) . '] ';
    error_log($prefix . $message);
}

/**
 * Get plugin version
 *
 * @return string
 */
function chc_get_version() {
    return defined('CHC_VERSION') ? CHC_VERSION : '1.0.0';
}

/**
 * Get plugin URL
 *
 * @param string $path Optional path to append
 * @return string
 */
function chc_get_plugin_url($path = '') {
    $url = CHC_PLUGIN_URL;
    
    if (!empty($path)) {
        $url .= ltrim($path, '/');
    }
    
    return $url;
}

/**
 * Get plugin path
 *
 * @param string $path Optional path to append
 * @return string
 */
function chc_get_plugin_path($path = '') {
    $plugin_path = CHC_PLUGIN_DIR;
    
    if (!empty($path)) {
        $plugin_path .= ltrim($path, '/');
    }
    
    return $plugin_path;
}

/**
 * Check if current page is plugin settings page
 *
 * @return bool
 */
function chc_is_settings_page() {
    if (!is_admin()) {
        return false;
    }
    
    $screen = get_current_screen();
    return $screen && $screen->id === 'settings_page_code-highlighter-copy';
}

/**
 * Sanitize code content
 *
 * @param string $code Raw code
 * @param bool $preserve_entities Whether to preserve HTML entities
 * @return string Sanitized code
 */
function chc_sanitize_code($code, $preserve_entities = false) {
    // Remove slashes if they were added
    $code = wp_unslash($code);
    
    // Normalize line endings
    $code = str_replace(array("\r\n", "\r"), "\n", $code);
    
    // Trim whitespace
    $code = trim($code);
    
    // Optionally preserve entities
    if (!$preserve_entities) {
        $code = html_entity_decode($code, ENT_QUOTES | ENT_HTML5, get_bloginfo('charset'));
    }
    
    return $code;
}

/**
 * Escape code for display
 *
 * @param string $code Code to escape
 * @return string Escaped code
 */
function chc_escape_code($code) {
    return esc_html($code);
}

/**
 * Get supported file extensions for each language
 *
 * @return array
 */
function chc_get_language_extensions() {
    return array(
        'markup' => array('html', 'htm', 'xml', 'svg'),
        'css' => array('css', 'scss', 'sass', 'less'),
        'javascript' => array('js', 'mjs', 'jsx'),
        'typescript' => array('ts', 'tsx'),
        'php' => array('php', 'phtml'),
        'python' => array('py', 'pyw'),
        'ruby' => array('rb', 'erb'),
        'java' => array('java'),
        'c' => array('c', 'h'),
        'cpp' => array('cpp', 'cc', 'cxx', 'hpp', 'h++'),
        'csharp' => array('cs'),
        'go' => array('go'),
        'rust' => array('rs'),
        'sql' => array('sql'),
        'bash' => array('sh', 'bash', 'zsh'),
        'json' => array('json'),
        'yaml' => array('yaml', 'yml'),
        'markdown' => array('md', 'markdown'),
    );
}

/**
 * Detect language from file extension
 *
 * @param string $filename File name or path
 * @return string Detected language or 'plaintext'
 */
function chc_detect_language_from_file($filename) {
    $extension = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
    $extensions_map = chc_get_language_extensions();
    
    foreach ($extensions_map as $language => $extensions) {
        if (in_array($extension, $extensions, true)) {
            return $language;
        }
    }
    
    return 'plaintext';
}

/**
 * Get theme CSS URL
 *
 * @param string $theme Theme name
 * @return string Theme CSS URL
 */
function chc_get_theme_url($theme = null) {
    if (null === $theme) {
        $theme = chc_get_option('theme', 'prism-tomorrow');
    }
    
    return chc_get_plugin_url('assets/css/themes/' . $theme . '.css');
}

/**
 * Check if Gutenberg is active
 *
 * @return bool
 */
function chc_is_gutenberg_active() {
    // Include plugin.php if is_plugin_active is not available
    if (!function_exists('is_plugin_active')) {
        include_once(ABSPATH . 'wp-admin/includes/plugin.php');
    }
    
    // Check if Gutenberg plugin is active
    if (is_plugin_active('gutenberg/gutenberg.php')) {
        return true;
    }
    
    // Check WordPress version (5.0+ has Gutenberg built-in)
    if (version_compare(get_bloginfo('version'), '5.0', '>=')) {
        return true;
    }
    
    return false;
}

/**
 * Check if Classic Editor is active
 *
 * @return bool
 */
function chc_is_classic_editor_active() {
    // Include plugin.php if is_plugin_active is not available
    if (!function_exists('is_plugin_active')) {
        include_once(ABSPATH . 'wp-admin/includes/plugin.php');
    }
    
    return is_plugin_active('classic-editor/classic-editor.php');
}

/**
 * Get code block from post content
 *
 * @param int $post_id Post ID
 * @param string $language Optional language filter
 * @return array Array of code blocks
 */
function chc_get_code_blocks($post_id, $language = '') {
    $post = get_post($post_id);
    if (!$post) {
        return array();
    }
    
    $blocks = array();
    $content = $post->post_content;
    
    // Extract shortcode blocks
    $pattern = '/\[code[^\]]*\](.*?)\[\/code\]/is';
    preg_match_all($pattern, $content, $matches);
    
    foreach ($matches[0] as $index => $full_match) {
        $code = $matches[1][$index];
        
        // Parse attributes
        $atts_pattern = '/\[code\s+([^\]]*)\]/';
        preg_match($atts_pattern, $full_match, $atts_match);
        
        $attributes = array();
        if (!empty($atts_match[1])) {
            $attributes = shortcode_parse_atts($atts_match[1]);
        }
        
        $block_language = isset($attributes['language']) ? $attributes['language'] : 'plaintext';
        
        // Filter by language if specified
        if (!empty($language) && $block_language !== $language) {
            continue;
        }
        
        $blocks[] = array(
            'code' => $code,
            'language' => $block_language,
            'attributes' => $attributes,
        );
    }
    
    return $blocks;
}

/**
 * Format file size
 *
 * @param int $bytes Size in bytes
 * @param int $decimals Number of decimal places
 * @return string Formatted size
 */
function chc_format_file_size($bytes, $decimals = 2) {
    $units = array('B', 'KB', 'MB', 'GB', 'TB');
    
    $bytes = max($bytes, 0);
    $pow = floor(($bytes ? log($bytes) : 0) / log(1024));
    $pow = min($pow, count($units) - 1);
    
    $bytes /= pow(1024, $pow);
    
    return round($bytes, $decimals) . ' ' . $units[$pow];
}

/**
 * Get client IP address
 *
 * @return string
 */
function chc_get_client_ip() {
    $ip_keys = array('HTTP_CLIENT_IP', 'HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR');
    
    foreach ($ip_keys as $key) {
        if (array_key_exists($key, $_SERVER) === true) {
            $ip_list = explode(',', $_SERVER[$key]);
            foreach ($ip_list as $ip) {
                $ip = trim($ip);
                
                if (filter_var(
                    $ip,
                    FILTER_VALIDATE_IP,
                    FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE
                ) !== false) {
                    return $ip;
                }
            }
        }
    }
    
    return '127.0.0.1';
}

/**
 * Check if request is AJAX
 *
 * @return bool
 */
function chc_is_ajax_request() {
    return defined('DOING_AJAX') && DOING_AJAX;
}

/**
 * Check if request is REST API
 *
 * @return bool
 */
function chc_is_rest_request() {
    return defined('REST_REQUEST') && REST_REQUEST;
}

/**
 * Generate unique element ID
 *
 * @param string $prefix Optional prefix
 * @return string
 */
function chc_generate_id($prefix = 'chc') {
    return $prefix . '-' . wp_generate_password(8, false);
}

/**
 * Minify CSS
 *
 * @param string $css CSS to minify
 * @return string Minified CSS
 */
function chc_minify_css($css) {
    // Remove comments
    $css = preg_replace('!/\*[^*]*\*+([^/][^*]*\*+)*/!', '', $css);
    
    // Remove unnecessary whitespace
    $css = str_replace(array("\r\n", "\r", "\n", "\t", '  ', '    ', '    '), '', $css);
    
    // Remove unnecessary semicolons
    $css = str_replace(';}', '}', $css);
    
    return $css;
}

/**
 * Minify JavaScript
 *
 * @param string $js JavaScript to minify
 * @return string Minified JavaScript
 */
function chc_minify_js($js) {
    // This is a simple minification. For production, use a proper minifier.
    
    // Remove comments
    $js = preg_replace('/(?:(?:\/\*(?:[^*]|(?:\*+[^*\/]))*\*+\/)|(?:\/\/.*))/', '', $js);
    
    // Remove unnecessary whitespace
    $js = preg_replace('/\s+/', ' ', $js);
    
    return trim($js);
}