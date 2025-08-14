/**
 * Code Highlighter Copy - Frontend JavaScript
 * Version: 1.0.0
 */

(function() {
    'use strict';
    
    // Define debug flag
    window.CHC_DEBUG = false;
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializePlugin);
    } else {
        initializePlugin();
    }
    
    /**
     * Initialize the plugin
     */
    function initializePlugin() {
        // Initialize Prism.js if available
        if (typeof Prism !== 'undefined') {
            // Configure Prism
            configurePrism();
            
            // Highlight all code blocks
            Prism.highlightAll();
            
            // Process custom code blocks
            processCodeBlocks();
        }
        
        // Initialize Clipboard.js if available
        if (typeof ClipboardJS !== 'undefined') {
            initializeClipboard();
        }
        
        // Initialize fullscreen functionality
        initializeFullscreen();
        
        // Listen for dynamic content
        observeDynamicContent();
        
        // Handle WordPress block editor preview
        handleBlockEditorPreview();
    }
    
    /**
     * Configure Prism.js settings
     */
    function configurePrism() {
        // Set Prism configuration
        if (typeof Prism.plugins !== 'undefined') {
            // Configure normalize whitespace plugin
            if (Prism.plugins.NormalizeWhitespace) {
                Prism.plugins.NormalizeWhitespace.setDefaults({
                    'remove-trailing': true,
                    'remove-indent': true,
                    'left-trim': true,
                    'right-trim': true,
                    'break-lines': 80,
                    'remove-initial-line-feed': false,
                    'tabs-to-spaces': 4
                });
            }
            
            // Configure autolinker plugin
            if (Prism.plugins.Autolinker) {
                Prism.plugins.Autolinker.setDefaults({
                    'url': true,
                    'email': true,
                    'phone': false
                });
            }
        }
    }
    
    /**
     * Process all code blocks and add custom wrapper
     */
    function processCodeBlocks() {
        // Find all Prism code blocks
        const codeBlocks = document.querySelectorAll('pre[class*="language-"]');
        
        codeBlocks.forEach(function(pre) {
            // Skip if already processed
            if (pre.closest('.chcb-code-block')) {
                return;
            }
            
            // Get language from class
            const languageClass = Array.from(pre.classList).find(cls => cls.startsWith('language-'));
            const language = languageClass ? languageClass.replace('language-', '') : 'code';
            
            // Create wrapper
            const wrapper = createCodeBlockWrapper(pre, language);
            
            // Replace pre with wrapper
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(pre);
            
            // Add fade-in animation
            wrapper.classList.add('chcb-fade-in');
        });
    }
    
    /**
     * Create wrapper for code block
     */
    function createCodeBlockWrapper(pre, language) {
        // Create main wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'chcb-code-block';
        wrapper.setAttribute('data-language', language);
        
        // Check if line numbers are enabled
        if (pre.classList.contains('line-numbers') || (typeof chc_params !== 'undefined' && chc_params && chc_params.line_numbers)) {
            wrapper.classList.add('line-numbers');
            pre.classList.add('line-numbers');
        }
        
        // Create header
        const header = createCodeBlockHeader(pre, language);
        wrapper.appendChild(header);
        wrapper.classList.add('has-header');
        
        return wrapper;
    }
    
    /**
     * Create header for code block
     */
    function createCodeBlockHeader(pre, language) {
        const header = document.createElement('div');
        header.className = 'chcb-header';
        
        // Create language label
        const langLabel = document.createElement('span');
        langLabel.className = 'chcb-language';
        langLabel.textContent = getLanguageDisplayName(language);
        header.appendChild(langLabel);
        
        // Create copy button if enabled
        if (typeof chc_params === 'undefined' || !chc_params || chc_params.copy_button !== false) {
            const copyBtn = createCopyButton(pre);
            header.appendChild(copyBtn);
        }
        
        return header;
    }
    
    /**
     * Create copy button with SVG icons
     */
    function createCopyButton(pre) {
        const btn = document.createElement('button');
        btn.className = 'chcb-copy-btn';
        btn.type = 'button';
        btn.setAttribute('aria-label', 'Copy code to clipboard');
        
        // Create icon container
        const iconContainer = document.createElement('span');
        iconContainer.className = 'chcb-icon-container';
        
        // Copy icon SVG
        const copyIcon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        copyIcon.setAttribute('class', 'chcb-icon chcb-icon-copy');
        copyIcon.setAttribute('width', '16');
        copyIcon.setAttribute('height', '16');
        copyIcon.setAttribute('viewBox', '0 0 24 24');
        copyIcon.setAttribute('fill', 'currentColor');
        copyIcon.innerHTML = '<path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>';
        
        // Check icon SVG
        const checkIcon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        checkIcon.setAttribute('class', 'chcb-icon chcb-icon-check');
        checkIcon.setAttribute('width', '16');
        checkIcon.setAttribute('height', '16');
        checkIcon.setAttribute('viewBox', '0 0 24 24');
        checkIcon.setAttribute('fill', 'currentColor');
        checkIcon.style.display = 'none';
        checkIcon.innerHTML = '<path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>';
        
        // Error icon SVG
        const errorIcon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        errorIcon.setAttribute('class', 'chcb-icon chcb-icon-error');
        errorIcon.setAttribute('width', '16');
        errorIcon.setAttribute('height', '16');
        errorIcon.setAttribute('viewBox', '0 0 24 24');
        errorIcon.setAttribute('fill', 'currentColor');
        errorIcon.style.display = 'none';
        errorIcon.innerHTML = '<path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>';
        
        iconContainer.appendChild(copyIcon);
        iconContainer.appendChild(checkIcon);
        iconContainer.appendChild(errorIcon);
        btn.appendChild(iconContainer);
        
        // Add text span
        const textSpan = document.createElement('span');
        textSpan.className = 'chcb-btn-text';
        textSpan.textContent = (typeof chc_params !== 'undefined' && chc_params && chc_params.copy_text) || 'Копировать';
        btn.appendChild(textSpan);
        
        // Create tooltip
        const tooltip = document.createElement('div');
        tooltip.className = 'chcb-copy-tooltip';
        tooltip.textContent = 'Скопировано!';
        btn.appendChild(tooltip);
        
        // Generate unique ID for the code element
        const codeId = 'chcb-code-' + Math.random().toString(36).substr(2, 9);
        const code = pre.querySelector('code');
        if (code) {
            code.id = codeId;
            btn.setAttribute('data-clipboard-target', '#' + codeId);
        }
        
        // Add screen reader text
        const srText = document.createElement('span');
        srText.className = 'chcb-sr-only';
        srText.textContent = 'Copy code to clipboard';
        btn.appendChild(srText);
        
        return btn;
    }
    
    /**
     * Get clean code without line numbers and formatting
     */
    function getCleanCode(codeElement) {
        if (!codeElement) return '';
        
        // Clone the code element to avoid modifying the original
        const clone = codeElement.cloneNode(true);
        
        // Remove line number elements if they exist
        const lineNumbersRows = clone.querySelector('.line-numbers-rows');
        if (lineNumbersRows) {
            lineNumbersRows.remove();
        }
        
        // Get the text content
        let text = clone.textContent || clone.innerText || '';
        
        // Clean up extra whitespace while preserving code formatting
        text = text.replace(/^\n+|\n+$/g, ''); // Trim leading/trailing newlines
        
        return text;
    }
    
    /**
     * Fallback copy method for older browsers
     */
    function fallbackCopyTextToClipboard(text, button) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        let success = false;
        try {
            success = document.execCommand('copy');
            if (success) {
                handleCopySuccess(button, text);
            } else {
                handleCopyError(button);
            }
        } catch (err) {
            // Log error only in debug mode
            if (typeof console !== 'undefined' && window.CHC_DEBUG) {
                console.error('Fallback: Unable to copy', err);
            }
            handleCopyError(button);
        } finally {
            document.body.removeChild(textArea);
        }
        
        return success;
    }
    
    /**
     * Handle successful copy
     */
    function handleCopySuccess(button, text) {
        const copyIcon = button.querySelector('.chcb-icon-copy');
        const checkIcon = button.querySelector('.chcb-icon-check');
        const textSpan = button.querySelector('.chcb-btn-text');
        const tooltip = button.querySelector('.chcb-copy-tooltip');
        const originalText = textSpan ? textSpan.textContent : '';
        const copiedText = (typeof chc_params !== 'undefined' && chc_params && chc_params.copied_text) || 'Скопировано!';
        
        // Update button state
        button.classList.add('copied');
        if (copyIcon) copyIcon.style.display = 'none';
        if (checkIcon) checkIcon.style.display = 'block';
        if (textSpan) textSpan.textContent = copiedText;
        
        // Show tooltip with animation
        if (tooltip) {
            tooltip.textContent = copiedText;
            tooltip.classList.add('show');
        }
        
        // Add ripple effect
        createRippleEffect(button);
        
        // Reset after delay
        setTimeout(function() {
            button.classList.remove('copied');
            if (copyIcon) copyIcon.style.display = 'block';
            if (checkIcon) checkIcon.style.display = 'none';
            if (textSpan) textSpan.textContent = originalText;
            if (tooltip) tooltip.classList.remove('show');
        }, 2000);
        
        // Trigger custom event
        triggerEvent('chcb:copied', { button: button, text: text });
    }
    
    /**
     * Handle copy error
     */
    function handleCopyError(button) {
        const copyIcon = button.querySelector('.chcb-icon-copy');
        const errorIcon = button.querySelector('.chcb-icon-error');
        const textSpan = button.querySelector('.chcb-btn-text');
        const tooltip = button.querySelector('.chcb-copy-tooltip');
        const originalText = textSpan ? textSpan.textContent : '';
        const errorText = (typeof chc_params !== 'undefined' && chc_params && chc_params.copy_error) || 'Ошибка!';
        
        // Update button state
        button.classList.add('error');
        if (copyIcon) copyIcon.style.display = 'none';
        if (errorIcon) errorIcon.style.display = 'block';
        if (textSpan) textSpan.textContent = errorText;
        
        // Show error tooltip
        if (tooltip) {
            tooltip.textContent = 'Не удалось скопировать';
            tooltip.classList.add('show', 'error');
        }
        
        // Reset after delay
        setTimeout(function() {
            button.classList.remove('error');
            if (copyIcon) copyIcon.style.display = 'block';
            if (errorIcon) errorIcon.style.display = 'none';
            if (textSpan) textSpan.textContent = originalText;
            if (tooltip) {
                tooltip.classList.remove('show', 'error');
            }
        }, 2000);
        
        // Trigger custom event
        triggerEvent('chcb:copy-error', { button: button });
    }
    
    /**
     * Create ripple effect on button click
     */
    function createRippleEffect(button) {
        const ripple = document.createElement('span');
        ripple.className = 'chcb-ripple';
        button.appendChild(ripple);
        
        // Remove ripple after animation
        setTimeout(function() {
            ripple.remove();
        }, 600);
    }
    
    /**
     * Initialize Clipboard.js with enhanced features
     */
    function initializeClipboard() {
        // Check if modern clipboard API is available
        const useModernAPI = navigator.clipboard && window.isSecureContext;
        
        if (useModernAPI) {
            // Use modern Clipboard API
            document.addEventListener('click', function(e) {
                const button = e.target.closest('.chcb-copy-btn');
                if (!button) return;
                
                e.preventDefault();
                
                const targetId = button.getAttribute('data-clipboard-target');
                const target = document.querySelector(targetId);
                const code = target || button.closest('.chcb-code-block').querySelector('code');
                
                if (code) {
                    const text = getCleanCode(code);
                    
                    navigator.clipboard.writeText(text).then(function() {
                        handleCopySuccess(button, text);
                    }).catch(function(err) {
                        // Log error only in debug mode
                        if (typeof console !== 'undefined' && window.CHC_DEBUG) {
                            console.error('Failed to copy:', err);
                        }
                        // Try fallback method
                        fallbackCopyTextToClipboard(text, button);
                    });
                }
            });
        } else if (typeof ClipboardJS !== 'undefined') {
            // Fallback to ClipboardJS library
            const clipboard = new ClipboardJS('.chcb-copy-btn', {
                target: function(trigger) {
                    const targetId = trigger.getAttribute('data-clipboard-target');
                    const target = document.querySelector(targetId);
                    return target || trigger.closest('.chcb-code-block').querySelector('code');
                },
                text: function(trigger) {
                    const targetId = trigger.getAttribute('data-clipboard-target');
                    const target = document.querySelector(targetId);
                    const code = target || trigger.closest('.chcb-code-block').querySelector('code');
                    
                    return code ? getCleanCode(code) : '';
                }
            });
            
            // Handle successful copy
            clipboard.on('success', function(e) {
                handleCopySuccess(e.trigger, e.text);
                e.clearSelection();
            });
            
            // Handle copy error
            clipboard.on('error', function(e) {
                // Try fallback method
                const targetId = e.trigger.getAttribute('data-clipboard-target');
                const target = document.querySelector(targetId);
                const code = target || e.trigger.closest('.chcb-code-block').querySelector('code');
                
                if (code) {
                    const text = getCleanCode(code);
                    fallbackCopyTextToClipboard(text, e.trigger);
                } else {
                    handleCopyError(e.trigger);
                }
            });
        } else {
            // No clipboard support, use fallback for all buttons
            document.addEventListener('click', function(e) {
                const button = e.target.closest('.chcb-copy-btn');
                if (!button) return;
                
                e.preventDefault();
                
                const targetId = button.getAttribute('data-clipboard-target');
                const target = document.querySelector(targetId);
                const code = target || button.closest('.chcb-code-block').querySelector('code');
                
                if (code) {
                    const text = getCleanCode(code);
                    fallbackCopyTextToClipboard(text, button);
                }
            });
        }
        
        // Add keyboard support (Ctrl+C when code is selected)
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
                const selection = window.getSelection();
                if (selection.toString()) {
                    const codeBlock = selection.anchorNode.parentElement.closest('.chcb-code-block');
                    if (codeBlock) {
                        // Show temporary notification
                        const notification = document.createElement('div');
                        notification.className = 'chcb-keyboard-copy-notification';
                        notification.textContent = 'Код скопирован!';
                        codeBlock.appendChild(notification);
                        
                        setTimeout(function() {
                            notification.remove();
                        }, 2000);
                    }
                }
            }
        });
    }
    
    /**
     * Initialize fullscreen functionality
     */
    function initializeFullscreen() {
        // Handle fullscreen button clicks
        document.addEventListener('click', function(e) {
            const button = e.target.closest('.chcb-fullscreen-btn');
            if (!button) return;
            
            e.preventDefault();
            const codeBlock = button.closest('.chcb-code-block');
            
            if (codeBlock) {
                toggleFullscreen(codeBlock);
            }
        });
        
        // Handle ESC key to exit fullscreen
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' || e.key === 'Esc') {
                const fullscreenBlock = document.querySelector('.chcb-code-block.fullscreen');
                if (fullscreenBlock) {
                    exitFullscreen(fullscreenBlock);
                }
            }
        });
    }
    
    /**
     * Toggle fullscreen mode for code block
     */
    function toggleFullscreen(codeBlock) {
        if (codeBlock.classList.contains('fullscreen')) {
            exitFullscreen(codeBlock);
        } else {
            enterFullscreen(codeBlock);
        }
    }
    
    /**
     * Enter fullscreen mode
     */
    function enterFullscreen(codeBlock) {
        codeBlock.classList.add('fullscreen');
        document.body.style.overflow = 'hidden';
        
        // Update button icon/text
        const button = codeBlock.querySelector('.chcb-fullscreen-btn');
        if (button) {
            const textSpan = button.querySelector('.chcb-btn-text');
            if (textSpan) {
                textSpan.textContent = 'Exit';
            }
        }
        
        // Trigger custom event
        triggerEvent('chcb:fullscreen-enter', { codeBlock: codeBlock });
    }
    
    /**
     * Exit fullscreen mode
     */
    function exitFullscreen(codeBlock) {
        codeBlock.classList.remove('fullscreen');
        document.body.style.overflow = '';
        
        // Update button icon/text
        const button = codeBlock.querySelector('.chcb-fullscreen-btn');
        if (button) {
            const textSpan = button.querySelector('.chcb-btn-text');
            if (textSpan) {
                textSpan.textContent = 'Fullscreen';
            }
        }
        
        // Trigger custom event
        triggerEvent('chcb:fullscreen-exit', { codeBlock: codeBlock });
    }
    
    /**
     * Get display name for language
     */
    function getLanguageDisplayName(language) {
        const languageNames = {
            'markup': 'HTML',
            'html': 'HTML',
            'xml': 'XML',
            'svg': 'SVG',
            'mathml': 'MathML',
            'css': 'CSS',
            'clike': 'C-like',
            'javascript': 'JavaScript',
            'js': 'JavaScript',
            'bash': 'Bash',
            'shell': 'Shell',
            'c': 'C',
            'cpp': 'C++',
            'csharp': 'C#',
            'cs': 'C#',
            'java': 'Java',
            'python': 'Python',
            'py': 'Python',
            'php': 'PHP',
            'sql': 'SQL',
            'ruby': 'Ruby',
            'rb': 'Ruby',
            'go': 'Go',
            'rust': 'Rust',
            'rs': 'Rust',
            'swift': 'Swift',
            'kotlin': 'Kotlin',
            'kt': 'Kotlin',
            'yaml': 'YAML',
            'yml': 'YAML',
            'json': 'JSON',
            'typescript': 'TypeScript',
            'ts': 'TypeScript',
            'markdown': 'Markdown',
            'md': 'Markdown',
            'perl': 'Perl',
            'r': 'R',
            'powershell': 'PowerShell',
            'ps1': 'PowerShell',
            'objectivec': 'Objective-C',
            'objc': 'Objective-C',
            'haskell': 'Haskell',
            'hs': 'Haskell',
            'scala': 'Scala',
            'clojure': 'Clojure',
            'clj': 'Clojure',
            'erlang': 'Erlang',
            'erl': 'Erlang',
            'fsharp': 'F#',
            'fs': 'F#',
            'groovy': 'Groovy',
            'latex': 'LaTeX',
            'tex': 'LaTeX',
            'matlab': 'MATLAB',
            'pascal': 'Pascal',
            'diff': 'Diff',
            'arduino': 'Arduino',
            'actionscript': 'ActionScript',
            'as': 'ActionScript',
            'plaintext': 'Plain Text',
            'text': 'Plain Text',
            'none': 'Code'
        };
        
        return languageNames[language.toLowerCase()] || language.toUpperCase();
    }
    
    /**
     * Observe for dynamically added content
     */
    function observeDynamicContent() {
        // Check if MutationObserver is supported
        if (typeof MutationObserver === 'undefined') {
            return;
        }
        
        // Create observer
        const observer = new MutationObserver(function(mutations) {
            let shouldProcess = false;
            
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1 && (
                            node.matches('pre[class*="language-"]') ||
                            node.querySelector('pre[class*="language-"]')
                        )) {
                            shouldProcess = true;
                        }
                    });
                }
            });
            
            if (shouldProcess) {
                // Debounce processing
                clearTimeout(window.chcbProcessTimeout);
                window.chcbProcessTimeout = setTimeout(function() {
                    Prism.highlightAll();
                    processCodeBlocks();
                    
                    // Trigger custom event
                    triggerEvent('chcb:code-added');
                }, 100);
            }
        });
        
        // Start observing
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    /**
     * Handle WordPress block editor preview
     */
    function handleBlockEditorPreview() {
        // Check if we're in the block editor
        if (typeof wp !== 'undefined' && wp.data) {
            wp.data.subscribe(function() {
                // Re-process code blocks in editor
                const editorBlocks = document.querySelectorAll('.block-editor-block-preview__content pre[class*="language-"]');
                if (editorBlocks.length > 0) {
                    setTimeout(function() {
                        Prism.highlightAll();
                        processCodeBlocks();
                    }, 100);
                }
            });
        }
    }
    
    /**
     * Trigger custom event
     */
    function triggerEvent(eventName, detail) {
        const event = new CustomEvent(eventName, {
            detail: detail,
            bubbles: true,
            cancelable: true
        });
        document.dispatchEvent(event);
    }
    
    /**
     * Public API
     */
    window.CHCBHighlighter = {
        /**
         * Manually highlight code blocks
         */
        highlight: function(container) {
            container = container || document;
            
            if (typeof Prism !== 'undefined') {
                Prism.highlightAllUnder(container);
            }
            
            processCodeBlocks();
        },
        
        /**
         * Add code block programmatically
         */
        addCodeBlock: function(code, language, container) {
            language = language || 'plaintext';
            
            const pre = document.createElement('pre');
            pre.className = 'language-' + language;
            
            const codeEl = document.createElement('code');
            codeEl.className = 'language-' + language;
            codeEl.textContent = code;
            
            pre.appendChild(codeEl);
            
            if (container) {
                container.appendChild(pre);
                this.highlight(container);
            }
            
            return pre;
        },
        
        /**
         * Get all code blocks
         */
        getCodeBlocks: function() {
            return document.querySelectorAll('.chcb-code-block');
        },
        
        /**
         * Copy code from specific block
         */
        copyCode: function(blockElement) {
            const btn = blockElement.querySelector('.chcb-copy-btn');
            if (btn) {
                btn.click();
            }
        }
    };
    
    // jQuery support
    if (typeof jQuery !== 'undefined') {
        jQuery.fn.chcbHighlight = function() {
            return this.each(function() {
                window.CHCBHighlighter.highlight(this);
            });
        };
        
        // Listen for custom jQuery events
        jQuery(document).on('chcb_code_added', function() {
            window.CHCBHighlighter.highlight();
        });
    }
    
})();