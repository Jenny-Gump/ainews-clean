<?php
/**
 * Shortcodes Management Class
 *
 * @package CodeHighlighterCopy
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Class CHC_Shortcodes
 * 
 * Handles registration and rendering of shortcodes
 */
class CHC_Shortcodes {
    
    /**
     * Cache for processed code blocks
     *
     * @var array
     */
    private $cache = array();
    
    /**
     * Language mappings (aliases to main language names)
     *
     * @var array
     */
    private $language_aliases = array(
        // PHP
        'php' => 'php',
        
        // Python
        'python' => 'python',
        'py' => 'python',
        
        // JavaScript
        'javascript' => 'javascript',
        'js' => 'javascript',
        
        // HTML/Markup
        'html' => 'html',
        'xhtml' => 'html',
        
        // CSS
        'css' => 'css',
        
        // SQL
        'sql' => 'sql',
        
        // Shell/Bash
        'bash' => 'bash',
        'shell' => 'bash',
        'sh' => 'bash',
        
        // C/C++
        'cpp' => 'cpp',
        'c++' => 'cpp',
        'c' => 'c',
        
        // C#
        'csharp' => 'csharp',
        'c-sharp' => 'csharp',
        'cs' => 'csharp',
        
        // Java
        'java' => 'java',
        
        // Go
        'go' => 'go',
        'golang' => 'go',
        
        // Ruby
        'ruby' => 'ruby',
        'rb' => 'ruby',
        
        // Swift
        'swift' => 'swift',
        
        // Kotlin
        'kotlin' => 'kotlin',
        
        // Rust
        'rust' => 'rust',
        
        // ActionScript
        'as3' => 'actionscript',
        'actionscript3' => 'actionscript',
        'actionscript' => 'actionscript',
        
        // Arduino
        'arduino' => 'arduino',
        
        // ColdFusion
        'coldfusion' => 'coldfusion',
        'cf' => 'coldfusion',
        
        // Clojure
        'clojure' => 'clojure',
        'clj' => 'clojure',
        
        // Delphi/Pascal
        'delphi' => 'delphi',
        'pas' => 'delphi',
        'pascal' => 'delphi',
        
        // Diff
        'diff' => 'diff',
        'patch' => 'diff',
        
        // Erlang
        'erl' => 'erlang',
        'erlang' => 'erlang',
        
        // F#
        'fsharp' => 'fsharp',
        'f#' => 'fsharp',
        
        // Groovy
        'groovy' => 'groovy',
        
        // Haskell
        'haskell' => 'haskell',
        
        // JavaFX
        'javafx' => 'javafx',
        'jfx' => 'javafx',
        
        // LaTeX
        'latex' => 'latex',
        'tex' => 'latex',
        
        // MATLAB
        'matlab' => 'matlab',
        'matlabkey' => 'matlab',
        
        // Objective-C
        'objc' => 'objectivec',
        'obj-c' => 'objectivec',
        'objectivec' => 'objectivec',
        
        // Perl
        'perl' => 'perl',
        'pl' => 'perl',
        
        // Plain Text
        'plain' => 'plaintext',
        'text' => 'plaintext',
        'plaintext' => 'plaintext',
        
        // PowerShell
        'ps' => 'powershell',
        'powershell' => 'powershell',
        
        // R
        'r' => 'r',
        'splus' => 'r',
        
        // Ruby on Rails
        'rails' => 'ruby',
        'ror' => 'ruby',
        
        // Scala
        'scala' => 'scala',
        
        // Visual Basic
        'vb' => 'vb',
        'vbnet' => 'vb',
        
        // XML
        'xml' => 'xml',
        'xslt' => 'xml',
        
        // YAML
        'yaml' => 'yaml',
        'yml' => 'yaml',
        
        // JSON
        'json' => 'json',
        
        // TypeScript
        'typescript' => 'typescript',
        'ts' => 'typescript',
        
        // Markdown
        'markdown' => 'markdown',
        'md' => 'markdown',
    );
    
    /**
     * Display names for languages
     *
     * @var array
     */
    private $language_display_names = array(
        'php' => 'PHP',
        'python' => 'Python',
        'javascript' => 'JavaScript',
        'html' => 'HTML',
        'css' => 'CSS',
        'sql' => 'SQL',
        'bash' => 'Bash/Shell',
        'cpp' => 'C++',
        'c' => 'C',
        'csharp' => 'C#',
        'java' => 'Java',
        'go' => 'Go',
        'ruby' => 'Ruby',
        'swift' => 'Swift',
        'kotlin' => 'Kotlin',
        'rust' => 'Rust',
        'actionscript' => 'ActionScript',
        'arduino' => 'Arduino',
        'coldfusion' => 'ColdFusion',
        'clojure' => 'Clojure',
        'delphi' => 'Delphi/Pascal',
        'diff' => 'Diff',
        'erlang' => 'Erlang',
        'fsharp' => 'F#',
        'groovy' => 'Groovy',
        'haskell' => 'Haskell',
        'javafx' => 'JavaFX',
        'latex' => 'LaTeX',
        'matlab' => 'MATLAB',
        'objectivec' => 'Objective-C',
        'perl' => 'Perl',
        'plaintext' => 'Plain Text',
        'powershell' => 'PowerShell',
        'r' => 'R',
        'scala' => 'Scala',
        'vb' => 'Visual Basic',
        'xml' => 'XML',
        'yaml' => 'YAML',
        'json' => 'JSON',
        'typescript' => 'TypeScript',
        'markdown' => 'Markdown',
    );
    
    /**
     * Constructor
     */
    public function __construct() {
        $this->register_shortcodes();
        $this->init_hooks();
    }
    
    /**
     * Register shortcodes
     */
    private function register_shortcodes() {
        // Main code shortcode
        add_shortcode('code', array($this, 'render_code_shortcode'));
        
        // Inline code shortcode
        add_shortcode('inline_code', array($this, 'render_inline_code_shortcode'));
        
        // Code block with file info
        add_shortcode('code_file', array($this, 'render_code_file_shortcode'));
        
        // Legacy support for common shortcodes
        add_shortcode('highlight', array($this, 'render_code_shortcode'));
        add_shortcode('sourcecode', array($this, 'render_code_shortcode'));
        
        // Register individual language shortcodes
        foreach ($this->language_aliases as $alias => $language) {
            add_shortcode($alias, array($this, 'render_language_shortcode'));
        }
    }
    
    /**
     * Initialize hooks
     */
    private function init_hooks() {
        // Process content for auto-highlighting
        if (get_option('chc_auto_detect_language', false)) {
            add_filter('the_content', array($this, 'auto_highlight_code'), 99);
        }
        
        // Add support for comments if enabled
        if (get_option('chc_enable_in_comments', false)) {
            add_filter('comment_text', array($this, 'process_comment_code'), 99);
        }
        
        // Clear cache on post save
        add_action('save_post', array($this, 'clear_cache'));
    }
    
    /**
     * Render main code shortcode
     *
     * @param array $atts Shortcode attributes
     * @param string $content Shortcode content
     * @return string Rendered HTML
     */
    public function render_code_shortcode($atts, $content = null) {
        // Return empty if no content
        if (empty($content)) {
            return '';
        }
        
        // Parse attributes
        $atts = shortcode_atts(array(
            'language' => 'plaintext',
            'lang' => '',  // Alias for language
            'title' => '',
            'highlight' => '',  // Line numbers to highlight (e.g., "1,3-5,8")
            'start' => '1',  // Starting line number
            'line_numbers' => null,  // Override global setting
            'copy_button' => null,  // Override global setting
            'class' => '',  // Additional CSS classes
            'id' => '',  // HTML ID
            'inline' => 'false',  // Inline code flag
            'escape' => 'true',  // Whether to escape HTML
        ), $atts, 'code');
        
        // Handle language alias
        if (!empty($atts['lang']) && empty($atts['language'])) {
            $atts['language'] = $atts['lang'];
        }
        
        // Sanitize attributes
        $language = $this->sanitize_language($atts['language']);
        $title = sanitize_text_field($atts['title']);
        $highlight_lines = sanitize_text_field($atts['highlight']);
        $start_line = absint($atts['start']);
        $additional_class = sanitize_html_class($atts['class']);
        $element_id = sanitize_html_class($atts['id']);
        $is_inline = filter_var($atts['inline'], FILTER_VALIDATE_BOOLEAN);
        $should_escape = filter_var($atts['escape'], FILTER_VALIDATE_BOOLEAN);
        
        // Determine line numbers setting
        $show_line_numbers = $atts['line_numbers'] !== null 
            ? filter_var($atts['line_numbers'], FILTER_VALIDATE_BOOLEAN)
            : get_option('chc_line_numbers', true);
            
        // Determine copy button setting
        $show_copy_button = $atts['copy_button'] !== null
            ? filter_var($atts['copy_button'], FILTER_VALIDATE_BOOLEAN)
            : get_option('chc_copy_button', true);
        
        // Process content
        $content = $this->process_code_content($content, $should_escape);
        
        // Generate cache key
        $cache_key = $this->generate_cache_key($atts, $content);
        
        // Check cache
        if (get_option('chc_cache_enabled', true) && isset($this->cache[$cache_key])) {
            return $this->cache[$cache_key];
        }
        
        // Build HTML
        if ($is_inline) {
            $html = $this->render_inline_code($content, $language, $additional_class);
        } else {
            $html = $this->render_code_block(
                $content,
                $language,
                $title,
                $show_line_numbers,
                $show_copy_button,
                $highlight_lines,
                $start_line,
                $additional_class,
                $element_id
            );
        }
        
        // Cache result
        if (get_option('chc_cache_enabled', true)) {
            $this->cache[$cache_key] = $html;
        }
        
        return $html;
    }
    
    /**
     * Render inline code shortcode
     *
     * @param array $atts Shortcode attributes
     * @param string $content Shortcode content
     * @return string Rendered HTML
     */
    public function render_inline_code_shortcode($atts, $content = null) {
        if (empty($content)) {
            return '';
        }
        
        $atts = shortcode_atts(array(
            'language' => 'plaintext',
            'class' => '',
        ), $atts, 'inline_code');
        
        $language = $this->sanitize_language($atts['language']);
        $additional_class = sanitize_html_class($atts['class']);
        
        return $this->render_inline_code($content, $language, $additional_class);
    }
    
    /**
     * Render code file shortcode
     *
     * @param array $atts Shortcode attributes
     * @param string $content Shortcode content
     * @return string Rendered HTML
     */
    public function render_code_file_shortcode($atts, $content = null) {
        if (empty($content)) {
            return '';
        }
        
        $atts = shortcode_atts(array(
            'file' => '',
            'language' => 'plaintext',
            'line_numbers' => null,
            'copy_button' => null,
            'highlight' => '',
            'start' => '1',
            'class' => '',
        ), $atts, 'code_file');
        
        // Add file info to title
        $title = !empty($atts['file']) ? sprintf(__('File: %s', 'code-highlighter-copy'), $atts['file']) : '';
        
        // Merge attributes and render
        $atts['title'] = $title;
        return $this->render_code_shortcode($atts, $content);
    }
    
    /**
     * Render language-specific shortcode
     *
     * @param array $atts Shortcode attributes
     * @param string $content Shortcode content
     * @param string $tag The shortcode tag used
     * @return string Rendered HTML
     */
    public function render_language_shortcode($atts, $content = null, $tag = '') {
        if (empty($content)) {
            return '';
        }
        
        // Get the language from the shortcode tag
        $language = $this->normalize_language($tag);
        
        // Parse attributes with language preset
        $atts = shortcode_atts(array(
            'title' => '',
            'highlight' => '',
            'start' => '1',
            'line_numbers' => null,
            'copy_button' => null,
            'class' => '',
            'id' => '',
            'escape' => 'true',
        ), $atts, $tag);
        
        // Set the language attribute
        $atts['language'] = $language;
        
        // Process the content preserving formatting
        $content = $this->preserve_code_formatting($content);
        
        // Render using the main code shortcode handler
        return $this->render_code_shortcode($atts, $content);
    }
    
    /**
     * Normalize language name from alias
     *
     * @param string $alias Language alias or name
     * @return string Normalized language name
     */
    private function normalize_language($alias) {
        $alias = strtolower(trim($alias));
        
        if (isset($this->language_aliases[$alias])) {
            return $this->language_aliases[$alias];
        }
        
        return 'plaintext';
    }
    
    /**
     * Preserve code formatting
     *
     * @param string $content Raw code content
     * @return string Formatted code content
     */
    private function preserve_code_formatting($content) {
        // Remove any wrapping paragraph tags that WordPress might have added
        $content = preg_replace('/<\/?p>/i', '', $content);
        
        // Convert HTML entities back to characters for proper display
        $content = html_entity_decode($content, ENT_QUOTES | ENT_HTML5, get_bloginfo('charset'));
        
        // Preserve line breaks
        $content = str_replace(array('<br />', '<br>', '<br/>'), "\n", $content);
        
        // Normalize line endings
        $content = str_replace(array("\r\n", "\r"), "\n", $content);
        
        // Trim only the very beginning and end, preserving internal whitespace
        $content = preg_replace('/^\n+|\n+$/', '', $content);
        
        return $content;
    }
    
    /**
     * Render code block HTML
     *
     * @param string $content Code content
     * @param string $language Programming language
     * @param string $title Optional title
     * @param bool $show_line_numbers Whether to show line numbers
     * @param bool $show_copy_button Whether to show copy button
     * @param string $highlight_lines Lines to highlight
     * @param int $start_line Starting line number
     * @param string $additional_class Additional CSS classes
     * @param string $element_id HTML ID
     * @return string Rendered HTML
     */
    private function render_code_block(
        $content,
        $language,
        $title = '',
        $show_line_numbers = true,
        $show_copy_button = true,
        $highlight_lines = '',
        $start_line = 1,
        $additional_class = '',
        $element_id = ''
    ) {
        // Generate unique ID if not provided
        if (empty($element_id)) {
            $element_id = 'chc-' . wp_generate_password(8, false);
        }
        
        // Build wrapper classes
        $wrapper_classes = array('chc-code-wrapper');
        if (!empty($additional_class)) {
            $wrapper_classes[] = $additional_class;
        }
        if ($show_line_numbers) {
            $wrapper_classes[] = 'line-numbers';
        }
        
        // Build pre attributes
        $pre_attrs = array(
            'class' => 'language-' . esc_attr($language),
            'id' => esc_attr($element_id),
        );
        
        if ($show_line_numbers && $start_line > 1) {
            $pre_attrs['data-start'] = $start_line;
        }
        
        if (!empty($highlight_lines)) {
            $pre_attrs['data-line'] = esc_attr($highlight_lines);
        }
        
        // Generate unique code ID
        $code_id = 'code-' . wp_generate_password(12, false);
        
        // Start building HTML with data-language attribute
        $html = '<div class="chcb-code-block ' . esc_attr(implode(' ', $wrapper_classes)) . '" data-language="' . esc_attr($language) . '">';
        
        // Add title if provided
        if (!empty($title)) {
            $html .= '<div class="chcb-title">' . esc_html($title) . '</div>';
        }
        
        // Add header with language label and copy button
        $html .= '<div class="chcb-header">';
        
        // Language label
        $language_label = $this->get_language_display_name($language);
        $html .= '<span class="chcb-language">' . esc_html($language_label) . '</span>';
        
        // Controls container
        $html .= '<div class="chcb-controls">';
        
        // Copy button with SVG icons
        if ($show_copy_button) {
            $copy_text = get_option('chc_copy_button_text', __('Копировать', 'code-highlighter-copy'));
            
            $html .= sprintf(
                '<button class="chcb-copy-btn" data-clipboard-target="#%s" aria-label="%s">
                    <span class="chcb-icon-container">
                        <svg class="chcb-icon chcb-icon-copy" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                        </svg>
                        <svg class="chcb-icon chcb-icon-check" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="display:none;">
                            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                        </svg>
                        <svg class="chcb-icon chcb-icon-error" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="display:none;">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                    </span>
                    <span class="chcb-btn-text">%s</span>
                    <div class="chcb-copy-tooltip">%s</div>
                    <span class="chcb-sr-only">%s</span>
                </button>',
                esc_attr($code_id),
                esc_attr__('Копировать код в буфер обмена', 'code-highlighter-copy'),
                esc_html($copy_text),
                esc_html__('Скопировано!', 'code-highlighter-copy'),
                esc_html__('Копировать код в буфер обмена', 'code-highlighter-copy')
            );
        }
        
        // Fullscreen button with SVG icons
        $html .= sprintf(
            '<button class="chcb-fullscreen-btn" aria-label="%s">
                <span class="chcb-icon-container">
                    <svg class="chcb-icon chcb-icon-expand" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
                    </svg>
                    <svg class="chcb-icon chcb-icon-compress" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="display:none;">
                        <path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
                    </svg>
                </span>
                <span class="chcb-btn-text">%s</span>
            </button>',
            esc_attr__('Полноэкранный режим', 'code-highlighter-copy'),
            esc_html__('Fullscreen', 'code-highlighter-copy')
        );
        
        $html .= '</div>'; // Close controls container
        $html .= '</div>'; // Close header
        
        // Add code block with proper classes
        $pre_classes = array();
        if ($show_line_numbers) {
            $pre_classes[] = 'line-numbers';
        }
        $pre_classes[] = 'language-' . esc_attr($language);
        
        $html .= '<pre class="' . esc_attr(implode(' ', $pre_classes)) . '"';
        
        // Add data attributes
        if ($show_line_numbers && $start_line > 1) {
            $html .= ' data-start="' . esc_attr($start_line) . '"';
        }
        if (!empty($highlight_lines)) {
            $html .= ' data-line="' . esc_attr($highlight_lines) . '"';
        }
        
        $html .= '>';
        $html .= '<code id="' . esc_attr($code_id) . '" class="language-' . esc_attr($language) . '">';
        $html .= $content;
        $html .= '</code>';
        $html .= '</pre>';
        
        $html .= '</div>';
        
        return $html;
    }
    
    /**
     * Render inline code HTML
     *
     * @param string $content Code content
     * @param string $language Programming language
     * @param string $additional_class Additional CSS classes
     * @return string Rendered HTML
     */
    private function render_inline_code($content, $language, $additional_class = '') {
        $classes = array('chc-inline-code', 'language-' . esc_attr($language));
        if (!empty($additional_class)) {
            $classes[] = $additional_class;
        }
        
        return sprintf(
            '<code class="%s">%s</code>',
            esc_attr(implode(' ', $classes)),
            esc_html($content)
        );
    }
    
    /**
     * Process code content
     *
     * @param string $content Raw content
     * @param bool $escape Whether to escape HTML
     * @return string Processed content
     */
    private function process_code_content($content, $escape = true) {
        // Remove shortcode wrapper if present
        $content = str_replace(array('[code]', '[/code]'), '', $content);
        
        // Decode HTML entities
        $content = html_entity_decode($content, ENT_QUOTES | ENT_HTML5, get_bloginfo('charset'));
        
        // Remove leading/trailing whitespace
        $content = trim($content);
        
        // Normalize line endings
        $content = str_replace(array("\r\n", "\r"), "\n", $content);
        
        // Escape HTML if needed
        if ($escape) {
            $content = esc_html($content);
        }
        
        return $content;
    }
    
    /**
     * Auto-highlight code blocks in content
     *
     * @param string $content Post content
     * @return string Modified content
     */
    public function auto_highlight_code($content) {
        // Find <pre><code> blocks
        $pattern = '/<pre[^>]*><code[^>]*>(.*?)<\/code><\/pre>/is';
        
        $content = preg_replace_callback($pattern, function($matches) {
            $code = $matches[1];
            $language = $this->detect_language($code);
            
            return $this->render_code_block(
                $code,
                $language,
                '',
                get_option('chc_line_numbers', true),
                get_option('chc_copy_button', true)
            );
        }, $content);
        
        return $content;
    }
    
    /**
     * Process code in comments
     *
     * @param string $comment Comment text
     * @return string Modified comment text
     */
    public function process_comment_code($comment) {
        // Only process if shortcodes are enabled in comments
        if (!get_option('chc_enable_in_comments', false)) {
            return $comment;
        }
        
        // Process shortcodes
        return do_shortcode($comment);
    }
    
    /**
     * Sanitize language identifier
     *
     * @param string $language Raw language
     * @return string Sanitized language
     */
    private function sanitize_language($language) {
        $language = strtolower(trim($language));
        
        // Use the centralized language aliases array
        if (isset($this->language_aliases[$language])) {
            $language = $this->language_aliases[$language];
        }
        
        // If language is not recognized, default to plaintext
        if (!isset($this->language_display_names[$language])) {
            $language = 'plaintext';
        }
        
        return $language;
    }
    
    /**
     * Get language label
     *
     * @param string $language Language identifier
     * @return string Language label
     */
    private function get_language_label($language) {
        $languages = $this->get_supported_languages();
        return isset($languages[$language]) ? $languages[$language] : ucfirst($language);
    }
    
    /**
     * Get language display name
     *
     * @param string $language Language identifier
     * @return string Language display name
     */
    private function get_language_display_name($language) {
        // First normalize the language
        $normalized = $this->normalize_language($language);
        
        // Return display name if exists
        if (isset($this->language_display_names[$normalized])) {
            return $this->language_display_names[$normalized];
        }
        
        // Fallback to uppercase first letter
        return ucfirst($normalized);
    }
    
    /**
     * Get supported languages
     *
     * @return array
     */
    private function get_supported_languages() {
        return array(
            'plaintext' => __('Plain Text', 'code-highlighter-copy'),
            'markup' => __('HTML/XML', 'code-highlighter-copy'),
            'css' => __('CSS', 'code-highlighter-copy'),
            'javascript' => __('JavaScript', 'code-highlighter-copy'),
            'php' => __('PHP', 'code-highlighter-copy'),
            'python' => __('Python', 'code-highlighter-copy'),
            'sql' => __('SQL', 'code-highlighter-copy'),
            'bash' => __('Bash', 'code-highlighter-copy'),
            'json' => __('JSON', 'code-highlighter-copy'),
            'yaml' => __('YAML', 'code-highlighter-copy'),
            'markdown' => __('Markdown', 'code-highlighter-copy'),
        );
    }
    
    /**
     * Detect language from code content
     *
     * @param string $code Code content
     * @return string Detected language
     */
    private function detect_language($code) {
        // Simple detection based on patterns
        $patterns = array(
            'php' => '/<\?php|\$[a-zA-Z_]/',
            'javascript' => '/function\s+\w+\s*\(|const\s+\w+\s*=|let\s+\w+\s*=/',
            'python' => '/def\s+\w+\s*\(|import\s+\w+|from\s+\w+\s+import/',
            'css' => '/[.#]\w+\s*{|@media|@import/',
            'sql' => '/SELECT\s+|INSERT\s+INTO|UPDATE\s+|DELETE\s+FROM/i',
            'bash' => '/^#!/|export\s+\w+=/m',
            'json' => '/^\s*{[\s\S]*}\s*$|^\s*\[[\s\S]*\]\s*$/',
        );
        
        foreach ($patterns as $language => $pattern) {
            if (preg_match($pattern, $code)) {
                return $language;
            }
        }
        
        // Check for HTML/XML
        if (preg_match('/<[a-zA-Z][^>]*>/', $code)) {
            return 'markup';
        }
        
        return 'plaintext';
    }
    
    /**
     * Generate cache key
     *
     * @param array $atts Attributes
     * @param string $content Content
     * @return string Cache key
     */
    private function generate_cache_key($atts, $content) {
        return md5(serialize($atts) . $content);
    }
    
    /**
     * Clear cache
     */
    public function clear_cache() {
        $this->cache = array();
        
        // Clear transient cache if used
        delete_transient('chc_code_cache');
    }
}