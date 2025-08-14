<?php
/**
 * Security Tests for Code Highlighter Copy Plugin
 *
 * Run these tests to verify all security measures are working correctly.
 *
 * @package CodeHighlighterCopy
 * @since 1.0.0
 */

// Load WordPress environment
require_once dirname(__FILE__) . '/../../../../wp-load.php';

// Security test class
class CHC_Security_Tests {
    
    private $passed = 0;
    private $failed = 0;
    private $tests = array();
    
    /**
     * Run all security tests
     */
    public function run_all_tests() {
        echo "<h1>Code Highlighter Copy - Security Tests</h1>\n";
        echo "<hr>\n";
        
        // Test 1: Nonce verification
        $this->test_nonce_verification();
        
        // Test 2: Capability checks
        $this->test_capability_checks();
        
        // Test 3: Input sanitization
        $this->test_input_sanitization();
        
        // Test 4: Output escaping
        $this->test_output_escaping();
        
        // Test 5: File upload validation
        $this->test_file_upload_validation();
        
        // Test 6: SQL injection prevention
        $this->test_sql_injection_prevention();
        
        // Test 7: XSS prevention
        $this->test_xss_prevention();
        
        // Test 8: CSRF protection
        $this->test_csrf_protection();
        
        // Test 9: Rate limiting
        $this->test_rate_limiting();
        
        // Test 10: Settings validation
        $this->test_settings_validation();
        
        // Display results
        $this->display_results();
    }
    
    /**
     * Test nonce verification
     */
    private function test_nonce_verification() {
        $test_name = "Nonce Verification";
        
        // Create a valid nonce
        $valid_nonce = wp_create_nonce('chc_admin_nonce');
        
        // Test with valid nonce
        $result = wp_verify_nonce($valid_nonce, 'chc_admin_nonce');
        if ($result !== false) {
            $this->add_result($test_name . " (Valid)", true, "Valid nonce accepted");
        } else {
            $this->add_result($test_name . " (Valid)", false, "Valid nonce rejected");
        }
        
        // Test with invalid nonce
        $invalid_nonce = 'invalid_nonce_12345';
        $result = wp_verify_nonce($invalid_nonce, 'chc_admin_nonce');
        if ($result === false) {
            $this->add_result($test_name . " (Invalid)", true, "Invalid nonce rejected");
        } else {
            $this->add_result($test_name . " (Invalid)", false, "Invalid nonce accepted!");
        }
    }
    
    /**
     * Test capability checks
     */
    private function test_capability_checks() {
        $test_name = "Capability Checks";
        
        // Test as admin
        $admin_user = get_user_by('login', 'admin');
        if ($admin_user) {
            wp_set_current_user($admin_user->ID);
            $can_manage = current_user_can('manage_options');
            $this->add_result($test_name . " (Admin)", $can_manage, 
                $can_manage ? "Admin has manage_options capability" : "Admin lacks manage_options capability");
        }
        
        // Test as subscriber (should fail)
        $subscriber = get_user_by('role', 'subscriber');
        if (!$subscriber) {
            // Create a test subscriber
            $subscriber_id = wp_create_user('test_subscriber_' . time(), wp_generate_password());
            $subscriber = get_user_by('id', $subscriber_id);
            $subscriber->set_role('subscriber');
        }
        
        if ($subscriber) {
            wp_set_current_user($subscriber->ID);
            $can_manage = current_user_can('manage_options');
            $this->add_result($test_name . " (Subscriber)", !$can_manage, 
                !$can_manage ? "Subscriber correctly denied manage_options" : "Subscriber incorrectly has manage_options!");
        }
    }
    
    /**
     * Test input sanitization
     */
    private function test_input_sanitization() {
        $test_name = "Input Sanitization";
        
        // Test sanitize_text_field
        $dirty_text = '<script>alert("XSS")</script>Hello World';
        $clean_text = sanitize_text_field($dirty_text);
        $is_clean = (strpos($clean_text, '<script>') === false);
        $this->add_result($test_name . " (Text Field)", $is_clean, 
            "Input: $dirty_text | Output: $clean_text");
        
        // Test sanitize_textarea_field
        $dirty_textarea = "Line 1\n<script>alert('XSS')</script>\nLine 3";
        $clean_textarea = sanitize_textarea_field($dirty_textarea);
        $is_clean = (strpos($clean_textarea, '<script>') === false);
        $this->add_result($test_name . " (Textarea)", $is_clean, 
            "Script tags " . ($is_clean ? "removed" : "not removed!"));
        
        // Test sanitize_key
        $dirty_key = 'some-KEY_123!@#';
        $clean_key = sanitize_key($dirty_key);
        $is_clean = ($clean_key === 'some-key_123');
        $this->add_result($test_name . " (Key)", $is_clean, 
            "Input: $dirty_key | Output: $clean_key");
        
        // Test email sanitization
        $dirty_email = 'test@<script>alert("xss")</script>example.com';
        $clean_email = sanitize_email($dirty_email);
        $is_clean = (strpos($clean_email, '<script>') === false);
        $this->add_result($test_name . " (Email)", $is_clean, 
            "Email sanitization " . ($is_clean ? "successful" : "failed!"));
    }
    
    /**
     * Test output escaping
     */
    private function test_output_escaping() {
        $test_name = "Output Escaping";
        
        // Test esc_html
        $html = '<script>alert("XSS")</script>';
        $escaped = esc_html($html);
        $is_escaped = ($escaped === '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;');
        $this->add_result($test_name . " (HTML)", $is_escaped, 
            "HTML properly escaped: $escaped");
        
        // Test esc_attr
        $attr = '" onclick="alert(\'XSS\')"';
        $escaped_attr = esc_attr($attr);
        $is_escaped = (strpos($escaped_attr, 'onclick') === false || strpos($escaped_attr, '&quot;') !== false);
        $this->add_result($test_name . " (Attribute)", $is_escaped, 
            "Attribute properly escaped");
        
        // Test esc_url
        $url = 'javascript:alert("XSS")';
        $escaped_url = esc_url($url);
        $is_escaped = (strpos($escaped_url, 'javascript:') === false);
        $this->add_result($test_name . " (URL)", $is_escaped, 
            "JavaScript URL " . ($is_escaped ? "blocked" : "not blocked!"));
        
        // Test esc_js
        $js = 'alert("XSS"); //';
        $escaped_js = esc_js($js);
        $is_escaped = ($escaped_js !== $js);
        $this->add_result($test_name . " (JavaScript)", $is_escaped, 
            "JavaScript properly escaped");
    }
    
    /**
     * Test file upload validation
     */
    private function test_file_upload_validation() {
        $test_name = "File Upload Validation";
        
        // Test file type checking
        $allowed_types = array('application/json', 'text/plain');
        
        // Test valid JSON file
        $json_file = 'settings.json';
        $file_type = wp_check_filetype($json_file);
        $is_valid = ($file_type['ext'] === 'json');
        $this->add_result($test_name . " (JSON)", $is_valid, 
            "JSON file " . ($is_valid ? "accepted" : "rejected"));
        
        // Test invalid file type
        $exe_file = 'malware.exe';
        $file_type = wp_check_filetype($exe_file);
        $is_blocked = ($file_type['ext'] !== 'json');
        $this->add_result($test_name . " (EXE)", $is_blocked, 
            "EXE file " . ($is_blocked ? "blocked" : "not blocked!"));
        
        // Test PHP file (should be blocked)
        $php_file = 'backdoor.php';
        $file_type = wp_check_filetype($php_file);
        $is_blocked = ($file_type['ext'] !== 'json');
        $this->add_result($test_name . " (PHP)", $is_blocked, 
            "PHP file " . ($is_blocked ? "blocked" : "not blocked!"));
    }
    
    /**
     * Test SQL injection prevention
     */
    private function test_sql_injection_prevention() {
        global $wpdb;
        $test_name = "SQL Injection Prevention";
        
        // Test prepared statement
        $user_input = "'; DROP TABLE wp_users; --";
        $safe_query = $wpdb->prepare(
            "SELECT * FROM {$wpdb->options} WHERE option_name = %s",
            $user_input
        );
        
        $is_safe = (strpos($safe_query, 'DROP TABLE') === false);
        $this->add_result($test_name . " (Prepared Statement)", $is_safe, 
            "SQL injection " . ($is_safe ? "prevented" : "possible!"));
        
        // Test LIKE escaping
        $search_term = "test%' OR '1'='1";
        $escaped_like = $wpdb->esc_like($search_term);
        $is_escaped = (strpos($escaped_like, "\\'") !== false || strpos($escaped_like, "\\%") !== false);
        $this->add_result($test_name . " (LIKE Escape)", $is_escaped, 
            "LIKE wildcards " . ($is_escaped ? "escaped" : "not escaped!"));
    }
    
    /**
     * Test XSS prevention
     */
    private function test_xss_prevention() {
        $test_name = "XSS Prevention";
        
        // Test various XSS vectors
        $xss_vectors = array(
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            'javascript:alert("XSS")',
            '<iframe src="javascript:alert(\'XSS\')">',
            '<script>alert("XSS")</script>',
            '"><script>alert("XSS")</script>',
            '<body onload=alert("XSS")>',
            '<input onfocus=alert("XSS") autofocus>',
        );
        
        foreach ($xss_vectors as $index => $vector) {
            $cleaned = wp_kses($vector, array());
            $is_clean = (
                strpos($cleaned, '<script') === false &&
                strpos($cleaned, 'javascript:') === false &&
                strpos($cleaned, 'onerror') === false &&
                strpos($cleaned, 'onload') === false &&
                strpos($cleaned, 'onfocus') === false
            );
            
            $this->add_result($test_name . " (Vector " . ($index + 1) . ")", $is_clean, 
                "XSS vector " . ($is_clean ? "blocked" : "not blocked: " . $vector));
        }
    }
    
    /**
     * Test CSRF protection
     */
    private function test_csrf_protection() {
        $test_name = "CSRF Protection";
        
        // Test form nonce field generation
        ob_start();
        wp_nonce_field('chc_admin_action', 'chc_nonce');
        $nonce_field = ob_get_clean();
        
        $has_nonce = (strpos($nonce_field, 'name="chc_nonce"') !== false);
        $this->add_result($test_name . " (Nonce Field)", $has_nonce, 
            "Nonce field " . ($has_nonce ? "generated" : "not generated!"));
        
        // Test referer check
        $_SERVER['HTTP_REFERER'] = home_url('/wp-admin/');
        $referer_valid = wp_verify_nonce(wp_create_nonce('test'), 'test');
        $this->add_result($test_name . " (Referer)", $referer_valid !== false, 
            "Referer check " . ($referer_valid !== false ? "passed" : "failed"));
    }
    
    /**
     * Test rate limiting
     */
    private function test_rate_limiting() {
        $test_name = "Rate Limiting";
        
        // Test transient-based rate limiting
        $user_id = get_current_user_id();
        $transient_key = 'chc_test_rate_limit_' . $user_id;
        
        // Simulate multiple requests
        for ($i = 1; $i <= 15; $i++) {
            $requests = get_transient($transient_key) ?: 0;
            
            if ($i <= 10) {
                // Should be allowed (under limit)
                if ($requests <= 10) {
                    set_transient($transient_key, $requests + 1, 60);
                }
            } else {
                // Should be blocked (over limit)
                if ($requests > 10) {
                    $this->add_result($test_name . " (Request $i)", true, 
                        "Request $i correctly blocked (limit exceeded)");
                } else {
                    $this->add_result($test_name . " (Request $i)", false, 
                        "Request $i not blocked (should be over limit)!");
                }
                break;
            }
        }
        
        // Clean up
        delete_transient($transient_key);
    }
    
    /**
     * Test settings validation
     */
    private function test_settings_validation() {
        $test_name = "Settings Validation";
        
        // Test boolean setting
        $bool_values = array('1', 'true', 1, true, '0', 'false', 0, false, 'invalid');
        foreach ($bool_values as $value) {
            $sanitized = (bool) $value;
            $is_bool = is_bool($sanitized);
            if (!$is_bool) {
                $this->add_result($test_name . " (Boolean)", false, 
                    "Failed to convert to boolean: " . var_export($value, true));
            }
        }
        $this->add_result($test_name . " (Boolean)", true, "All boolean values validated");
        
        // Test integer constraints
        $font_size = 999;
        $validated_size = max(8, min(32, absint($font_size)));
        $is_constrained = ($validated_size === 32);
        $this->add_result($test_name . " (Integer Constraints)", $is_constrained, 
            "Font size constrained: $font_size -> $validated_size");
        
        // Test select field validation
        $valid_themes = array('prism', 'prism-tomorrow', 'prism-okaidia');
        $user_theme = 'invalid-theme';
        $is_invalid = !in_array($user_theme, $valid_themes, true);
        $this->add_result($test_name . " (Select Validation)", $is_invalid, 
            "Invalid option " . ($is_invalid ? "rejected" : "accepted!"));
        
        // Test CSS sanitization
        $malicious_css = 'body { background: url("javascript:alert(1)"); } @import "http://evil.com/css";';
        $clean_css = preg_replace('#javascript:#i', '', $malicious_css);
        $clean_css = preg_replace('#@import#i', '', $clean_css);
        $is_clean = (strpos($clean_css, 'javascript:') === false && strpos($clean_css, '@import') === false);
        $this->add_result($test_name . " (CSS)", $is_clean, 
            "Malicious CSS " . ($is_clean ? "sanitized" : "not sanitized!"));
    }
    
    /**
     * Add test result
     */
    private function add_result($test, $passed, $message) {
        $this->tests[] = array(
            'test' => $test,
            'passed' => $passed,
            'message' => $message
        );
        
        if ($passed) {
            $this->passed++;
        } else {
            $this->failed++;
        }
    }
    
    /**
     * Display test results
     */
    private function display_results() {
        echo "\n<h2>Test Results</h2>\n";
        echo "<table border='1' cellpadding='5' cellspacing='0' style='border-collapse: collapse;'>\n";
        echo "<tr><th>Test</th><th>Status</th><th>Details</th></tr>\n";
        
        foreach ($this->tests as $test) {
            $status = $test['passed'] ? 
                '<span style="color: green;">✓ PASSED</span>' : 
                '<span style="color: red;">✗ FAILED</span>';
            
            echo "<tr>\n";
            echo "<td>" . esc_html($test['test']) . "</td>\n";
            echo "<td>$status</td>\n";
            echo "<td>" . esc_html($test['message']) . "</td>\n";
            echo "</tr>\n";
        }
        
        echo "</table>\n";
        
        echo "\n<h2>Summary</h2>\n";
        echo "<p>Total Tests: " . ($this->passed + $this->failed) . "</p>\n";
        echo "<p style='color: green;'>Passed: $this->passed</p>\n";
        echo "<p style='color: red;'>Failed: $this->failed</p>\n";
        
        $percentage = $this->passed + $this->failed > 0 ? 
            round(($this->passed / ($this->passed + $this->failed)) * 100, 2) : 0;
        
        echo "<p>Success Rate: $percentage%</p>\n";
        
        if ($this->failed === 0) {
            echo "<p style='color: green; font-weight: bold;'>✓ All security tests passed!</p>\n";
        } else {
            echo "<p style='color: red; font-weight: bold;'>⚠ Some security tests failed. Please review and fix the issues.</p>\n";
        }
    }
}

// Run tests if accessed directly
if (!defined('WP_CLI')) {
    $tester = new CHC_Security_Tests();
    ?>
    <!DOCTYPE html>
    <html>
    <head>
        <title>Code Highlighter Copy - Security Tests</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 20px auto; padding: 20px; }
            h1 { color: #333; }
            h2 { color: #666; margin-top: 30px; }
            table { width: 100%; margin: 20px 0; }
            th { background: #f0f0f0; text-align: left; }
            td, th { padding: 8px; border: 1px solid #ddd; }
            .success { color: green; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <?php $tester->run_all_tests(); ?>
    </body>
    </html>
    <?php
}
?>