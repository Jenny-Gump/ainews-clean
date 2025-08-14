/**
 * Code Highlighter Copy - Admin JavaScript
 * 
 * @package CodeHighlighterCopy
 * @since 1.0.0
 */

(function($) {
    'use strict';

    /**
     * Admin settings handler
     */
    const CHCAdmin = {
        
        /**
         * Initialize admin functions
         */
        init: function() {
            this.bindEvents();
            this.initTabs();
            this.initLivePreview();
            this.initShortcodeGenerator();
            this.initColorPicker();
            this.initCodeStatistics();
        },

        /**
         * Bind event handlers
         */
        bindEvents: function() {
            // AJAX form submission
            $('#chcb-settings-form').on('submit', this.handleFormSubmit.bind(this));
            
            // Reset settings button
            $('#chc-reset-settings').on('click', this.handleResetSettings.bind(this));
            
            // Clear cache button
            $('#chc-clear-cache').on('click', this.handleClearCache.bind(this));
            
            // Live preview update on settings change
            $('.chcb-setting-field').on('change', this.updateLivePreview.bind(this));
            
            // Export settings
            $('#chc-export-settings').on('click', this.handleExportSettings.bind(this));
            
            // Import settings
            $('#chc-import-file').on('change', this.handleImportPreview.bind(this));
            
            // Help links
            $('.chc-help-link').on('click', this.handleHelpLink.bind(this));
            
            // Database optimization
            $('#chc-optimize-db').on('click', this.handleOptimizeDatabase.bind(this));
        },

        /**
         * Initialize tabs system
         */
        initTabs: function() {
            const $tabs = $('.chcb-tab');
            const $contents = $('.chcb-tab-content');
            
            $tabs.on('click', function(e) {
                e.preventDefault();
                
                const targetId = $(this).data('tab');
                
                // Update active states
                $tabs.removeClass('active');
                $(this).addClass('active');
                
                // Show/hide content
                $contents.removeClass('active').hide();
                $('#' + targetId).addClass('active').fadeIn(300);
                
                // Save active tab to localStorage
                localStorage.setItem('chcb_active_tab', targetId);
            });
            
            // Restore last active tab
            const lastTab = localStorage.getItem('chcb_active_tab');
            if (lastTab) {
                $tabs.filter('[data-tab="' + lastTab + '"]').trigger('click');
            } else {
                $tabs.first().trigger('click');
            }
        },

        /**
         * Initialize live preview
         */
        initLivePreview: function() {
            const self = this;
            
            // Preview button
            $('#chc-preview-button').on('click', function() {
                self.generatePreview();
            });
            
            // Auto-update on language change
            $('#chc-preview-language').on('change', function() {
                self.generatePreview();
            });
            
            // Auto-update on code change (with debounce)
            let previewTimeout;
            $('#chc-preview-code').on('input', function() {
                clearTimeout(previewTimeout);
                previewTimeout = setTimeout(() => {
                    self.generatePreview();
                }, 500);
            });
            
            // Initial preview
            this.generatePreview();
        },

        /**
         * Generate live preview
         */
        generatePreview: function() {
            const code = $('#chc-preview-code').val();
            const language = $('#chc-preview-language').val();
            const theme = $('#chc_theme').val() || 'prism-tomorrow';
            const lineNumbers = $('#chc_line_numbers').is(':checked');
            const copyButton = $('#chc_copy_button').is(':checked');
            const showLanguage = $('#chc_show_language_label').is(':checked');
            
            // Build preview HTML
            let previewHtml = '<div class="chcb-code-container ' + theme + '">';
            
            if (showLanguage) {
                previewHtml += '<div class="chcb-code-header">';
                previewHtml += '<span class="chcb-language-label">' + this.getLanguageLabel(language) + '</span>';
                previewHtml += '</div>';
            }
            
            previewHtml += '<div class="chcb-code-wrapper">';
            previewHtml += '<pre class="' + (lineNumbers ? 'line-numbers' : '') + '">';
            previewHtml += '<code class="language-' + language + '">';
            previewHtml += this.escapeHtml(code);
            previewHtml += '</code></pre>';
            
            if (copyButton) {
                previewHtml += '<button class="chcb-copy-button" data-clipboard-text="' + this.escapeHtml(code) + '">';
                previewHtml += $('#chc_copy_button_text').val() || 'Copy';
                previewHtml += '</button>';
            }
            
            previewHtml += '</div></div>';
            
            $('#chc-preview-result').html(previewHtml);
            
            // Re-run Prism highlighting
            if (typeof Prism !== 'undefined') {
                Prism.highlightAllUnder(document.getElementById('chc-preview-result'));
            }
        },

        /**
         * Initialize shortcode generator
         */
        initShortcodeGenerator: function() {
            const self = this;
            
            $('#chc-generate-shortcode').on('click', function() {
                const language = $('#chc-gen-language').val();
                const title = $('#chc-gen-title').val();
                const lineNumbers = $('#chc-gen-line-numbers').is(':checked');
                const copyButton = $('#chc-gen-copy-button').is(':checked');
                
                let shortcode = '[code';
                
                if (language) {
                    shortcode += ' language="' + language + '"';
                }
                if (title) {
                    shortcode += ' title="' + title + '"';
                }
                if (!lineNumbers) {
                    shortcode += ' line_numbers="false"';
                }
                if (!copyButton) {
                    shortcode += ' copy_button="false"';
                }
                
                shortcode += ']';
                shortcode += '\n// Your code here\n';
                shortcode += '[/code]';
                
                $('#chc-shortcode-output').text(shortcode);
                $('#chc-generated-shortcode').slideDown();
                
                // Auto-select shortcode text
                self.selectText('chc-shortcode-output');
            });
            
            // Copy shortcode button
            $('#chc-copy-shortcode').on('click', function() {
                self.copyToClipboard($('#chc-shortcode-output').text());
                $(this).text('Copied!');
                setTimeout(() => {
                    $(this).text('Copy');
                }, 2000);
            });
        },

        /**
         * Initialize color picker for custom colors
         */
        initColorPicker: function() {
            // Add color pickers if needed
            $('.chcb-color-field').each(function() {
                $(this).wpColorPicker({
                    change: function() {
                        // Update preview on color change
                        CHCAdmin.updateLivePreview();
                    }
                });
            });
        },

        /**
         * Initialize code statistics
         */
        initCodeStatistics: function() {
            // Load statistics via AJAX
            $.ajax({
                url: ajaxurl,
                type: 'POST',
                data: {
                    action: 'chc_get_statistics',
                    nonce: chc_admin.nonce
                },
                success: function(response) {
                    if (response.success && response.data) {
                        CHCAdmin.displayStatistics(response.data);
                    }
                }
            });
        },

        /**
         * Display statistics
         */
        displayStatistics: function(stats) {
            if (!$('#chc-statistics').length) {
                return;
            }
            
            let html = '<div class="chc-stats-grid">';
            
            // Total blocks
            html += '<div class="chc-stat-item">';
            html += '<div class="chc-stat-value">' + (stats.total_blocks || 0) + '</div>';
            html += '<div class="chc-stat-label">Total Code Blocks</div>';
            html += '</div>';
            
            // Most used languages
            if (stats.languages) {
                html += '<div class="chc-stat-item">';
                html += '<div class="chc-stat-label">Most Used Languages</div>';
                html += '<ul class="chc-lang-list">';
                for (let lang in stats.languages) {
                    html += '<li>' + lang + ': ' + stats.languages[lang] + '</li>';
                }
                html += '</ul>';
                html += '</div>';
            }
            
            // Cache size
            if (stats.cache_size) {
                html += '<div class="chc-stat-item">';
                html += '<div class="chc-stat-value">' + stats.cache_size + '</div>';
                html += '<div class="chc-stat-label">Cache Size</div>';
                html += '</div>';
            }
            
            html += '</div>';
            
            $('#chc-statistics').html(html);
        },

        /**
         * Handle form submission via AJAX
         */
        handleFormSubmit: function(e) {
            e.preventDefault();
            
            const $form = $(e.target);
            const $submitButton = $form.find('input[type="submit"]');
            const originalText = $submitButton.val();
            
            // Show loading state
            $submitButton.val('Saving...').prop('disabled', true);
            
            // Gather form data
            const formData = $form.serialize();
            
            $.ajax({
                url: ajaxurl,
                type: 'POST',
                data: {
                    action: 'chc_save_settings',
                    nonce: chc_admin.nonce,
                    settings: formData
                },
                success: function(response) {
                    if (response.success) {
                        CHCAdmin.showNotification(response.data || 'Settings saved successfully!', 'success');
                        CHCAdmin.updateLivePreview();
                    } else {
                        CHCAdmin.showNotification(response.data || chc_admin.error_generic || 'Error saving settings', 'error');
                    }
                },
                error: function(xhr, status, error) {
                    let message = chc_admin.error_generic || 'Network error. Please try again.';
                    if (xhr.status === 403) {
                        message = 'Security check failed. Please refresh the page and try again.';
                    } else if (xhr.status === 429) {
                        message = 'Too many requests. Please wait a moment and try again.';
                    }
                    CHCAdmin.showNotification(message, 'error');
                },
                complete: function() {
                    // Restore button state
                    $submitButton.val(originalText).prop('disabled', false);
                }
            });
        },

        /**
         * Handle reset settings
         */
        handleResetSettings: function(e) {
            e.preventDefault();
            
            if (!confirm('Are you sure you want to reset all settings to defaults? This cannot be undone.')) {
                return;
            }
            
            const $button = $(e.target);
            const originalText = $button.text();
            
            $button.text('Resetting...').prop('disabled', true);
            
            $.ajax({
                url: ajaxurl,
                type: 'POST',
                data: {
                    action: 'chc_reset_settings',
                    nonce: chc_admin.nonce
                },
                success: function(response) {
                    if (response.success) {
                        CHCAdmin.showNotification('Settings reset to defaults!', 'success');
                        // Reload page to show default values
                        setTimeout(() => {
                            window.location.reload();
                        }, 1500);
                    } else {
                        CHCAdmin.showNotification(response.data || 'Error resetting settings', 'error');
                    }
                },
                complete: function() {
                    $button.text(originalText).prop('disabled', false);
                }
            });
        },

        /**
         * Handle clear cache
         */
        handleClearCache: function(e) {
            e.preventDefault();
            
            const $button = $(e.target);
            const originalText = $button.text();
            
            $button.text('Clearing...').prop('disabled', true);
            
            $.ajax({
                url: ajaxurl,
                type: 'POST',
                data: {
                    action: 'chc_clear_cache',
                    nonce: chc_admin.nonce
                },
                success: function(response) {
                    if (response.success) {
                        CHCAdmin.showNotification('Cache cleared successfully!', 'success');
                        // Update statistics
                        CHCAdmin.initCodeStatistics();
                    } else {
                        CHCAdmin.showNotification(response.data || 'Error clearing cache', 'error');
                    }
                },
                complete: function() {
                    $button.text(originalText).prop('disabled', false);
                }
            });
        },

        /**
         * Handle export settings
         */
        handleExportSettings: function(e) {
            e.preventDefault();
            
            // Trigger form submission for file download
            $('#chc-export-form').submit();
            
            CHCAdmin.showNotification('Settings exported successfully!', 'success');
        },

        /**
         * Handle import preview
         */
        handleImportPreview: function(e) {
            const file = e.target.files[0];
            
            if (!file) {
                return;
            }
            
            if (!file.name.endsWith('.json')) {
                CHCAdmin.showNotification('Please select a valid JSON file', 'error');
                e.target.value = '';
                return;
            }
            
            // Show file name
            $('#chc-import-filename').text(file.name);
        },

        /**
         * Handle help links
         */
        handleHelpLink: function(e) {
            e.preventDefault();
            
            const helpType = $(e.target).data('help');
            const $modal = $('#chc-help-modal');
            
            // Load help content
            let content = '';
            switch(helpType) {
                case 'shortcodes':
                    content = this.getShortcodeHelp();
                    break;
                case 'languages':
                    content = this.getLanguagesHelp();
                    break;
                case 'themes':
                    content = this.getThemesHelp();
                    break;
            }
            
            // Show modal with content
            if ($modal.length) {
                $modal.find('.modal-content').html(content);
                $modal.fadeIn();
            } else {
                // Fallback: show notification instead of alert
                CHCAdmin.showNotification($(content).text() || 'Информация доступна в консоли разработчика', 'info');
                if (typeof console !== 'undefined' && console.log) {
                    console.log('Modal content:', content);
                }
            }
        },

        /**
         * Update live preview
         */
        updateLivePreview: function() {
            // Debounce preview updates
            clearTimeout(this.previewTimeout);
            this.previewTimeout = setTimeout(() => {
                this.generatePreview();
            }, 300);
        },

        /**
         * Show notification
         */
        showNotification: function(message, type = 'success') {
            // Remove existing notifications
            $('.chcb-notice').remove();
            
            const notice = $('<div>')
                .addClass('notice notice-' + type + ' is-dismissible chcb-notice')
                .html('<p>' + message + '</p>');
            
            // Add dismiss button
            const dismissButton = $('<button type="button" class="notice-dismiss">');
            dismissButton.on('click', function() {
                notice.fadeOut(() => notice.remove());
            });
            notice.append(dismissButton);
            
            // Insert after page title
            $('.wrap h1').first().after(notice);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                notice.fadeOut(() => notice.remove());
            }, 5000);
        },

        /**
         * Utility: Escape HTML
         */
        escapeHtml: function(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;',
                '/': '&#x2F;',
                '`': '&#x60;',
                '=': '&#x3D;'
            };
            // Convert to string and escape, handle null/undefined
            return String(text || '').replace(/[&<>"'`=\/]/g, m => map[m]);
        },

        /**
         * Utility: Get language label
         */
        getLanguageLabel: function(language) {
            const labels = {
                'javascript': 'JavaScript',
                'php': 'PHP',
                'python': 'Python',
                'css': 'CSS',
                'markup': 'HTML',
                'sql': 'SQL',
                'bash': 'Bash',
                'java': 'Java',
                'csharp': 'C#',
                'cpp': 'C++',
                'typescript': 'TypeScript',
                'ruby': 'Ruby',
                'go': 'Go',
                'rust': 'Rust',
                'swift': 'Swift'
            };
            return labels[language] || language.toUpperCase();
        },

        /**
         * Utility: Select text
         */
        selectText: function(elementId) {
            const element = document.getElementById(elementId);
            if (window.getSelection && document.createRange) {
                const selection = window.getSelection();
                const range = document.createRange();
                range.selectNodeContents(element);
                selection.removeAllRanges();
                selection.addRange(range);
            }
        },

        /**
         * Utility: Copy to clipboard
         */
        copyToClipboard: function(text) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
        },

        /**
         * Get shortcode help content
         */
        getShortcodeHelp: function() {
            return `
                <h3>Using Shortcodes</h3>
                <p>Basic usage:</p>
                <pre>[code language="javascript"]
// Your code here
[/code]</pre>
                <p>With all options:</p>
                <pre>[code language="php" title="Example.php" line_numbers="true" copy_button="true" start_line="10"]
// Your PHP code
[/code]</pre>
                <h4>Available Parameters:</h4>
                <ul>
                    <li><code>language</code> - Programming language (e.g., php, javascript, python)</li>
                    <li><code>title</code> - Optional title for the code block</li>
                    <li><code>line_numbers</code> - Show line numbers (true/false)</li>
                    <li><code>copy_button</code> - Show copy button (true/false)</li>
                    <li><code>start_line</code> - Starting line number</li>
                    <li><code>highlight</code> - Highlight specific lines (e.g., "1,3-5,7")</li>
                </ul>
            `;
        },

        /**
         * Get languages help content
         */
        getLanguagesHelp: function() {
            return `
                <h3>Supported Languages</h3>
                <p>The following programming languages are supported:</p>
                <div class="chc-lang-grid">
                    <div>
                        <h4>Web Technologies</h4>
                        <ul>
                            <li>HTML/XML (markup)</li>
                            <li>CSS</li>
                            <li>JavaScript</li>
                            <li>TypeScript</li>
                            <li>PHP</li>
                        </ul>
                    </div>
                    <div>
                        <h4>Programming Languages</h4>
                        <ul>
                            <li>Python</li>
                            <li>Java</li>
                            <li>C/C++</li>
                            <li>C#</li>
                            <li>Go</li>
                            <li>Rust</li>
                            <li>Ruby</li>
                            <li>Swift</li>
                            <li>Kotlin</li>
                        </ul>
                    </div>
                    <div>
                        <h4>Scripting & Data</h4>
                        <ul>
                            <li>Bash/Shell</li>
                            <li>PowerShell</li>
                            <li>SQL</li>
                            <li>JSON</li>
                            <li>YAML</li>
                            <li>Markdown</li>
                        </ul>
                    </div>
                </div>
            `;
        },

        /**
         * Get themes help content
         */
        getThemesHelp: function() {
            return `
                <h3>Available Themes</h3>
                <p>Choose from these syntax highlighting themes:</p>
                <ul>
                    <li><strong>Default</strong> - Clean and simple light theme</li>
                    <li><strong>Tomorrow Night</strong> - Popular dark theme</li>
                    <li><strong>Okaidia</strong> - Sublime Text inspired</li>
                    <li><strong>Twilight</strong> - Dark purple theme</li>
                    <li><strong>Coy</strong> - Fun and playful theme</li>
                    <li><strong>Solarized Light</strong> - Popular light theme</li>
                    <li><strong>Dark</strong> - High contrast dark theme</li>
                    <li><strong>Funky</strong> - Vibrant and colorful</li>
                </ul>
                <p>You can preview each theme using the live preview panel.</p>
            `;
        },
        
        /**
         * Handle database optimization
         */
        handleOptimizeDatabase: function(e) {
            e.preventDefault();
            
            // Use localized confirmation message
            if (!confirm(chc_admin.confirm_optimize || 'This will optimize database tables and clear old data. Continue?')) {
                return;
            }
            
            const $button = $(e.target);
            const originalText = $button.text();
            
            $button.text('Optimizing...').prop('disabled', true);
            
            $.ajax({
                url: ajaxurl,
                type: 'POST',
                data: {
                    action: 'chc_optimize_database',
                    nonce: chc_admin.nonce
                },
                success: function(response) {
                    if (response.success) {
                        CHCAdmin.showNotification(response.data.message || 'Database optimized successfully!', 'success');
                        // Update statistics
                        CHCAdmin.initCodeStatistics();
                    } else {
                        CHCAdmin.showNotification(response.data || 'Error optimizing database', 'error');
                    }
                },
                error: function() {
                    CHCAdmin.showNotification('Network error. Please try again.', 'error');
                },
                complete: function() {
                    $button.text(originalText).prop('disabled', false);
                }
            });
        }
    };

    /**
     * Initialize when document is ready
     */
    $(document).ready(function() {
        // Check if we're on the settings page
        if ($('#chc-settings-container').length) {
            CHCAdmin.init();
        }
        
        // Initialize WordPress color picker if available
        if ($.fn.wpColorPicker) {
            $('.chcb-color-picker').wpColorPicker();
        }
        
        // Initialize select2 for better dropdowns if available
        if ($.fn.select2) {
            $('.chc-multiselect').select2({
                placeholder: 'Select languages...',
                allowClear: true
            });
        }
    });

})(jQuery);