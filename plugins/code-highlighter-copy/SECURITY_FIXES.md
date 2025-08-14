# Security Fixes Documentation

## Version 1.1.0 - Security Hardening Update

This document details all security vulnerabilities that have been identified and fixed in the Code Highlighter Copy plugin.

## Critical Security Fixes Implemented

### 1. AJAX Request Security

#### Fixed Vulnerabilities:
- **Missing nonce verification in some AJAX handlers**
- **No rate limiting on AJAX requests**
- **Insufficient permission checks**
- **Missing input sanitization**

#### Implementations:
```php
// Before (VULNERABLE)
public function ajax_save_settings() {
    $settings = $_POST['settings'];
    foreach ($settings as $key => $value) {
        update_option($key, $value);
    }
}

// After (SECURE)
public function ajax_save_settings() {
    // Verify nonce
    if (!check_ajax_referer('chc_admin_nonce', 'nonce', false)) {
        wp_send_json_error(__('Security check failed.', 'code-highlighter-copy'), 403);
    }
    
    // Check permissions
    if (!current_user_can('manage_options')) {
        wp_send_json_error(__('Insufficient permissions.', 'code-highlighter-copy'), 403);
    }
    
    // Rate limiting
    $user_id = get_current_user_id();
    $transient_key = 'chc_ajax_limit_' . $user_id;
    $requests = get_transient($transient_key) ?: 0;
    
    if ($requests > 10) { // Max 10 requests per minute
        wp_send_json_error(__('Too many requests.', 'code-highlighter-copy'), 429);
    }
    
    set_transient($transient_key, $requests + 1, 60);
    
    // Sanitize and validate with whitelist
    $allowed_settings = $this->get_allowed_settings_keys();
    foreach ($settings as $key => $value) {
        $sanitized_key = sanitize_key($key);
        if (in_array($sanitized_key, $allowed_settings, true)) {
            $sanitized_value = $this->sanitize_setting_value($sanitized_key, $value);
            update_option($sanitized_key, $sanitized_value);
        }
    }
}
```

### 2. File Import/Export Security

#### Fixed Vulnerabilities:
- **No file type validation**
- **No file size limits**
- **Missing MIME type checking**
- **No JSON structure validation**
- **Missing nonce protection**

#### Implementations:
```php
// File type validation
$file_type = wp_check_filetype($uploaded_file['name']);
if ($file_type['ext'] !== 'json') {
    wp_redirect(add_query_arg('error', 'invalid_type', wp_get_referer()));
    exit;
}

// MIME type validation
$finfo = finfo_open(FILEINFO_MIME_TYPE);
$mime_type = finfo_file($finfo, $uploaded_file['tmp_name']);
finfo_close($finfo);

if (!in_array($mime_type, array('application/json', 'text/plain'), true)) {
    wp_redirect(add_query_arg('error', 'invalid_mime', wp_get_referer()));
    exit;
}

// File size limit (1MB max)
if ($uploaded_file['size'] > 1048576) {
    wp_redirect(add_query_arg('error', 'file_too_large', wp_get_referer()));
    exit;
}

// JSON structure validation
$import_data = json_decode($file_content, true);
if (json_last_error() !== JSON_ERROR_NONE) {
    wp_redirect(add_query_arg('error', 'invalid_json', wp_get_referer()));
    exit;
}
```

### 3. Input Sanitization

#### Fixed Vulnerabilities:
- **Direct use of $_POST data without sanitization**
- **Missing validation for setting types**
- **No constraints on numeric inputs**
- **Unfiltered CSS input**

#### Implementations:
```php
// Comprehensive sanitization method
private function sanitize_setting_value($key, $value) {
    // Boolean settings
    if (in_array($key, $boolean_settings, true)) {
        return (bool) $value;
    }
    
    // Integer settings with constraints
    elseif (in_array($key, $integer_settings, true)) {
        $int_value = absint($value);
        
        if ($key === 'chc_font_size') {
            return max(8, min(32, $int_value)); // 8-32px
        } elseif ($key === 'chc_max_height') {
            return min(2000, $int_value); // Max 2000px
        }
    }
    
    // Select fields with whitelist validation
    elseif (isset($select_settings[$key])) {
        if (isset($select_settings[$key][$value])) {
            return sanitize_text_field($value);
        }
        return array_key_first($select_settings[$key]); // Default
    }
    
    // CSS sanitization
    elseif ($key === 'chc_custom_css') {
        $value = strip_tags($value);
        $value = preg_replace('#javascript:#i', '', $value);
        $value = preg_replace('#expression\s*\(#i', '', $value);
        $value = preg_replace('#@import#i', '', $value);
        return sanitize_textarea_field($value);
    }
}
```

### 4. Output Escaping

#### Fixed Vulnerabilities:
- **Unescaped output in admin templates**
- **Missing esc_html() in dynamic content**
- **Unescaped attributes**
- **JavaScript injection possibilities**

#### Implementations:
```php
// Always escape output
echo esc_html($variable);
echo esc_attr($attribute);
echo esc_url($url);
echo esc_js($javascript);
echo wp_kses_post($html_content);

// JavaScript escaping improvements
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
    return String(text || '').replace(/[&<>"'`=\/]/g, m => map[m]);
}
```

### 5. SQL Injection Prevention

#### Fixed Vulnerabilities:
- **Direct SQL queries without preparation**
- **Unescaped LIKE queries**
- **Dynamic table/column names**

#### Implementations:
```php
// Always use prepared statements
$wpdb->prepare(
    "DELETE FROM {$wpdb->options} WHERE option_name LIKE %s",
    '_transient_chc_%'
);

// Escape LIKE wildcards
$search_term = $wpdb->esc_like($user_input) . '%';
```

### 6. Rate Limiting

#### Implementation Details:
- **AJAX requests**: 10 per minute
- **Settings reset**: 3 per hour
- **Cache clear**: 5 per hour
- **Database optimization**: 1 per hour
- **Export operations**: 10 per hour
- **Import operations**: 5 per hour

```php
// Rate limiting implementation
$user_id = get_current_user_id();
$transient_key = 'chc_action_limit_' . $user_id;
$requests = get_transient($transient_key) ?: 0;

if ($requests > $limit) {
    wp_send_json_error(__('Too many requests.', 'code-highlighter-copy'), 429);
}

set_transient($transient_key, $requests + 1, $timeout);
```

### 7. Settings Whitelist

#### Implementation:
All settings are now validated against a whitelist to prevent unauthorized option updates:

```php
private function get_allowed_settings_keys() {
    return array(
        'chc_enable_on_frontend',
        'chc_enable_in_comments',
        'chc_auto_detect_language',
        'chc_theme',
        'chc_line_numbers',
        'chc_copy_button',
        // ... etc
    );
}
```

## Security Best Practices Implemented

### 1. Defense in Depth
- Multiple layers of security checks
- Fail-safe defaults
- Principle of least privilege

### 2. Input Validation
- Whitelist approach for all inputs
- Type checking and constraints
- Size limitations

### 3. Output Encoding
- Context-aware escaping
- Prevention of XSS attacks
- Safe HTML rendering

### 4. Authentication & Authorization
- Nonce verification on all forms
- Capability checks for all operations
- User session validation

### 5. Error Handling
- Secure error messages (no sensitive data leakage)
- Proper HTTP status codes
- Logging of suspicious activity

## Testing

### Running Security Tests
```bash
# Navigate to plugin directory
cd /path/to/wp-content/plugins/code-highlighter-copy

# Run security tests
php tests/test-security.php
```

### Test Coverage
- Nonce verification
- Capability checks
- Input sanitization
- Output escaping
- File upload validation
- SQL injection prevention
- XSS prevention
- CSRF protection
- Rate limiting
- Settings validation

## Recommendations for Deployment

1. **Clear all caches** after updating to ensure new security measures are active
2. **Review user permissions** to ensure only trusted users have admin access
3. **Enable WordPress debugging** temporarily to catch any issues:
   ```php
   define('WP_DEBUG', true);
   define('WP_DEBUG_LOG', true);
   define('WP_DEBUG_DISPLAY', false);
   ```
4. **Monitor error logs** for the first 24-48 hours after deployment
5. **Test all functionality** thoroughly, especially:
   - Settings save/load
   - Import/export
   - Cache operations
   - Database optimization

## Security Headers (Recommended)

Add these to your `.htaccess` file for additional security:

```apache
# Security Headers
Header set X-Content-Type-Options "nosniff"
Header set X-Frame-Options "SAMEORIGIN"
Header set X-XSS-Protection "1; mode=block"
Header set Referrer-Policy "strict-origin-when-cross-origin"
```

## Changelog

### Version 1.1.0 (Current)
- Added comprehensive input sanitization
- Implemented rate limiting on all AJAX endpoints
- Added file upload validation for import/export
- Enhanced nonce verification
- Added settings whitelist validation
- Improved output escaping
- Added SQL injection prevention measures
- Implemented proper error handling
- Added security test suite

## Security Contact

If you discover any security vulnerabilities, please report them responsibly to:
- Email: security@yourplugin.com
- Do not disclose publicly until a fix is available

## Additional Resources

- [WordPress Security Best Practices](https://developer.wordpress.org/plugins/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [WordPress Coding Standards](https://developer.wordpress.org/coding-standards/wordpress-coding-standards/)

---

**Last Updated**: <?php echo date('Y-m-d'); ?>
**Security Audit Completed**: Yes
**Ready for Production**: Yes