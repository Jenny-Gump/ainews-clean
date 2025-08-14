<?php
/**
 * Settings Page View - Enhanced Version
 *
 * @package CodeHighlighterCopy
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Security check
if (!current_user_can('manage_options')) {
    wp_die(esc_html__('You do not have sufficient permissions to access this page.', 'code-highlighter-copy'));
}

// Enqueue admin scripts and styles
wp_enqueue_script('chc-admin-js', CHC_PLUGIN_URL . 'assets/js/admin.js', array('jquery'), CHC_VERSION, true);
wp_localize_script('chc-admin-js', 'chc_admin', array(
    'ajaxurl' => admin_url('admin-ajax.php'),
    'nonce' => wp_create_nonce('chc_admin_nonce'),
    'confirm_reset' => esc_html__('Are you sure you want to reset all settings to defaults?', 'code-highlighter-copy'),
    'confirm_clear_cache' => esc_html__('Are you sure you want to clear the cache?', 'code-highlighter-copy'),
    'confirm_optimize' => esc_html__('Are you sure you want to optimize the database?', 'code-highlighter-copy'),
    'error_generic' => esc_html__('An error occurred. Please try again.', 'code-highlighter-copy'),
    'success_generic' => esc_html__('Operation completed successfully.', 'code-highlighter-copy')
));

// Enqueue Prism for preview
wp_enqueue_script('chc-prism', CHC_PLUGIN_URL . 'assets/js/prism.js', array(), CHC_VERSION);
wp_enqueue_style('chc-prism', CHC_PLUGIN_URL . 'assets/css/prism.css', array(), CHC_VERSION);
wp_enqueue_style('chc-admin-styles', CHC_PLUGIN_URL . 'assets/css/admin-styles.css', array(), CHC_VERSION);
?>

<div class="wrap chcb-admin-wrap">
    <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
    
    <!-- Tabs Navigation -->
    <div class="chcb-tabs">
        <button class="chcb-tab active" data-tab="chcb-general">
            <span class="dashicons dashicons-admin-settings"></span>
            <?php _e('General', 'code-highlighter-copy'); ?>
        </button>
        <button class="chcb-tab" data-tab="chcb-appearance">
            <span class="dashicons dashicons-admin-appearance"></span>
            <?php _e('Appearance', 'code-highlighter-copy'); ?>
        </button>
        <button class="chcb-tab" data-tab="chcb-advanced">
            <span class="dashicons dashicons-admin-tools"></span>
            <?php _e('Advanced', 'code-highlighter-copy'); ?>
        </button>
        <button class="chcb-tab" data-tab="chcb-tools">
            <span class="dashicons dashicons-admin-generic"></span>
            <?php _e('Tools', 'code-highlighter-copy'); ?>
        </button>
        <button class="chcb-tab" data-tab="chcb-statistics">
            <span class="dashicons dashicons-chart-bar"></span>
            <?php _e('Statistics', 'code-highlighter-copy'); ?>
        </button>
    </div>

    <div class="chcb-settings-grid">
        <!-- Main Settings Area -->
        <div class="chcb-settings-main">
            <form method="post" action="options.php" id="chcb-settings-form">
                <?php settings_fields('chc_settings'); ?>
                
                <!-- General Settings Tab -->
                <div id="chcb-general" class="chcb-tab-content active">
                    <h2><?php _e('General Settings', 'code-highlighter-copy'); ?></h2>
                    <table class="form-table">
                        <tr>
                            <th scope="row"><?php _e('Default Theme', 'code-highlighter-copy'); ?></th>
                            <td>
                                <select name="chc_default_theme" id="chc_theme" class="chcb-setting-field">
                                    <?php
                                    $current_theme = get_option('chc_theme', 'prism-tomorrow');
                                    $themes = array(
                                        'prism' => 'Default Light',
                                        'prism-tomorrow' => 'Tomorrow Night',
                                        'prism-okaidia' => 'Okaidia',
                                        'prism-twilight' => 'Twilight',
                                        'prism-coy' => 'Coy',
                                        'prism-solarizedlight' => 'Solarized Light',
                                        'prism-dark' => 'Dark',
                                        'prism-funky' => 'Funky',
                                    );
                                    foreach ($themes as $value => $label) {
                                        echo '<option value="' . esc_attr($value) . '"' . selected($current_theme, $value, false) . '>' . esc_html($label) . '</option>';
                                    }
                                    ?>
                                </select>
                                <p class="description"><?php _e('Select the default syntax highlighting theme.', 'code-highlighter-copy'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Display Options', 'code-highlighter-copy'); ?></th>
                            <td>
                                <fieldset>
                                    <label>
                                        <input type="checkbox" name="chc_line_numbers" id="chc_line_numbers" value="1" <?php checked((bool) get_option('chc_line_numbers', true)); ?> class="chcb-setting-field" />
                                        <?php _e('Show line numbers by default', 'code-highlighter-copy'); ?>
                                    </label><br>
                                    <label>
                                        <input type="checkbox" name="chc_show_language_label" id="chc_show_language_label" value="1" <?php checked((bool) get_option('chc_show_language_label', true)); ?> class="chcb-setting-field" />
                                        <?php _e('Show language label in header', 'code-highlighter-copy'); ?>
                                    </label><br>
                                    <label>
                                        <input type="checkbox" name="chc_copy_button" id="chc_copy_button" value="1" <?php checked(get_option('chc_copy_button', true)); ?> class="chcb-setting-field" />
                                        <?php _e('Show copy button', 'code-highlighter-copy'); ?>
                                    </label><br>
                                    <label>
                                        <input type="checkbox" name="chc_fullscreen_mode" value="1" <?php checked(get_option('chc_fullscreen_mode', false)); ?> />
                                        <?php _e('Enable fullscreen mode button', 'code-highlighter-copy'); ?>
                                    </label>
                                </fieldset>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Copy Button Position', 'code-highlighter-copy'); ?></th>
                            <td>
                                <select name="chc_copy_button_position">
                                    <?php
                                    $position = get_option('chc_copy_button_position', 'top-right');
                                    $positions = array(
                                        'top-right' => 'Top Right',
                                        'top-left' => 'Top Left',
                                        'bottom-right' => 'Bottom Right',
                                        'bottom-left' => 'Bottom Left',
                                    );
                                    foreach ($positions as $value => $label) {
                                        echo '<option value="' . esc_attr($value) . '"' . selected($position, $value, false) . '>' . esc_html($label) . '</option>';
                                    }
                                    ?>
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Copy Button Text', 'code-highlighter-copy'); ?></th>
                            <td>
                                <input type="text" name="chc_copy_button_text" id="chc_copy_button_text" value="<?php echo esc_attr(get_option('chc_copy_button_text', 'Copy')); ?>" class="regular-text chcb-setting-field" />
                                <p class="description"><?php _e('Text to display on the copy button.', 'code-highlighter-copy'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Auto-detect Language', 'code-highlighter-copy'); ?></th>
                            <td>
                                <label>
                                    <input type="checkbox" name="chc_auto_detect_language" value="1" <?php checked(get_option('chc_auto_detect_language', false)); ?> />
                                    <?php _e('Automatically detect programming language from code content', 'code-highlighter-copy'); ?>
                                </label>
                                <p class="description"><?php _e('May impact performance on large code blocks.', 'code-highlighter-copy'); ?></p>
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- Appearance Settings Tab -->
                <div id="chcb-appearance" class="chcb-tab-content" style="display:none;">
                    <h2><?php _e('Appearance Settings', 'code-highlighter-copy'); ?></h2>
                    <table class="form-table">
                        <tr>
                            <th scope="row"><?php _e('Code Font Size', 'code-highlighter-copy'); ?></th>
                            <td>
                                <input type="range" name="chc_font_size" min="12" max="20" value="<?php echo esc_attr(get_option('chc_font_size', 14)); ?>" class="chcb-setting-field" />
                                <span id="chc-font-size-display"><?php echo esc_html(get_option('chc_font_size', 14)); ?>px</span>
                                <p class="description"><?php _e('Adjust the font size for code blocks.', 'code-highlighter-copy'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Code Font Family', 'code-highlighter-copy'); ?></th>
                            <td>
                                <select name="chc_font_family">
                                    <?php
                                    $current_font = get_option('chc_font_family', 'default');
                                    $fonts = array(
                                        'default' => 'System Default',
                                        'Monaco, monospace' => 'Monaco',
                                        'Consolas, monospace' => 'Consolas',
                                        '"Courier New", monospace' => 'Courier New',
                                        '"Source Code Pro", monospace' => 'Source Code Pro',
                                        '"Fira Code", monospace' => 'Fira Code',
                                        'Menlo, monospace' => 'Menlo',
                                        '"JetBrains Mono", monospace' => 'JetBrains Mono',
                                    );
                                    foreach ($fonts as $value => $label) {
                                        echo '<option value="' . esc_attr($value) . '"' . selected($current_font, $value, false) . '>' . esc_html($label) . '</option>';
                                    }
                                    ?>
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Maximum Block Height', 'code-highlighter-copy'); ?></th>
                            <td>
                                <input type="number" name="chc_max_height" value="<?php echo esc_attr(get_option('chc_max_height', 500)); ?>" min="200" max="1000" step="50" />
                                <span>px</span>
                                <p class="description"><?php _e('Maximum height before scrollbar appears. Set to 0 for no limit.', 'code-highlighter-copy'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Header Style', 'code-highlighter-copy'); ?></th>
                            <td>
                                <select name="chc_header_style">
                                    <?php
                                    $header_style = get_option('chc_header_style', 'gradient');
                                    $styles = array(
                                        'gradient' => 'Gradient',
                                        'solid' => 'Solid Color',
                                        'minimal' => 'Minimal',
                                        'none' => 'No Header',
                                    );
                                    foreach ($styles as $value => $label) {
                                        echo '<option value="' . esc_attr($value) . '"' . selected($header_style, $value, false) . '>' . esc_html($label) . '</option>';
                                    }
                                    ?>
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Border Radius', 'code-highlighter-copy'); ?></th>
                            <td>
                                <input type="range" name="chc_border_radius" min="0" max="20" value="<?php echo esc_attr(get_option('chc_border_radius', 4)); ?>" />
                                <span id="chc-radius-display"><?php echo esc_html(get_option('chc_border_radius', 4)); ?>px</span>
                                <p class="description"><?php _e('Roundness of code block corners.', 'code-highlighter-copy'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Custom CSS', 'code-highlighter-copy'); ?></th>
                            <td>
                                <textarea name="chc_custom_css" rows="10" cols="50" class="large-text code"><?php echo esc_textarea(get_option('chc_custom_css', '')); ?></textarea>
                                <p class="description"><?php _e('Add custom CSS styles for code blocks. Will be added inline.', 'code-highlighter-copy'); ?></p>
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- Advanced Settings Tab -->
                <div id="chcb-advanced" class="chcb-tab-content" style="display:none;">
                    <h2><?php _e('Advanced Settings', 'code-highlighter-copy'); ?></h2>
                    <table class="form-table">
                        <tr>
                            <th scope="row"><?php _e('Performance', 'code-highlighter-copy'); ?></th>
                            <td>
                                <fieldset>
                                    <label>
                                        <input type="checkbox" name="chc_lazy_loading" value="1" <?php checked(get_option('chc_lazy_loading', true)); ?> />
                                        <?php _e('Enable lazy loading for large code blocks', 'code-highlighter-copy'); ?>
                                    </label><br>
                                    <label>
                                        <input type="checkbox" name="chc_cache_enabled" value="1" <?php checked(get_option('chc_cache_enabled', true)); ?> />
                                        <?php _e('Enable caching of processed code blocks', 'code-highlighter-copy'); ?>
                                    </label><br>
                                    <label>
                                        <input type="checkbox" name="chc_minify_assets" value="1" <?php checked(get_option('chc_minify_assets', false)); ?> />
                                        <?php _e('Use minified CSS/JS files', 'code-highlighter-copy'); ?>
                                    </label>
                                </fieldset>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Cache Duration', 'code-highlighter-copy'); ?></th>
                            <td>
                                <input type="number" name="chc_cache_duration" value="<?php echo esc_attr(get_option('chc_cache_duration', 86400)); ?>" min="3600" max="604800" step="3600" />
                                <span>seconds</span>
                                <p class="description"><?php _e('How long to cache processed code blocks (3600 = 1 hour, 86400 = 24 hours).', 'code-highlighter-copy'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Keyboard Shortcuts', 'code-highlighter-copy'); ?></th>
                            <td>
                                <label>
                                    <input type="checkbox" name="chc_enable_shortcuts" value="1" <?php checked(get_option('chc_enable_shortcuts', false)); ?> />
                                    <?php _e('Enable keyboard shortcuts (Ctrl+C to copy when code is selected)', 'code-highlighter-copy'); ?>
                                </label>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Supported Languages', 'code-highlighter-copy'); ?></th>
                            <td>
                                <select name="chc_supported_languages[]" multiple="multiple" class="chc-multiselect" size="10" style="width: 100%; max-width: 400px;">
                                    <?php
                                    $selected_langs = get_option('chc_supported_languages', array('markup', 'css', 'javascript', 'php', 'python'));
                                    $all_languages = array(
                                        'markup' => 'HTML/XML',
                                        'css' => 'CSS',
                                        'javascript' => 'JavaScript',
                                        'php' => 'PHP',
                                        'python' => 'Python',
                                        'sql' => 'SQL',
                                        'bash' => 'Bash/Shell',
                                        'json' => 'JSON',
                                        'yaml' => 'YAML',
                                        'markdown' => 'Markdown',
                                        'java' => 'Java',
                                        'c' => 'C',
                                        'cpp' => 'C++',
                                        'csharp' => 'C#',
                                        'go' => 'Go',
                                        'rust' => 'Rust',
                                        'typescript' => 'TypeScript',
                                        'ruby' => 'Ruby',
                                        'swift' => 'Swift',
                                        'kotlin' => 'Kotlin',
                                        'scala' => 'Scala',
                                        'r' => 'R',
                                        'matlab' => 'MATLAB',
                                        'powershell' => 'PowerShell',
                                        'objectivec' => 'Objective-C',
                                        'perl' => 'Perl',
                                        'lua' => 'Lua',
                                        'dart' => 'Dart',
                                        'groovy' => 'Groovy',
                                        'haskell' => 'Haskell',
                                        'erlang' => 'Erlang',
                                        'clojure' => 'Clojure',
                                        'fsharp' => 'F#',
                                        'pascal' => 'Pascal',
                                        'latex' => 'LaTeX',
                                        'arduino' => 'Arduino',
                                        'actionscript' => 'ActionScript',
                                        'diff' => 'Diff',
                                    );
                                    foreach ($all_languages as $code => $name) {
                                        $selected = in_array($code, $selected_langs) ? ' selected="selected"' : '';
                                        echo '<option value="' . esc_attr($code) . '"' . $selected . '>' . esc_html($name) . '</option>';
                                    }
                                    ?>
                                </select>
                                <p class="description"><?php _e('Select which programming languages to load. Loading fewer languages improves performance.', 'code-highlighter-copy'); ?></p>
                            </td>
                        </tr>
                        <tr>
                            <th scope="row"><?php _e('Load Assets', 'code-highlighter-copy'); ?></th>
                            <td>
                                <select name="chc_load_assets">
                                    <?php
                                    $load_option = get_option('chc_load_assets', 'auto');
                                    $options = array(
                                        'auto' => 'Auto-detect (recommended)',
                                        'always' => 'Always load on all pages',
                                        'posts' => 'Only on posts and pages',
                                        'manual' => 'Manual (use wp_enqueue functions)',
                                    );
                                    foreach ($options as $value => $label) {
                                        echo '<option value="' . esc_attr($value) . '"' . selected($load_option, $value, false) . '>' . esc_html($label) . '</option>';
                                    }
                                    ?>
                                </select>
                                <p class="description"><?php _e('Control when plugin assets (CSS/JS) are loaded.', 'code-highlighter-copy'); ?></p>
                            </td>
                        </tr>
                    </table>
                </div>

                <!-- Tools Tab -->
                <div id="chcb-tools" class="chcb-tab-content" style="display:none;">
                    <h2><?php _e('Tools & Maintenance', 'code-highlighter-copy'); ?></h2>
                    
                    <!-- Cache Management -->
                    <div class="chcb-tool-section">
                        <h3><?php _e('Cache Management', 'code-highlighter-copy'); ?></h3>
                        <p>
                            <button type="button" class="button" id="chc-clear-cache">
                                <?php _e('Clear All Cache', 'code-highlighter-copy'); ?>
                            </button>
                            <span class="description"><?php _e('Clear all cached code blocks and transients.', 'code-highlighter-copy'); ?></span>
                        </p>
                    </div>

                    <!-- Settings Management -->
                    <div class="chcb-tool-section">
                        <h3><?php _e('Settings Management', 'code-highlighter-copy'); ?></h3>
                        <p>
                            <button type="button" class="button" id="chc-reset-settings">
                                <?php _e('Reset to Defaults', 'code-highlighter-copy'); ?>
                            </button>
                            <span class="description"><?php _e('Reset all settings to their default values.', 'code-highlighter-copy'); ?></span>
                        </p>
                    </div>

                    <!-- Import/Export -->
                    <div class="chcb-tool-section">
                        <h3><?php _e('Import/Export Settings', 'code-highlighter-copy'); ?></h3>
                        
                        <div class="chc-export-section">
                            <h4><?php _e('Export Settings', 'code-highlighter-copy'); ?></h4>
                            <p><?php _e('Download your current settings as a JSON file for backup or migration.', 'code-highlighter-copy'); ?></p>
                            <form method="post" action="<?php echo admin_url('admin-post.php'); ?>" id="chc-export-form">
                                <input type="hidden" name="action" value="chc_export_settings" />
                                <?php wp_nonce_field('chc_export_settings'); ?>
                                <button type="submit" class="button button-primary" id="chc-export-settings">
                                    <span class="dashicons dashicons-download"></span>
                                    <?php _e('Export Settings', 'code-highlighter-copy'); ?>
                                </button>
                            </form>
                        </div>
                        
                        <div class="chc-import-section">
                            <h4><?php _e('Import Settings', 'code-highlighter-copy'); ?></h4>
                            <p><?php _e('Restore settings from a previously exported JSON file.', 'code-highlighter-copy'); ?></p>
                            <form method="post" action="<?php echo admin_url('admin-post.php'); ?>" enctype="multipart/form-data">
                                <input type="hidden" name="action" value="chc_import_settings" />
                                <?php wp_nonce_field('chc_import_settings'); ?>
                                <input type="file" name="import_file" id="chc-import-file" accept=".json" required />
                                <span id="chc-import-filename"></span>
                                <br><br>
                                <button type="submit" class="button">
                                    <span class="dashicons dashicons-upload"></span>
                                    <?php _e('Import Settings', 'code-highlighter-copy'); ?>
                                </button>
                            </form>
                        </div>
                    </div>

                    <!-- Database Optimization -->
                    <div class="chcb-tool-section">
                        <h3><?php _e('Database Optimization', 'code-highlighter-copy'); ?></h3>
                        <p>
                            <button type="button" class="button" id="chc-optimize-db">
                                <?php _e('Optimize Database Tables', 'code-highlighter-copy'); ?>
                            </button>
                            <span class="description"><?php _e('Clean up and optimize plugin database entries.', 'code-highlighter-copy'); ?></span>
                        </p>
                    </div>
                </div>

                <!-- Statistics Tab -->
                <div id="chcb-statistics" class="chcb-tab-content" style="display:none;">
                    <h2><?php _e('Usage Statistics', 'code-highlighter-copy'); ?></h2>
                    <div id="chc-statistics">
                        <div class="chc-loading">
                            <span class="spinner is-active"></span>
                            <?php _e('Loading statistics...', 'code-highlighter-copy'); ?>
                        </div>
                    </div>
                </div>

                <?php submit_button(__('Save All Settings', 'code-highlighter-copy'), 'primary', 'submit', true, array('style' => 'display:none;')); ?>
            </form>
        </div>

        <!-- Sidebar -->
        <div class="chcb-settings-sidebar">
            <!-- Live Preview -->
            <div class="chcb-preview-section">
                <h3><?php _e('Live Preview', 'code-highlighter-copy'); ?></h3>
                <div class="chc-preview-controls">
                    <label for="chc-preview-language"><?php _e('Language:', 'code-highlighter-copy'); ?></label>
                    <select id="chc-preview-language">
                        <option value="javascript">JavaScript</option>
                        <option value="php">PHP</option>
                        <option value="python">Python</option>
                        <option value="css">CSS</option>
                        <option value="markup">HTML</option>
                        <option value="sql">SQL</option>
                        <option value="bash">Bash</option>
                    </select>
                </div>
                <div class="chc-preview-input">
                    <label for="chc-preview-code"><?php _e('Sample Code:', 'code-highlighter-copy'); ?></label>
                    <textarea id="chc-preview-code" rows="6">// Example code
function helloWorld() {
    console.log("Hello, World!");
    return true;
}
helloWorld();</textarea>
                </div>
                <button type="button" class="button button-primary" id="chc-preview-button">
                    <?php _e('Update Preview', 'code-highlighter-copy'); ?>
                </button>
                <div id="chc-preview-result"></div>
            </div>
            
            <!-- Shortcode Generator -->
            <div class="chcb-shortcode-generator">
                <h3><?php _e('Shortcode Generator', 'code-highlighter-copy'); ?></h3>
                <div class="chc-generator-controls">
                    <label>
                        <?php _e('Language:', 'code-highlighter-copy'); ?>
                        <select id="chc-gen-language">
                            <option value="">Auto-detect</option>
                            <option value="javascript">JavaScript</option>
                            <option value="php">PHP</option>
                            <option value="python">Python</option>
                            <option value="css">CSS</option>
                            <option value="markup">HTML</option>
                            <option value="sql">SQL</option>
                            <option value="bash">Bash</option>
                            <option value="java">Java</option>
                            <option value="csharp">C#</option>
                        </select>
                    </label>
                    
                    <label>
                        <?php _e('Title:', 'code-highlighter-copy'); ?>
                        <input type="text" id="chc-gen-title" placeholder="Optional file name" />
                    </label>
                    
                    <label>
                        <input type="checkbox" id="chc-gen-line-numbers" checked />
                        <?php _e('Show Line Numbers', 'code-highlighter-copy'); ?>
                    </label>
                    
                    <label>
                        <input type="checkbox" id="chc-gen-copy-button" checked />
                        <?php _e('Show Copy Button', 'code-highlighter-copy'); ?>
                    </label>
                    
                    <label>
                        <?php _e('Start Line:', 'code-highlighter-copy'); ?>
                        <input type="number" id="chc-gen-start-line" placeholder="1" min="1" />
                    </label>
                    
                    <label>
                        <?php _e('Highlight Lines:', 'code-highlighter-copy'); ?>
                        <input type="text" id="chc-gen-highlight" placeholder="e.g., 1,3-5,7" />
                    </label>
                </div>
                
                <button type="button" class="button button-primary" id="chc-generate-shortcode">
                    <?php _e('Generate Shortcode', 'code-highlighter-copy'); ?>
                </button>
                
                <div id="chc-generated-shortcode" style="display:none;">
                    <h4><?php _e('Your Shortcode:', 'code-highlighter-copy'); ?></h4>
                    <code id="chc-shortcode-output"></code>
                    <button type="button" class="button button-small" id="chc-copy-shortcode">
                        <?php _e('Copy', 'code-highlighter-copy'); ?>
                    </button>
                </div>
            </div>
            
            <!-- Help & Documentation -->
            <div class="chcb-help-box">
                <h3><?php _e('Quick Help', 'code-highlighter-copy'); ?></h3>
                <ul>
                    <li>
                        <a href="#" class="chc-help-link" data-help="shortcodes">
                            <span class="dashicons dashicons-editor-code"></span>
                            <?php _e('How to use shortcodes', 'code-highlighter-copy'); ?>
                        </a>
                    </li>
                    <li>
                        <a href="#" class="chc-help-link" data-help="languages">
                            <span class="dashicons dashicons-translation"></span>
                            <?php _e('Supported languages', 'code-highlighter-copy'); ?>
                        </a>
                    </li>
                    <li>
                        <a href="#" class="chc-help-link" data-help="themes">
                            <span class="dashicons dashicons-admin-appearance"></span>
                            <?php _e('Available themes', 'code-highlighter-copy'); ?>
                        </a>
                    </li>
                    <li>
                        <a href="https://prismjs.com/" target="_blank">
                            <span class="dashicons dashicons-external"></span>
                            <?php _e('Prism.js Documentation', 'code-highlighter-copy'); ?>
                        </a>
                    </li>
                </ul>
            </div>
            
            <!-- Plugin Info -->
            <div class="chcb-info-box">
                <h3><?php _e('Plugin Information', 'code-highlighter-copy'); ?></h3>
                <table class="chcb-info-table">
                    <tr>
                        <td><strong><?php _e('Version:', 'code-highlighter-copy'); ?></strong></td>
                        <td><?php echo CHC_VERSION; ?></td>
                    </tr>
                    <tr>
                        <td><strong><?php _e('PHP Version:', 'code-highlighter-copy'); ?></strong></td>
                        <td><?php echo PHP_VERSION; ?></td>
                    </tr>
                    <tr>
                        <td><strong><?php _e('WordPress:', 'code-highlighter-copy'); ?></strong></td>
                        <td><?php echo get_bloginfo('version'); ?></td>
                    </tr>
                    <tr>
                        <td><strong><?php _e('Author:', 'code-highlighter-copy'); ?></strong></td>
                        <td>AI News Team</td>
                    </tr>
                    <tr>
                        <td><strong><?php _e('Support:', 'code-highlighter-copy'); ?></strong></td>
                        <td><a href="https://ailynx.ru" target="_blank">ailynx.ru</a></td>
                    </tr>
                </table>
            </div>
        </div>
    </div>
</div>

<!-- Help Modal -->
<div id="chc-help-modal" class="chc-modal" style="display:none;">
    <div class="chc-modal-content">
        <span class="chc-modal-close">&times;</span>
        <div class="modal-content">
            <!-- Content will be loaded dynamically -->
        </div>
    </div>
</div>