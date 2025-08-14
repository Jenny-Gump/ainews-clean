<?php
/**
 * Assets Management Class
 *
 * @package CodeHighlighterCopy
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Class CHC_Assets
 * 
 * Handles loading and management of CSS and JavaScript assets
 */
class CHC_Assets {
    
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
        // Frontend assets
        if (get_option('chc_enable_on_frontend', true)) {
            add_action('wp_enqueue_scripts', array($this, 'enqueue_frontend_assets'));
        }
        
        // Admin assets
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_assets'));
        
        // Editor assets (Gutenberg)
        add_action('enqueue_block_editor_assets', array($this, 'enqueue_block_editor_assets'));
        
        // Add async/defer attributes
        add_filter('script_loader_tag', array($this, 'add_script_attributes'), 10, 3);
        
        // Add theme classes to body
        add_filter('body_class', array($this, 'add_theme_body_classes'));
    }
    
    /**
     * Enqueue frontend assets
     */
    public function enqueue_frontend_assets() {
        // Check if we should load assets on this page
        if (!$this->should_load_assets()) {
            return;
        }
        
        $theme = get_option('chc_theme', 'prism-tomorrow');
        
        // Enqueue base Prism CSS
        wp_enqueue_style(
            'prism-base',
            CHC_PLUGIN_URL . 'assets/css/prism.css',
            array(),
            '1.29.0',
            'all'
        );
        
        // Enqueue selected theme CSS
        $theme_file = $this->get_theme_file($theme);
        if ($theme_file) {
            wp_enqueue_style(
                'prism-theme',
                CHC_PLUGIN_URL . 'assets/css/' . $theme_file,
                array('prism-base'),
                '1.29.0',
                'all'
            );
        }
        
        // Enqueue plugin CSS for line numbers and toolbar
        if (get_option('chc_line_numbers', true)) {
            wp_enqueue_style(
                'prism-line-numbers',
                CHC_PLUGIN_URL . 'assets/css/prism-line-numbers.css',
                array('prism-base'),
                '1.29.0',
                'all'
            );
        }
        
        if (get_option('chc_copy_button', true)) {
            wp_enqueue_style(
                'prism-toolbar',
                CHC_PLUGIN_URL . 'assets/css/prism-toolbar.css',
                array('prism-base'),
                '1.29.0',
                'all'
            );
        }
        
        // Enqueue custom plugin CSS
        wp_enqueue_style(
            'chc-styles',
            CHC_PLUGIN_URL . 'assets/css/code-highlighter.css',
            array('prism-base'),
            CHC_VERSION,
            'all'
        );
        
        // Enqueue CSS Variables for customization
        wp_enqueue_style(
            'chc-custom-variables',
            CHC_PLUGIN_URL . 'assets/css/themes/custom-variables.css',
            array('chc-styles'),
            CHC_VERSION,
            'all'
        );
        
        // Enqueue WordPress themes compatibility styles
        wp_enqueue_style(
            'chc-themes-compat',
            CHC_PLUGIN_URL . 'assets/css/themes/wordpress-themes-compat.css',
            array('chc-styles'),
            CHC_VERSION,
            'all'
        );
        
        // Add inline CSS for theme detection
        $inline_css = $this->get_inline_css($theme);
        if ($inline_css) {
            wp_add_inline_style('chc-styles', $inline_css);
        }
        
        // Add theme class to body for better targeting
        $this->add_theme_body_class();
        
        // Enqueue Prism core JS
        wp_enqueue_script(
            'prism-core',
            CHC_PLUGIN_URL . 'assets/js/prism.js',
            array(),
            '1.29.0',
            true
        );
        
        // Enqueue language components
        $this->enqueue_language_components();
        
        // Enqueue plugins
        $this->enqueue_prism_plugins();
        
        // Enqueue Clipboard.js if copy button is enabled
        if (get_option('chc_copy_button', true)) {
            wp_enqueue_script(
                'clipboard-js',
                CHC_PLUGIN_URL . 'assets/js/clipboard.min.js',
                array(),
                '2.0.11',
                true
            );
        }
        
        // Build dependencies array
        $dependencies = array('prism-core');
        if (get_option('chc_copy_button', true)) {
            $dependencies[] = 'clipboard-js';
        }
        
        // Enqueue custom plugin JS
        wp_enqueue_script(
            'chc-scripts',
            CHC_PLUGIN_URL . 'assets/js/code-highlighter.js',
            $dependencies,
            CHC_VERSION,
            true
        );
        
        // Localize script
        wp_localize_script('chc-scripts', 'chc_params', $this->get_script_params());
    }
    
    /**
     * Enqueue admin assets
     *
     * @param string $hook Current admin page hook
     */
    public function enqueue_admin_assets($hook) {
        // Only load on plugin settings page
        if ('settings_page_code-highlighter-copy' !== $hook) {
            return;
        }
        
        // Admin styles
        wp_enqueue_style(
            'chc-admin-styles',
            CHC_PLUGIN_URL . 'assets/css/admin.css',
            array(),
            CHC_VERSION,
            'all'
        );
        
        // Color picker
        wp_enqueue_style('wp-color-picker');
        
        // Admin scripts
        wp_enqueue_script(
            'chc-admin-scripts',
            CHC_PLUGIN_URL . 'assets/js/admin.js',
            array('jquery', 'wp-color-picker'),
            CHC_VERSION,
            true
        );
        
        // Localize admin script
        wp_localize_script('chc-admin-scripts', 'chc_admin', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('chc_admin_nonce'),
            'strings' => array(
                'confirm_reset' => __('Are you sure you want to reset all settings to defaults?', 'code-highlighter-copy'),
                'save_success' => __('Settings saved successfully!', 'code-highlighter-copy'),
                'save_error' => __('Error saving settings. Please try again.', 'code-highlighter-copy'),
            ),
        ));
    }
    
    /**
     * Enqueue block editor assets
     */
    public function enqueue_block_editor_assets() {
        // Block editor styles
        wp_enqueue_style(
            'chc-block-editor',
            CHC_PLUGIN_URL . 'assets/css/block-editor.css',
            array('wp-edit-blocks'),
            CHC_VERSION
        );
        
        // Block editor scripts
        wp_enqueue_script(
            'chc-block-editor',
            CHC_PLUGIN_URL . 'assets/js/block-editor.js',
            array('wp-blocks', 'wp-element', 'wp-editor', 'wp-components', 'wp-i18n'),
            CHC_VERSION,
            true
        );
        
        // Register block
        wp_localize_script('chc-block-editor', 'chc_block_params', array(
            'languages' => $this->get_supported_languages(),
            'themes' => $this->get_available_themes(),
            'default_language' => 'javascript',
        ));
    }
    
    /**
     * Enqueue Prism language components
     */
    private function enqueue_language_components() {
        // Detect languages actually used on the current page
        $detected_languages = $this->detect_used_languages();
        
        // If no languages detected, use minimal set or settings
        if (empty($detected_languages)) {
            // In admin, load defaults from settings
            if (is_admin()) {
                $languages = get_option('chc_supported_languages', array('javascript', 'css', 'html', 'php'));
            } else {
                // On frontend with no detected languages, load minimal set
                $languages = array('javascript', 'css', 'html');
            }
        } else {
            $languages = $detected_languages;
        }
        
        // Core dependencies that should always be loaded
        $core_dependencies = array('clike');
        
        // Language dependencies mapping
        $dependencies = array(
            'javascript' => array('clike'),
            'typescript' => array('javascript'),
            'java' => array('clike'),
            'php' => array('clike', 'markup'),
            'c' => array('clike'),
            'cpp' => array('c'),
            'csharp' => array('clike'),
            'objectivec' => array('c'),
            'swift' => array('clike'),
            'kotlin' => array('clike'),
            'scala' => array('java'),
            'groovy' => array('clike'),
            'go' => array('clike'),
            'rust' => array('clike'),
            'powershell' => array('clike'),
        );
        
        // Load core dependencies first
        foreach ($core_dependencies as $dep) {
            $this->load_language_component($dep);
        }
        
        // Load selected languages with their dependencies
        foreach ($languages as $language) {
            // Load dependencies first
            if (isset($dependencies[$language])) {
                foreach ($dependencies[$language] as $dep) {
                    $this->load_language_component($dep);
                }
            }
            
            // Load the language itself
            $this->load_language_component($language);
        }
    }
    
    /**
     * Load a single language component
     */
    private function load_language_component($language) {
        static $loaded = array();
        
        // Skip if already loaded
        if (isset($loaded[$language])) {
            return;
        }
        
        $handle = 'prism-lang-' . $language;
        $file = 'assets/js/components/prism-' . $language . '.min.js';
        
        if (file_exists(CHC_PLUGIN_DIR . $file)) {
            wp_enqueue_script(
                $handle,
                CHC_PLUGIN_URL . $file,
                array('prism-core'),
                '1.29.0',
                true
            );
            
            $loaded[$language] = true;
        }
    }
    
    /**
     * Detect languages used on the current page
     */
    private function detect_used_languages() {
        global $post;
        $detected_languages = array();
        
        if (!$post || empty($post->post_content)) {
            return $detected_languages;
        }
        
        $content = $post->post_content;
        
        // Method 1: Find language-xxx classes in pre tags
        if (preg_match_all('/\blanguage-(\w+)\b/', $content, $matches)) {
            $detected_languages = array_merge($detected_languages, $matches[1]);
        }
        
        // Method 2: Check for language shortcodes
        $language_shortcodes = array(
            'php' => 'php',
            'python' => 'python',
            'javascript' => 'javascript',
            'js' => 'javascript',
            'html' => 'markup',
            'css' => 'css',
            'sql' => 'sql',
            'bash' => 'bash',
            'shell' => 'bash',
            'java' => 'java',
            'cpp' => 'cpp',
            'c' => 'c',
            'csharp' => 'csharp',
            'ruby' => 'ruby',
            'rb' => 'ruby',
            'go' => 'go',
            'golang' => 'go',
            'rust' => 'rust',
            'swift' => 'swift',
            'kotlin' => 'kotlin',
            'typescript' => 'typescript',
            'ts' => 'typescript',
            'json' => 'json',
            'xml' => 'markup',
            'yaml' => 'yaml',
            'yml' => 'yaml',
            'markdown' => 'markdown',
            'md' => 'markdown',
            'perl' => 'perl',
            'pl' => 'perl',
            'r' => 'r',
            'powershell' => 'powershell',
            'ps' => 'powershell',
            'objectivec' => 'objectivec',
            'objc' => 'objectivec',
            'haskell' => 'haskell',
            'scala' => 'scala'
        );
        
        foreach ($language_shortcodes as $shortcode => $language) {
            if (has_shortcode($content, $shortcode)) {
                $detected_languages[] = $language;
            }
        }
        
        // Always include markup for HTML-based languages
        if (array_intersect($detected_languages, array('php', 'html', 'xml'))) {
            $detected_languages[] = 'markup';
        }
        
        // Remove duplicates and return
        return array_unique($detected_languages);
    }
    
    /**
     * Get default languages
     */
    private function get_default_languages() {
        return array(
            'markup', 'css', 'javascript', 'bash', 'c', 'cpp', 
            'csharp', 'java', 'python', 'php', 'sql', 'ruby', 
            'go', 'rust', 'swift', 'kotlin', 'yaml', 'json', 
            'typescript', 'markdown', 'perl', 'r', 'powershell',
            'objectivec', 'haskell', 'scala'
        );
    }
    
    /**
     * Enqueue Prism plugins
     */
    private function enqueue_prism_plugins() {
        $plugins = array();
        
        // Line numbers plugin
        if (get_option('chc_line_numbers', true)) {
            $plugins[] = 'line-numbers';
        }
        
        // Toolbar plugin (required for copy button and show language)
        if (get_option('chc_copy_button', true) || get_option('chc_show_language_label', true)) {
            $plugins[] = 'toolbar';
        }
        
        // Copy to clipboard plugin
        if (get_option('chc_copy_button', true)) {
            $plugins[] = 'copy-to-clipboard';
        }
        
        // Show language plugin
        if (get_option('chc_show_language_label', true)) {
            $plugins[] = 'show-language';
        }
        
        // Additional plugins that are always loaded
        $additional = array('normalize-whitespace', 'autolinker');
        $plugins = array_merge($plugins, $additional);
        
        // Remove duplicates
        $plugins = array_unique($plugins);
        
        // Plugin dependencies
        $plugin_deps = array(
            'copy-to-clipboard' => array('toolbar'),
            'show-language' => array('toolbar'),
        );
        
        // Load plugins in correct order
        foreach ($plugins as $plugin) {
            // Load dependencies first
            if (isset($plugin_deps[$plugin])) {
                foreach ($plugin_deps[$plugin] as $dep) {
                    $this->load_prism_plugin($dep);
                }
            }
            
            // Load the plugin
            $this->load_prism_plugin($plugin);
        }
    }
    
    /**
     * Load a single Prism plugin
     */
    private function load_prism_plugin($plugin) {
        static $loaded = array();
        
        // Skip if already loaded
        if (isset($loaded[$plugin])) {
            return;
        }
        
        $handle = 'prism-plugin-' . $plugin;
        $file = 'assets/js/plugins/prism-' . $plugin . '.min.js';
        
        if (file_exists(CHC_PLUGIN_DIR . $file)) {
            wp_enqueue_script(
                $handle,
                CHC_PLUGIN_URL . $file,
                array('prism-core'),
                '1.29.0',
                true
            );
            
            $loaded[$plugin] = true;
        }
    }
    
    /**
     * Get script parameters for localization
     *
     * @return array
     */
    private function get_script_params() {
        return array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('chc_nonce'),
            'copy_text' => get_option('chc_copy_button_text', __('Copy', 'code-highlighter-copy')),
            'copied_text' => get_option('chc_copied_text', __('Copied!', 'code-highlighter-copy')),
            'copy_error' => __('Failed to copy', 'code-highlighter-copy'),
            'auto_detect' => get_option('chc_auto_detect_language', false),
            'line_numbers' => get_option('chc_line_numbers', true),
        );
    }
    
    /**
     * Check if assets should be loaded on current page
     *
     * @return bool
     */
    private function should_load_assets() {
        // Always load in admin
        if (is_admin()) {
            return true;
        }
        
        // Check if disabled on frontend
        if (!get_option('chc_enable_on_frontend', true)) {
            return false;
        }
        
        // Check for shortcode presence
        global $post;
        if ($post && has_shortcode($post->post_content, 'code')) {
            return true;
        }
        
        // Check for language-specific shortcodes
        if ($post && !empty($post->post_content)) {
            $language_shortcodes = array(
                'php', 'python', 'javascript', 'js', 'html', 'css', 'sql', 
                'bash', 'shell', 'java', 'cpp', 'c', 'csharp', 'ruby', 'go', 
                'rust', 'swift', 'kotlin', 'typescript', 'json', 'xml', 'yaml'
            );
            
            foreach ($language_shortcodes as $lang) {
                if (has_shortcode($post->post_content, $lang)) {
                    return true;
                }
            }
        }
        
        // Check for Gutenberg block
        if ($post && function_exists('has_block') && has_block('chc/code-block', $post)) {
            return true;
        }
        
        // Allow filtering
        return apply_filters('chc_should_load_assets', false);
    }
    
    /**
     * Add async/defer attributes to scripts
     *
     * @param string $tag Script tag
     * @param string $handle Script handle
     * @param string $src Script source
     * @return string Modified script tag
     */
    public function add_script_attributes($tag, $handle, $src) {
        // Add defer to all plugin scripts for better performance
        $defer_handles = array(
            'prism-', // Prism core and components
            'chc-', // Plugin scripts
            'clipboard-js', // Clipboard library
            'code-highlighter-main', // Main script
            'code-highlighter-admin' // Admin script
        );
        
        foreach ($defer_handles as $prefix) {
            if (strpos($handle, $prefix) === 0 || $handle === $prefix) {
                // Check if defer already added
                if (strpos($tag, ' defer') === false) {
                    return str_replace(' src', ' defer src', $tag);
                }
                break;
            }
        }
        
        return $tag;
    }
    
    /**
     * Get supported languages
     *
     * @return array
     */
    private function get_supported_languages() {
        return array(
            'markup' => __('HTML/XML', 'code-highlighter-copy'),
            'css' => __('CSS', 'code-highlighter-copy'),
            'clike' => __('C-like', 'code-highlighter-copy'),
            'javascript' => __('JavaScript', 'code-highlighter-copy'),
            'bash' => __('Bash/Shell', 'code-highlighter-copy'),
            'c' => __('C', 'code-highlighter-copy'),
            'cpp' => __('C++', 'code-highlighter-copy'),
            'csharp' => __('C#', 'code-highlighter-copy'),
            'java' => __('Java', 'code-highlighter-copy'),
            'python' => __('Python', 'code-highlighter-copy'),
            'php' => __('PHP', 'code-highlighter-copy'),
            'sql' => __('SQL', 'code-highlighter-copy'),
            'ruby' => __('Ruby', 'code-highlighter-copy'),
            'go' => __('Go', 'code-highlighter-copy'),
            'rust' => __('Rust', 'code-highlighter-copy'),
            'swift' => __('Swift', 'code-highlighter-copy'),
            'kotlin' => __('Kotlin', 'code-highlighter-copy'),
            'yaml' => __('YAML', 'code-highlighter-copy'),
            'json' => __('JSON', 'code-highlighter-copy'),
            'typescript' => __('TypeScript', 'code-highlighter-copy'),
            'markdown' => __('Markdown', 'code-highlighter-copy'),
            'perl' => __('Perl', 'code-highlighter-copy'),
            'r' => __('R', 'code-highlighter-copy'),
            'powershell' => __('PowerShell', 'code-highlighter-copy'),
            'objectivec' => __('Objective-C', 'code-highlighter-copy'),
            'haskell' => __('Haskell', 'code-highlighter-copy'),
            'scala' => __('Scala', 'code-highlighter-copy'),
            'clojure' => __('Clojure', 'code-highlighter-copy'),
            'erlang' => __('Erlang', 'code-highlighter-copy'),
            'fsharp' => __('F#', 'code-highlighter-copy'),
            'groovy' => __('Groovy', 'code-highlighter-copy'),
            'latex' => __('LaTeX', 'code-highlighter-copy'),
            'matlab' => __('MATLAB', 'code-highlighter-copy'),
            'pascal' => __('Pascal', 'code-highlighter-copy'),
            'diff' => __('Diff', 'code-highlighter-copy'),
            'arduino' => __('Arduino', 'code-highlighter-copy'),
            'actionscript' => __('ActionScript', 'code-highlighter-copy'),
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
     * Get theme file name
     *
     * @param string $theme Theme identifier
     * @return string|false Theme file name or false if not found
     */
    private function get_theme_file($theme) {
        $theme_files = array(
            'prism' => 'prism.css',
            'prism-tomorrow' => 'prism-tomorrow.css',
            'prism-okaidia' => 'prism-okaidia.css',
            'prism-twilight' => 'themes/prism-twilight.css',
            'prism-coy' => 'themes/prism-coy.css',
            'prism-solarized' => 'themes/prism-solarized.css',
            'prism-dark' => 'themes/prism-dark.css',
            'prism-funky' => 'themes/prism-funky.css',
        );
        
        return isset($theme_files[$theme]) ? $theme_files[$theme] : false;
    }
    
    /**
     * Get inline CSS for theme customization
     *
     * @param string $theme Theme identifier
     * @return string Inline CSS
     */
    private function get_inline_css($theme) {
        $css = '';
        
        // Add light theme class if applicable
        $light_themes = array('prism', 'prism-coy', 'prism-solarized', 'prism-funky');
        if (in_array($theme, $light_themes)) {
            $css .= '.chcb-code-block { --chcb-theme: light; }' . "\n";
            $css .= '.chcb-code-block.light-theme { display: block; }' . "\n";
        }
        
        // Add custom colors if set
        $custom_bg = get_option('chc_custom_bg_color');
        $custom_text = get_option('chc_custom_text_color');
        
        if ($custom_bg || $custom_text) {
            $css .= '.chcb-code-block pre[class*="language-"] {';
            if ($custom_bg) {
                $css .= ' background: ' . esc_attr($custom_bg) . ' !important;';
            }
            if ($custom_text) {
                $css .= ' color: ' . esc_attr($custom_text) . ' !important;';
            }
            $css .= ' }' . "\n";
        }
        
        // Add custom font size if set
        $font_size = get_option('chc_font_size');
        if ($font_size && $font_size !== '14') {
            $css .= '.chcb-code-block code { font-size: ' . intval($font_size) . 'px !important; }' . "\n";
        }
        
        // Add custom line height if set
        $line_height = get_option('chc_line_height');
        if ($line_height && $line_height !== '1.6') {
            $css .= '.chcb-code-block code { line-height: ' . floatval($line_height) . ' !important; }' . "\n";
        }
        
        return $css;
    }
    
    /**
     * Add theme detection method (called in enqueue)
     */
    private function add_theme_body_class() {
        // This is just a placeholder since we're using the filter
        // The actual work is done in add_theme_body_classes method
    }
    
    /**
     * Add theme-specific classes to body
     *
     * @param array $classes Existing body classes
     * @return array Modified body classes
     */
    public function add_theme_body_classes($classes) {
        // Get current theme
        $theme = wp_get_theme();
        $theme_slug = $theme->get_stylesheet();
        $parent_theme = $theme->parent() ? $theme->parent()->get_stylesheet() : '';
        
        // Add theme classes
        $classes[] = 'chcb-theme-' . sanitize_html_class($theme_slug);
        
        if ($parent_theme) {
            $classes[] = 'chcb-parent-theme-' . sanitize_html_class($parent_theme);
        }
        
        // Add color scheme class
        $color_scheme = get_option('chc_color_scheme', 'auto');
        if ($color_scheme === 'auto') {
            // Try to detect if the site is using dark mode
            $classes[] = $this->detect_dark_mode() ? 'chcb-theme-dark' : 'chcb-theme-light';
        } else {
            $classes[] = 'chcb-theme-' . $color_scheme;
        }
        
        // Add specific theme detection
        if (strpos($theme_slug, 'twentytwenty') !== false) {
            $classes[] = 'chcb-twentytwenty-theme';
        } elseif (strpos($theme_slug, 'astra') !== false) {
            $classes[] = 'chcb-astra-theme';
        } elseif (strpos($theme_slug, 'generatepress') !== false) {
            $classes[] = 'chcb-generatepress-theme';
        } elseif (strpos($theme_slug, 'oceanwp') !== false) {
            $classes[] = 'chcb-oceanwp-theme';
        } elseif (strpos($theme_slug, 'neve') !== false) {
            $classes[] = 'chcb-neve-theme';
        } elseif (strpos($theme_slug, 'blocksy') !== false) {
            $classes[] = 'chcb-blocksy-theme';
        } elseif (strpos($theme_slug, 'kadence') !== false) {
            $classes[] = 'chcb-kadence-theme';
        }
        
        return $classes;
    }
    
    /**
     * Detect if the site is using dark mode
     *
     * @return bool
     */
    private function detect_dark_mode() {
        // Check for common dark mode indicators
        $body_classes = get_body_class();
        
        $dark_indicators = array(
            'dark-mode',
            'dark-theme',
            'is-dark-theme',
            'night-mode',
            'theme-dark',
            'dark-style'
        );
        
        foreach ($dark_indicators as $indicator) {
            if (in_array($indicator, $body_classes)) {
                return true;
            }
        }
        
        // Check theme mods
        $color_scheme = get_theme_mod('color_scheme', '');
        if (strpos(strtolower($color_scheme), 'dark') !== false) {
            return true;
        }
        
        // Check customizer settings
        $background_color = get_theme_mod('background_color', '');
        if ($background_color) {
            // Convert hex to RGB and check brightness
            $rgb = $this->hex_to_rgb($background_color);
            if ($rgb) {
                $brightness = ($rgb['r'] * 299 + $rgb['g'] * 587 + $rgb['b'] * 114) / 1000;
                return $brightness < 128;
            }
        }
        
        return false;
    }
    
    /**
     * Convert hex color to RGB
     *
     * @param string $hex Hex color code
     * @return array|false RGB values or false on failure
     */
    private function hex_to_rgb($hex) {
        $hex = str_replace('#', '', $hex);
        
        if (strlen($hex) === 3) {
            $hex = str_repeat(substr($hex, 0, 1), 2) . 
                   str_repeat(substr($hex, 1, 1), 2) . 
                   str_repeat(substr($hex, 2, 1), 2);
        }
        
        if (strlen($hex) !== 6) {
            return false;
        }
        
        return array(
            'r' => hexdec(substr($hex, 0, 2)),
            'g' => hexdec(substr($hex, 2, 2)),
            'b' => hexdec(substr($hex, 4, 2))
        );
    }
}