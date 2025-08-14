<?php
/**
 * Bootstrap class for Code Highlighter Copy Plugin
 *
 * @package CodeHighlighterCopy
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Class CHC_Bootstrap
 * 
 * Handles plugin initialization and component loading
 */
class CHC_Bootstrap {
    
    /**
     * Plugin instance
     *
     * @var CHC_Bootstrap
     */
    private static $instance = null;
    
    /**
     * Plugin components
     *
     * @var array
     */
    private $components = array();
    
    /**
     * Plugin initialized flag
     *
     * @var bool
     */
    private $initialized = false;
    
    /**
     * Get singleton instance
     *
     * @return CHC_Bootstrap
     */
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }
    
    /**
     * Constructor
     */
    private function __construct() {
        // Don't do anything here - wait for init()
    }
    
    /**
     * Initialize the plugin
     *
     * @return bool True if initialization successful
     */
    public function init() {
        // Prevent double initialization
        if ($this->initialized) {
            return true;
        }
        
        try {
            // Load dependencies first
            $this->load_dependencies();
            
            // Initialize hooks
            $this->init_hooks();
            
            // Mark as initialized
            $this->initialized = true;
            
            return true;
            
        } catch (Exception $e) {
            // Log error if WP_DEBUG is enabled
            if (defined('WP_DEBUG') && WP_DEBUG) {
                error_log('Code Highlighter Copy Plugin Error: ' . $e->getMessage());
            }
            return false;
        }
    }
    
    /**
     * Load required dependencies
     */
    private function load_dependencies() {
        // Load helper functions first
        if (file_exists(CHC_PLUGIN_DIR . 'includes/functions.php')) {
            require_once CHC_PLUGIN_DIR . 'includes/functions.php';
        }
    }
    
    /**
     * Initialize WordPress hooks
     */
    private function init_hooks() {
        // Core initialization
        add_action('init', array($this, 'on_wordpress_init'), 0);
        
        // Admin initialization
        add_action('admin_init', array($this, 'on_admin_init'));
        
        // Plugin activation/deactivation
        register_activation_hook(CHC_PLUGIN_FILE, array($this, 'activate'));
        register_deactivation_hook(CHC_PLUGIN_FILE, array($this, 'deactivate'));
        
        // Plugin action links
        add_filter('plugin_action_links_' . CHC_PLUGIN_BASENAME, array($this, 'add_action_links'));
        
        // Load textdomain
        add_action('plugins_loaded', array($this, 'load_textdomain'));
    }
    
    /**
     * WordPress init hook callback
     */
    public function on_wordpress_init() {
        // Initialize components
        $this->init_components();
    }
    
    /**
     * Admin init hook callback
     */
    public function on_admin_init() {
        // Initialize admin component if needed
        if (is_admin() && !isset($this->components['admin'])) {
            $this->init_admin_component();
        }
    }
    
    /**
     * Initialize plugin components
     */
    private function init_components() {
        // Initialize Assets Manager - check if class exists
        if (CHC_Loader::class_exists('CHC_Assets')) {
            try {
                $this->components['assets'] = new CHC_Assets();
            } catch (Exception $e) {
                $this->log_error('Failed to initialize Assets component: ' . $e->getMessage());
            }
        }
        
        // Initialize Shortcodes - check if class exists
        if (CHC_Loader::class_exists('CHC_Shortcodes')) {
            try {
                $this->components['shortcodes'] = new CHC_Shortcodes();
            } catch (Exception $e) {
                $this->log_error('Failed to initialize Shortcodes component: ' . $e->getMessage());
            }
        }
    }
    
    /**
     * Initialize admin component
     */
    private function init_admin_component() {
        if (CHC_Loader::class_exists('CHC_Admin')) {
            try {
                $this->components['admin'] = new CHC_Admin();
            } catch (Exception $e) {
                $this->log_error('Failed to initialize Admin component: ' . $e->getMessage());
            }
        }
    }
    
    /**
     * Load plugin textdomain
     */
    public function load_textdomain() {
        load_plugin_textdomain(
            'code-highlighter-copy',
            false,
            dirname(CHC_PLUGIN_BASENAME) . '/languages'
        );
    }
    
    /**
     * Plugin activation
     */
    public function activate() {
        // Check requirements
        if (!$this->check_requirements()) {
            deactivate_plugins(CHC_PLUGIN_BASENAME);
            wp_die(
                __('Code Highlighter with Copy Button requires WordPress 5.8+ and PHP 7.4+', 'code-highlighter-copy'),
                __('Plugin Activation Error', 'code-highlighter-copy'),
                array('back_link' => true)
            );
        }
        
        // Set default options
        $this->set_default_options();
        
        // Create necessary database tables if needed
        $this->create_tables();
        
        // Clear rewrite rules
        flush_rewrite_rules();
    }
    
    /**
     * Plugin deactivation
     */
    public function deactivate() {
        // Clear scheduled events if any
        $this->clear_scheduled_events();
        
        // Clear transients
        $this->clear_transients();
        
        // Clear rewrite rules
        flush_rewrite_rules();
    }
    
    /**
     * Check plugin requirements
     *
     * @return bool
     */
    private function check_requirements() {
        // Check PHP version
        if (version_compare(PHP_VERSION, '7.4', '<')) {
            return false;
        }
        
        // Check WordPress version
        global $wp_version;
        if (version_compare($wp_version, '5.8', '<')) {
            return false;
        }
        
        return true;
    }
    
    /**
     * Set default plugin options
     */
    private function set_default_options() {
        $defaults = array(
            'chc_version' => CHC_VERSION,
            'chc_theme' => 'prism-tomorrow',
            'chc_line_numbers' => true,
            'chc_copy_button' => true,
            'chc_show_language_label' => true,
            'chc_enable_on_frontend' => true,
            'chc_cache_enabled' => true,
        );
        
        foreach ($defaults as $key => $value) {
            if (get_option($key) === false) {
                add_option($key, $value, '', 'yes');
            }
        }
    }
    
    /**
     * Create necessary database tables
     */
    private function create_tables() {
        // Placeholder for future database operations
    }
    
    /**
     * Clear scheduled events
     */
    private function clear_scheduled_events() {
        // Clear any scheduled cron jobs
        wp_clear_scheduled_hook('chc_daily_cleanup');
    }
    
    /**
     * Clear plugin transients
     */
    private function clear_transients() {
        global $wpdb;
        
        // Delete plugin transients
        $wpdb->query(
            "DELETE FROM {$wpdb->options} 
             WHERE option_name LIKE '_transient_chc_%' 
             OR option_name LIKE '_transient_timeout_chc_%'"
        );
    }
    
    /**
     * Add plugin action links
     *
     * @param array $links Existing links
     * @return array Modified links
     */
    public function add_action_links($links) {
        $settings_link = sprintf(
            '<a href="%s">%s</a>',
            esc_url(admin_url('options-general.php?page=code-highlighter-copy')),
            __('Settings', 'code-highlighter-copy')
        );
        
        array_unshift($links, $settings_link);
        
        return $links;
    }
    
    /**
     * Get plugin component
     *
     * @param string $component Component name
     * @return mixed|null Component instance or null
     */
    public function get_component($component) {
        return isset($this->components[$component]) ? $this->components[$component] : null;
    }
    
    /**
     * Log error message
     *
     * @param string $message Error message
     */
    private function log_error($message) {
        if (defined('WP_DEBUG') && WP_DEBUG) {
            error_log('Code Highlighter Copy: ' . $message);
        }
    }
    
    /**
     * Check if plugin is ready
     *
     * @return bool
     */
    public function is_ready() {
        return $this->initialized;
    }
}