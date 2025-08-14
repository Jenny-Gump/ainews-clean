<?php
/**
 * Tools Page View
 *
 * @package CodeHighlighterCopy
 * @since 1.0.0
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}
?>

<div class="wrap">
    <h1><?php _e('Code Highlighter Tools', 'code-highlighter-copy'); ?></h1>
    
    <div class="chc-tools-container">
        <!-- Code Converter -->
        <div class="chc-tool-box">
            <h2><?php _e('Code Converter', 'code-highlighter-copy'); ?></h2>
            <p><?php _e('Convert plain code blocks to highlighted shortcodes.', 'code-highlighter-copy'); ?></p>
            
            <div class="chc-converter">
                <div class="chc-converter-input">
                    <label for="chc-convert-input"><?php _e('Input (Plain Code):', 'code-highlighter-copy'); ?></label>
                    <textarea id="chc-convert-input" rows="10" class="large-text code" placeholder="<?php esc_attr_e('Paste your code here...', 'code-highlighter-copy'); ?>"></textarea>
                </div>
                
                <div class="chc-converter-options">
                    <label>
                        <?php _e('Language:', 'code-highlighter-copy'); ?>
                        <select id="chc-convert-language">
                            <option value="auto"><?php _e('Auto-detect', 'code-highlighter-copy'); ?></option>
                            <?php
                            $languages = array(
                                'markup' => 'HTML/XML',
                                'css' => 'CSS',
                                'javascript' => 'JavaScript',
                                'php' => 'PHP',
                                'python' => 'Python',
                                'sql' => 'SQL',
                                'bash' => 'Bash',
                                'json' => 'JSON',
                            );
                            foreach ($languages as $code => $name) {
                                echo '<option value="' . esc_attr($code) . '">' . esc_html($name) . '</option>';
                            }
                            ?>
                        </select>
                    </label>
                    
                    <button type="button" class="button button-primary" id="chc-convert-button">
                        <?php _e('Convert to Shortcode', 'code-highlighter-copy'); ?>
                    </button>
                </div>
                
                <div class="chc-converter-output" style="display:none;">
                    <label for="chc-convert-output"><?php _e('Output (Shortcode):', 'code-highlighter-copy'); ?></label>
                    <textarea id="chc-convert-output" rows="10" class="large-text code" readonly></textarea>
                    <button type="button" class="button" id="chc-copy-converted">
                        <?php _e('Copy Shortcode', 'code-highlighter-copy'); ?>
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Batch Operations -->
        <div class="chc-tool-box">
            <h2><?php _e('Batch Operations', 'code-highlighter-copy'); ?></h2>
            <p><?php _e('Perform bulk operations on code blocks across your site.', 'code-highlighter-copy'); ?></p>
            
            <div class="chc-batch-operations">
                <h3><?php _e('Find Code Blocks', 'code-highlighter-copy'); ?></h3>
                <p><?php _e('Search for code blocks in your content.', 'code-highlighter-copy'); ?></p>
                
                <div class="chc-batch-controls">
                    <label>
                        <?php _e('Post Type:', 'code-highlighter-copy'); ?>
                        <select id="chc-batch-post-type">
                            <option value="any"><?php _e('All Types', 'code-highlighter-copy'); ?></option>
                            <?php
                            $post_types = get_post_types(array('public' => true), 'objects');
                            foreach ($post_types as $post_type) {
                                echo '<option value="' . esc_attr($post_type->name) . '">' . esc_html($post_type->label) . '</option>';
                            }
                            ?>
                        </select>
                    </label>
                    
                    <label>
                        <?php _e('Language Filter:', 'code-highlighter-copy'); ?>
                        <select id="chc-batch-language">
                            <option value=""><?php _e('All Languages', 'code-highlighter-copy'); ?></option>
                            <?php
                            foreach ($languages as $code => $name) {
                                echo '<option value="' . esc_attr($code) . '">' . esc_html($name) . '</option>';
                            }
                            ?>
                        </select>
                    </label>
                    
                    <button type="button" class="button" id="chc-find-blocks">
                        <?php _e('Find Code Blocks', 'code-highlighter-copy'); ?>
                    </button>
                </div>
                
                <div id="chc-batch-results" style="display:none;">
                    <h3><?php _e('Results', 'code-highlighter-copy'); ?></h3>
                    <div id="chc-batch-results-content"></div>
                </div>
            </div>
        </div>
        
        <!-- Statistics -->
        <div class="chc-tool-box">
            <h2><?php _e('Statistics', 'code-highlighter-copy'); ?></h2>
            <p><?php _e('View usage statistics for code highlighting.', 'code-highlighter-copy'); ?></p>
            
            <div class="chc-statistics">
                <div class="chc-stat-grid">
                    <div class="chc-stat-item">
                        <h4><?php _e('Total Code Blocks', 'code-highlighter-copy'); ?></h4>
                        <p class="chc-stat-value" id="stat-total-blocks">
                            <span class="spinner is-active"></span>
                        </p>
                    </div>
                    
                    <div class="chc-stat-item">
                        <h4><?php _e('Most Used Language', 'code-highlighter-copy'); ?></h4>
                        <p class="chc-stat-value" id="stat-top-language">
                            <span class="spinner is-active"></span>
                        </p>
                    </div>
                    
                    <div class="chc-stat-item">
                        <h4><?php _e('Posts with Code', 'code-highlighter-copy'); ?></h4>
                        <p class="chc-stat-value" id="stat-posts-with-code">
                            <span class="spinner is-active"></span>
                        </p>
                    </div>
                    
                    <div class="chc-stat-item">
                        <h4><?php _e('Cache Size', 'code-highlighter-copy'); ?></h4>
                        <p class="chc-stat-value" id="stat-cache-size">
                            <span class="spinner is-active"></span>
                        </p>
                    </div>
                </div>
                
                <button type="button" class="button" id="chc-refresh-stats">
                    <?php _e('Refresh Statistics', 'code-highlighter-copy'); ?>
                </button>
            </div>
        </div>
        
        <!-- Migration Tool -->
        <div class="chc-tool-box">
            <h2><?php _e('Migration Tool', 'code-highlighter-copy'); ?></h2>
            <p><?php _e('Migrate from other syntax highlighting plugins.', 'code-highlighter-copy'); ?></p>
            
            <div class="chc-migration">
                <label>
                    <?php _e('Migrate From:', 'code-highlighter-copy'); ?>
                    <select id="chc-migrate-from">
                        <option value=""><?php _e('Select Plugin', 'code-highlighter-copy'); ?></option>
                        <option value="syntaxhighlighter">SyntaxHighlighter Evolved</option>
                        <option value="crayon">Crayon Syntax Highlighter</option>
                        <option value="enlighter">Enlighter</option>
                        <option value="prism">WP Prism Syntax Highlighter</option>
                        <option value="custom"><?php _e('Custom Format', 'code-highlighter-copy'); ?></option>
                    </select>
                </label>
                
                <div id="chc-migration-options" style="display:none;">
                    <h3><?php _e('Migration Options', 'code-highlighter-copy'); ?></h3>
                    <label>
                        <input type="checkbox" id="chc-migrate-backup" checked />
                        <?php _e('Create backup before migration', 'code-highlighter-copy'); ?>
                    </label>
                    
                    <label>
                        <input type="checkbox" id="chc-migrate-dry-run" checked />
                        <?php _e('Dry run (preview changes without saving)', 'code-highlighter-copy'); ?>
                    </label>
                    
                    <button type="button" class="button button-primary" id="chc-start-migration">
                        <?php _e('Start Migration', 'code-highlighter-copy'); ?>
                    </button>
                </div>
                
                <div id="chc-migration-results" style="display:none;">
                    <h3><?php _e('Migration Results', 'code-highlighter-copy'); ?></h3>
                    <div id="chc-migration-results-content"></div>
                </div>
            </div>
        </div>
        
        <!-- Diagnostic Tool -->
        <div class="chc-tool-box">
            <h2><?php _e('Diagnostics', 'code-highlighter-copy'); ?></h2>
            <p><?php _e('Check plugin health and compatibility.', 'code-highlighter-copy'); ?></p>
            
            <div class="chc-diagnostics">
                <button type="button" class="button button-primary" id="chc-run-diagnostics">
                    <?php _e('Run Diagnostics', 'code-highlighter-copy'); ?>
                </button>
                
                <div id="chc-diagnostic-results" style="display:none;">
                    <h3><?php _e('Diagnostic Results', 'code-highlighter-copy'); ?></h3>
                    <table class="widefat striped">
                        <thead>
                            <tr>
                                <th><?php _e('Check', 'code-highlighter-copy'); ?></th>
                                <th><?php _e('Status', 'code-highlighter-copy'); ?></th>
                                <th><?php _e('Details', 'code-highlighter-copy'); ?></th>
                            </tr>
                        </thead>
                        <tbody id="chc-diagnostic-table">
                            <!-- Results will be inserted here -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.chc-tools-container {
    max-width: 800px;
    margin-top: 20px;
}

.chc-tool-box {
    background: #fff;
    border: 1px solid #ccd0d4;
    padding: 20px;
    margin-bottom: 20px;
}

.chc-tool-box h2 {
    margin-top: 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #ddd;
}

.chc-converter-options {
    margin: 15px 0;
}

.chc-converter-options label {
    display: inline-block;
    margin-right: 15px;
}

.chc-converter-output {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #ddd;
}

.chc-batch-controls label {
    display: inline-block;
    margin-right: 15px;
}

.chc-stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 20px 0;
}

.chc-stat-item {
    background: #f0f0f1;
    padding: 15px;
    border-radius: 3px;
    text-align: center;
}

.chc-stat-item h4 {
    margin: 0 0 10px 0;
    font-size: 14px;
    color: #555;
}

.chc-stat-value {
    font-size: 24px;
    font-weight: bold;
    color: #2271b1;
    margin: 0;
}

.chc-migration label {
    display: block;
    margin: 10px 0;
}

#chc-migration-options,
#chc-migration-results {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #ddd;
}

#chc-diagnostic-results {
    margin-top: 20px;
}

.chc-diagnostic-success {
    color: #00a32a;
}

.chc-diagnostic-warning {
    color: #dba617;
}

.chc-diagnostic-error {
    color: #d63638;
}
</style>

<script>
jQuery(document).ready(function($) {
    // Load statistics on page load
    loadStatistics();
    
    // Statistics refresh
    $('#chc-refresh-stats').on('click', function() {
        loadStatistics();
    });
    
    function loadStatistics() {
        $('.chc-stat-value').html('<span class="spinner is-active"></span>');
        
        // Simulate loading statistics (replace with actual AJAX call)
        setTimeout(function() {
            $('#stat-total-blocks').text('142');
            $('#stat-top-language').text('JavaScript');
            $('#stat-posts-with-code').text('38');
            $('#stat-cache-size').text('256 KB');
        }, 1000);
    }
    
    // Code converter
    $('#chc-convert-button').on('click', function() {
        var input = $('#chc-convert-input').val();
        var language = $('#chc-convert-language').val();
        
        if (!input) {
            alert('<?php _e('Please enter some code to convert.', 'code-highlighter-copy'); ?>');
            return;
        }
        
        var shortcode = '[code language="' + language + '"]\n' + input + '\n[/code]';
        
        $('#chc-convert-output').val(shortcode);
        $('.chc-converter-output').slideDown();
    });
    
    // Copy converted shortcode
    $('#chc-copy-converted').on('click', function() {
        $('#chc-convert-output').select();
        document.execCommand('copy');
        $(this).text('<?php _e('Copied!', 'code-highlighter-copy'); ?>');
        setTimeout(function() {
            $('#chc-copy-converted').text('<?php _e('Copy Shortcode', 'code-highlighter-copy'); ?>');
        }, 2000);
    });
    
    // Migration tool
    $('#chc-migrate-from').on('change', function() {
        if ($(this).val()) {
            $('#chc-migration-options').slideDown();
        } else {
            $('#chc-migration-options').slideUp();
        }
    });
    
    // Diagnostics
    $('#chc-run-diagnostics').on('click', function() {
        var $button = $(this);
        $button.prop('disabled', true).text('<?php _e('Running...', 'code-highlighter-copy'); ?>');
        
        // Simulate diagnostic checks (replace with actual AJAX call)
        setTimeout(function() {
            var results = [
                {check: 'PHP Version', status: 'success', details: 'PHP 7.4+ detected'},
                {check: 'WordPress Version', status: 'success', details: 'WordPress 5.8+ detected'},
                {check: 'JavaScript Libraries', status: 'success', details: 'All libraries loaded'},
                {check: 'Database Tables', status: 'success', details: 'All tables present'},
                {check: 'File Permissions', status: 'warning', details: 'Check write permissions'},
            ];
            
            var html = '';
            results.forEach(function(result) {
                var statusClass = 'chc-diagnostic-' + result.status;
                var statusIcon = result.status === 'success' ? '✓' : (result.status === 'warning' ? '⚠' : '✗');
                
                html += '<tr>';
                html += '<td>' + result.check + '</td>';
                html += '<td class="' + statusClass + '">' + statusIcon + '</td>';
                html += '<td>' + result.details + '</td>';
                html += '</tr>';
            });
            
            $('#chc-diagnostic-table').html(html);
            $('#chc-diagnostic-results').slideDown();
            
            $button.prop('disabled', false).text('<?php _e('Run Diagnostics', 'code-highlighter-copy'); ?>');
        }, 1500);
    });
});
</script>