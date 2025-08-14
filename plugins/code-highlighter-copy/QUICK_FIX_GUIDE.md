# Руководство по быстрому исправлению уязвимостей

## 🚨 Критические исправления (выполнить немедленно)

### 1. Замените файл admin/class-admin.php

**Вариант А: Использовать безопасную версию**
```bash
# Сделайте резервную копию
cp admin/class-admin.php admin/class-admin.backup.php

# Замените на безопасную версию
cp admin/class-admin-secure.php admin/class-admin.php
```

**Вариант Б: Внести минимальные изменения вручную**

#### Исправление 1: Санитизация в ajax_save_settings (строка 563)

Замените:
```php
// Process and save settings
$settings = isset($_POST['settings']) ? $_POST['settings'] : array();

foreach ($settings as $key => $value) {
    update_option($key, $value);
}
```

На:
```php
// Process and save settings with sanitization
$settings = isset($_POST['settings']) ? $_POST['settings'] : array();
$allowed_keys = array('theme', 'line_numbers', 'copy_button', 'copy_button_text', 
                      'copied_text', 'supported_languages', 'auto_detect_language');

foreach ($settings as $key => $value) {
    $key = sanitize_key($key);
    
    // Only allow whitelisted settings
    if (!in_array(str_replace('chc_', '', $key), $allowed_keys)) {
        continue;
    }
    
    // Sanitize based on type
    if (in_array($key, array('chc_line_numbers', 'chc_copy_button', 'chc_auto_detect_language'))) {
        $value = (bool) $value;
    } elseif (is_array($value)) {
        $value = array_map('sanitize_text_field', $value);
    } else {
        $value = sanitize_text_field($value);
    }
    
    update_option($key, $value);
}
```

#### Исправление 2: Защита импорта файлов (строка 639)

Добавьте после строки 639:
```php
public function import_settings() {
    // Добавить проверку nonce
    check_admin_referer('chc_import_nonce', 'import_nonce');
    
    if (!current_user_can('manage_options')) {
        wp_die(__('Insufficient permissions.', 'code-highlighter-copy'));
    }
    
    if (empty($_FILES['import_file']['tmp_name'])) {
        wp_redirect(add_query_arg('error', 'no_file', wp_get_referer()));
        exit;
    }
    
    // ДОБАВИТЬ: Проверка типа файла
    $file_type = wp_check_filetype($_FILES['import_file']['name']);
    if ($file_type['ext'] !== 'json') {
        wp_redirect(add_query_arg('error', 'invalid_type', wp_get_referer()));
        exit;
    }
    
    // ДОБАВИТЬ: Ограничение размера (1MB)
    if ($_FILES['import_file']['size'] > 1048576) {
        wp_redirect(add_query_arg('error', 'file_too_large', wp_get_referer()));
        exit;
    }
    
    $file_content = file_get_contents($_FILES['import_file']['tmp_name']);
    $import_data = json_decode($file_content, true);
    
    // ДОБАВИТЬ: Проверка JSON
    if (json_last_error() !== JSON_ERROR_NONE) {
        wp_redirect(add_query_arg('error', 'invalid_json', wp_get_referer()));
        exit;
    }
    
    // Остальной код...
```

#### Исправление 3: Добавить nonce в формы экспорта/импорта

В файле `admin/views/settings-page.php` найдите форму импорта и добавьте:
```php
<form method="post" action="<?php echo admin_url('admin-post.php'); ?>" enctype="multipart/form-data">
    <?php wp_nonce_field('chc_import_nonce', 'import_nonce'); ?>
    <input type="hidden" name="action" value="chc_import_settings">
    <!-- остальные поля формы -->
</form>
```

Для экспорта:
```php
<form method="post" action="<?php echo admin_url('admin-post.php'); ?>">
    <?php wp_nonce_field('chc_export_nonce', 'export_nonce'); ?>
    <input type="hidden" name="action" value="chc_export_settings">
    <!-- кнопка экспорта -->
</form>
```

### 2. Исправьте XSS уязвимости в includes/class-shortcodes.php

#### Строка 574 - Экранирование title
Замените:
```php
$html .= '<div class="chcb-title">' . $title . '</div>';
```

На:
```php
$html .= '<div class="chcb-title">' . esc_html($title) . '</div>';
```

#### Строка 706 - Экранирование content
Замените:
```php
if ($escape) {
    $content = esc_html($content);
}
```

На:
```php
// Всегда экранировать для безопасности
$content = esc_html($content);
```

### 3. Добавьте Rate Limiting

Создайте новый файл `includes/class-security.php`:
```php
<?php
/**
 * Security Helper Class
 */
class CHC_Security {
    
    /**
     * Check rate limiting
     */
    public static function check_rate_limit($action, $limit = 10, $window = 60) {
        $user_id = get_current_user_id();
        $ip = $_SERVER['REMOTE_ADDR'] ?? '';
        $key = 'chc_rate_' . md5($action . $user_id . $ip);
        
        $attempts = get_transient($key);
        
        if ($attempts === false) {
            set_transient($key, 1, $window);
            return true;
        }
        
        if ($attempts >= $limit) {
            return false;
        }
        
        set_transient($key, $attempts + 1, $window);
        return true;
    }
    
    /**
     * Sanitize hex color
     */
    public static function sanitize_hex_color($color) {
        if (preg_match('|^#([A-Fa-f0-9]{3}){1,2}$|', $color)) {
            return $color;
        }
        return '';
    }
    
    /**
     * Validate language
     */
    public static function validate_language($language) {
        $allowed = array(
            'php', 'javascript', 'python', 'html', 'css', 'sql',
            'bash', 'java', 'cpp', 'csharp', 'ruby', 'go', 'rust'
        );
        return in_array($language, $allowed) ? $language : 'plaintext';
    }
}
```

Подключите в главном файле:
```php
require_once CHC_PLUGIN_DIR . 'includes/class-security.php';
```

## ⚡ Экспресс-проверка после исправлений

### Тест 1: Проверка санитизации
```php
// В консоли браузера на странице настроек плагина
jQuery.post(ajaxurl, {
    action: 'chc_save_settings',
    nonce: chc_admin.nonce,
    settings: {
        'chc_theme': '<script>alert("XSS")</script>'
    }
});
// Не должно выполнить скрипт
```

### Тест 2: Проверка импорта
1. Создайте файл test.txt (не JSON)
2. Попробуйте импортировать
3. Должна появиться ошибка "Invalid file type"

### Тест 3: Проверка rate limiting
```javascript
// Быстрые множественные запросы
for(let i = 0; i < 15; i++) {
    jQuery.post(ajaxurl, {
        action: 'chc_save_settings',
        nonce: chc_admin.nonce,
        settings: {}
    });
}
// После 10 запросов должна появиться ошибка
```

## 📋 Чек-лист проверки

- [ ] Заменен файл admin/class-admin.php
- [ ] Добавлена санитизация в AJAX обработчики
- [ ] Добавлены nonce проверки в формы
- [ ] Исправлено экранирование в шорткодах
- [ ] Добавлен класс безопасности
- [ ] Проведены тесты безопасности
- [ ] Проверена работоспособность основных функций

## 🔄 Обновление на продакшене

1. **Сделайте полный бэкап**
```bash
wp plugin deactivate code-highlighter-copy
cp -r wp-content/plugins/code-highlighter-copy wp-content/plugins/code-highlighter-copy.backup
```

2. **Примените исправления**
```bash
# Скопируйте исправленные файлы
```

3. **Протестируйте**
```bash
wp plugin activate code-highlighter-copy
```

4. **Проверьте логи**
```bash
tail -f wp-content/debug.log
```

## ⚠️ Важные замечания

1. **НЕ используйте плагин в продакшене** до применения ВСЕХ критических исправлений
2. После исправлений обязательно протестируйте все функции
3. Включите логирование для отслеживания подозрительной активности
4. Рассмотрите использование WAF (например, Wordfence или Sucuri)

## 📞 Поддержка

Если возникли проблемы с исправлениями:
1. Откатитесь на резервную копию
2. Обратитесь к разработчику WordPress
3. Используйте альтернативный плагин подсветки кода до исправления

---

**Время на исправление:** ~30 минут
**Приоритет:** КРИТИЧЕСКИЙ
**Статус:** Требует немедленных действий