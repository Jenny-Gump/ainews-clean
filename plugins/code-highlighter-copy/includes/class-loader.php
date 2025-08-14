<?php
/**
 * Autoloader for Code Highlighter Copy Plugin
 *
 * @package CodeHighlighterCopy
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Class CHC_Loader
 * 
 * Handles autoloading of plugin classes
 */
class CHC_Loader {
    
    /**
     * Registered classes mapping
     *
     * @var array
     */
    private static $classes = array();
    
    /**
     * Plugin directory path
     *
     * @var string
     */
    private static $plugin_dir = '';
    
    /**
     * Initialize the autoloader
     *
     * @param string $plugin_dir Plugin directory path
     */
    public static function init($plugin_dir) {
        self::$plugin_dir = trailingslashit($plugin_dir);
        
        // Register class mappings
        self::register_classes();
        
        // Register autoloader
        spl_autoload_register(array(__CLASS__, 'autoload'));
    }
    
    /**
     * Register class mappings
     */
    private static function register_classes() {
        self::$classes = array(
            // Core classes
            'CHC_Bootstrap'  => 'includes/class-bootstrap.php',
            'CHC_Assets'     => 'includes/class-assets.php',
            'CHC_Shortcodes' => 'includes/class-shortcodes.php',
            
            // Admin classes
            'CHC_Admin'        => 'admin/class-admin.php',
            'CHC_Admin_Secure' => 'admin/class-admin-secure.php',
        );
    }
    
    /**
     * Autoload handler
     *
     * @param string $class_name Class name to load
     */
    public static function autoload($class_name) {
        // Check if it's our class
        if (isset(self::$classes[$class_name])) {
            $file_path = self::$plugin_dir . self::$classes[$class_name];
            
            if (file_exists($file_path)) {
                require_once $file_path;
            }
        }
    }
    
    /**
     * Load a specific file
     *
     * @param string $file Relative path to file
     * @return bool True if loaded, false otherwise
     */
    public static function load_file($file) {
        $file_path = self::$plugin_dir . $file;
        
        if (file_exists($file_path)) {
            require_once $file_path;
            return true;
        }
        
        return false;
    }
    
    /**
     * Check if a class is available
     *
     * @param string $class_name Class name to check
     * @return bool
     */
    public static function class_exists($class_name) {
        // Try to load it first if registered
        if (isset(self::$classes[$class_name]) && !class_exists($class_name, false)) {
            self::autoload($class_name);
        }
        
        return class_exists($class_name, false);
    }
}