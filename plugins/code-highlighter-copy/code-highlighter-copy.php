<?php
/**
 * Plugin Name: Code Highlighter with Copy Button
 * Plugin URI: https://ailynx.ru/plugins/code-highlighter-copy
 * Description: Professional code syntax highlighting with copy button functionality using Prism.js
 * Version: 1.0.0
 * Author: AI News Team
 * Author URI: https://ailynx.ru
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: code-highlighter-copy
 * Domain Path: /languages
 * Requires at least: 5.8
 * Requires PHP: 7.4
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Define plugin constants
define('CHC_VERSION', '1.0.0');
define('CHC_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('CHC_PLUGIN_URL', plugin_dir_url(__FILE__));
define('CHC_PLUGIN_BASENAME', plugin_basename(__FILE__));
define('CHC_PLUGIN_FILE', __FILE__);

// Load the autoloader first
require_once CHC_PLUGIN_DIR . 'includes/class-loader.php';

// Initialize the autoloader
CHC_Loader::init(CHC_PLUGIN_DIR);

/**
 * Initialize the plugin
 *
 * This function is called on 'plugins_loaded' hook to ensure
 * WordPress is fully loaded before initializing our plugin
 */
function chc_initialize_plugin() {
    // Check if Bootstrap class is available
    if (!CHC_Loader::class_exists('CHC_Bootstrap')) {
        // Log error if in debug mode
        if (defined('WP_DEBUG') && WP_DEBUG) {
            error_log('Code Highlighter Copy: Bootstrap class not found');
        }
        return;
    }
    
    // Get plugin instance and initialize
    try {
        $plugin = CHC_Bootstrap::get_instance();
        $plugin->init();
    } catch (Exception $e) {
        // Log error if in debug mode
        if (defined('WP_DEBUG') && WP_DEBUG) {
            error_log('Code Highlighter Copy: Initialization failed - ' . $e->getMessage());
        }
    }
}

// Hook into plugins_loaded to ensure WordPress is ready
add_action('plugins_loaded', 'chc_initialize_plugin', 10);

/**
 * Public API function to get plugin instance
 *
 * @return CHC_Bootstrap|null Plugin instance or null if not initialized
 */
function chc_get_plugin_instance() {
    if (CHC_Loader::class_exists('CHC_Bootstrap')) {
        $instance = CHC_Bootstrap::get_instance();
        if ($instance->is_ready()) {
            return $instance;
        }
    }
    return null;
}

/**
 * Register uninstall hook
 * This runs when the plugin is deleted
 */
register_uninstall_hook(__FILE__, 'chc_uninstall');

/**
 * Plugin uninstall handler
 */
function chc_uninstall() {
    // Only run if uninstall is called from WordPress
    if (!defined('WP_UNINSTALL_PLUGIN')) {
        return;
    }
    
    // Remove all plugin options
    global $wpdb;
    $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE 'chc_%'");
    
    // Remove all plugin transients
    $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_chc_%'");
    $wpdb->query("DELETE FROM {$wpdb->options} WHERE option_name LIKE '_transient_timeout_chc_%'");
    
    // Clear any scheduled hooks
    wp_clear_scheduled_hook('chc_daily_cleanup');
}