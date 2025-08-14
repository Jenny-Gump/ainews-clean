# Code Highlighter with Copy Button

Профессиональный WordPress плагин для подсветки синтаксиса кода с функцией копирования в буфер обмена.

## ✨ Основные возможности

### 🎨 Подсветка и темы
- **Подсветка синтаксиса**: Красивая подсветка кода с использованием Prism.js
- **8 тем оформления**: От светлых до темных, включая популярные схемы
- **40+ языков программирования**: Поддержка всех популярных языков

### 📋 Функциональность
- **Кнопка копирования**: Копирование кода одним нажатием с анимацией
- **Полноэкранный режим**: Просмотр кода в полноэкранном режиме
- **Номера строк**: Опциональная нумерация строк
- **Индивидуальные шорткоды**: Уникальный шорткод для каждого языка

### 🛡️ Безопасность и производительность
- **Безопасность**: Следует лучшим практикам безопасности WordPress
- **Производительность**: Оптимизирован для скорости загрузки
- **Адаптивность**: Отлично работает на мобильных устройствах
- **Совместимость**: Протестирован с популярными темами WordPress

## 📦 Установка

1. Загрузите папку `code-highlighter-copy` в `/wp-content/plugins/`
2. Активируйте плагин через меню 'Плагины' в WordPress
3. Настройте параметры в Настройки > Code Highlighter
4. Начните использовать шорткоды в постах и страницах

## 💡 Использование

### Индивидуальные шорткоды для каждого языка

Плагин предоставляет уникальный шорткод для каждого поддерживаемого языка:

```
[php]
<?php
echo "Hello, World!";
?>
[/php]
```

```
[javascript]
function helloWorld() {
    console.log("Hello, World!");
}
helloWorld();
[/javascript]
```

```
[python]
def hello_world():
    print("Hello, World!")

hello_world()
[/python]
```

### Все поддерживаемые шорткоды

**Веб-технологии:**
- `[html]...[/html]` - HTML разметка
- `[css]...[/css]` - CSS стили
- `[javascript]...[/javascript]` - JavaScript код
- `[typescript]...[/typescript]` - TypeScript код
- `[json]...[/json]` - JSON данные
- `[xml]...[/xml]` - XML документы
- `[yaml]...[/yaml]` - YAML конфигурации

**Серверные языки:**
- `[php]...[/php]` - PHP код
- `[python]...[/python]` - Python скрипты
- `[java]...[/java]` - Java приложения
- `[csharp]...[/csharp]` - C# код
- `[ruby]...[/ruby]` - Ruby скрипты
- `[go]...[/go]` - Go программы
- `[rust]...[/rust]` - Rust код
- `[swift]...[/swift]` - Swift приложения
- `[kotlin]...[/kotlin]` - Kotlin код
- `[scala]...[/scala]` - Scala программы

**Системные языки:**
- `[c]...[/c]` - C код
- `[cpp]...[/cpp]` - C++ код
- `[objectivec]...[/objectivec]` - Objective-C
- `[pascal]...[/pascal]` - Pascal код
- `[erlang]...[/erlang]` - Erlang
- `[haskell]...[/haskell]` - Haskell
- `[clojure]...[/clojure]` - Clojure
- `[fsharp]...[/fsharp]` - F# код
- `[groovy]...[/groovy]` - Groovy скрипты

**Базы данных и конфигурации:**
- `[sql]...[/sql]` - SQL запросы
- `[bash]...[/bash]` - Bash скрипты
- `[powershell]...[/powershell]` - PowerShell команды
- `[r]...[/r]` - R статистика
- `[matlab]...[/matlab]` - MATLAB код
- `[latex]...[/latex]` - LaTeX документы
- `[markdown]...[/markdown]` - Markdown текст
- `[diff]...[/diff]` - Diff файлы
- `[actionscript]...[/actionscript]` - ActionScript
- `[arduino]...[/arduino]` - Arduino скетчи
- `[perl]...[/perl]` - Perl скрипты

## Shortcode Parameters

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `language` | Programming language | `plaintext` | See supported languages |
| `title` | Optional title for code block | empty | Any text |
| `line_numbers` | Show line numbers | `true` | `true`, `false` |
| `copy_button` | Show copy button | `true` | `true`, `false` |
| `highlight` | Lines to highlight | empty | e.g., "1,3-5,8" |
| `start` | Starting line number | `1` | Any number |
| `class` | Additional CSS classes | empty | Any valid CSS class |
| `id` | HTML ID attribute | auto-generated | Any valid ID |

## 🔧 Поддерживаемые языки (40+)

### Веб-разработка
- **HTML/XML** - Разметка и структура
- **CSS** - Стили и оформление
- **JavaScript** - Клиентские скрипты
- **TypeScript** - Типизированный JavaScript
- **JSON** - Обмен данными
- **YAML** - Конфигурационные файлы

### Серверная разработка
- **PHP** - Веб-приложения
- **Python** - Универсальный язык
- **Java** - Корпоративные решения
- **C#** - .NET разработка
- **Ruby** - Веб-фреймворки
- **Go** - Высокопроизводительные сервисы
- **Rust** - Системное программирование
- **Swift** - iOS/macOS приложения
- **Kotlin** - Android разработка
- **Scala** - JVM приложения

### Системное программирование
- **C** - Низкоуровневое программирование
- **C++** - Объектно-ориентированное программирование
- **Objective-C** - macOS/iOS (legacy)
- **Pascal** - Образовательное программирование
- **Erlang** - Высоконадежные системы
- **Haskell** - Функциональное программирование
- **Clojure** - Функциональный JVM язык
- **F#** - Функциональный .NET язык
- **Groovy** - JVM скриптинг

### Специализированные языки
- **SQL** - Работа с базами данных
- **Bash** - Системные скрипты
- **PowerShell** - Windows автоматизация
- **R** - Статистический анализ
- **MATLAB** - Научные вычисления
- **LaTeX** - Научная документация
- **Markdown** - Легкая разметка
- **Diff** - Сравнение файлов
- **ActionScript** - Flash разработка
- **Arduino** - Микроконтроллеры
- **Perl** - Обработка текста

## 🎨 Доступные темы оформления

### Светлые темы
1. **Default** - Чистая и минималистичная тема
2. **Coy** - Светлая тема с тенями и элегантностью
3. **Solarized Light** - Популярная светлая тема для глаз

### Темные темы
4. **Tomorrow Night** - Темная тема с яркими акцентами
5. **Okaidia** - Вдохновлена Sublime Text
6. **Twilight** - Мягкая темная тема
7. **Dark** - Простая темная тема
8. **Funky** - Яркая и игривая цветовая схема

### Настройка тем
Вы можете переключать темы в админ-панели WordPress:
- Перейдите в **Настройки** → **Code Highlighter**
- Выберите нужную тему из списка
- Сохраните изменения

## Configuration

### General Settings
- Enable/disable on frontend
- Enable/disable in comments
- Auto-detect language
- Select supported languages

### Appearance Settings
- Choose color theme
- Toggle line numbers
- Configure copy button
- Customize button text
- Show/hide language labels

### Advanced Settings
- Enable caching
- Set cache expiration
- Add custom CSS

## Hooks & Filters

### Actions

```php
// Fired after plugin initialization
do_action('chc_init', $plugin_instance);

// Before rendering code block
do_action('chc_before_render', $code, $language, $attributes);

// After rendering code block
do_action('chc_after_render', $html, $code, $language);
```

### Filters

```php
// Modify supported languages
add_filter('chc_supported_languages', function($languages) {
    $languages['custom'] = 'Custom Language';
    return $languages;
});

// Control asset loading
add_filter('chc_should_load_assets', function($load) {
    // Custom logic
    return $load;
});

// Modify rendered HTML
add_filter('chc_code_html', function($html, $code, $language) {
    // Modify HTML
    return $html;
}, 10, 3);
```

## Security Features

- **Input Sanitization**: All user inputs are properly sanitized
- **Output Escaping**: All outputs are escaped to prevent XSS
- **Nonce Verification**: AJAX requests use WordPress nonces
- **Capability Checks**: User permissions are validated
- **SQL Injection Prevention**: Using prepared statements

## Performance Optimization

- **Lazy Loading**: Assets loaded only when needed
- **Caching System**: Built-in cache for processed code blocks
- **Minified Assets**: Production-ready minified CSS/JS
- **Conditional Loading**: Scripts loaded only on pages with code blocks
- **Database Optimized**: Minimal database queries

## ⚙️ Системные требования

### Минимальные требования
- **WordPress:** 5.0 или выше
- **PHP:** 7.4 или выше
- **MySQL:** 5.6 или выше
- **Браузер:** Современный браузер с поддержкой JavaScript

### Рекомендуемые требования
- **WordPress:** 6.0 или выше
- **PHP:** 8.0 или выше
- **MySQL:** 8.0 или выше
- **HTTPS:** Для корректной работы Clipboard API

### Совместимость браузеров
- **Chrome:** 66+
- **Firefox:** 63+
- **Safari:** 13.1+
- **Edge:** 79+
- **iOS Safari:** 13.4+
- **Chrome Mobile:** 66+

## Troubleshooting

### Code not highlighting
1. Check if JavaScript is enabled
2. Verify language is supported
3. Clear cache (Settings > Code Highlighter > Clear Cache)

### Copy button not working
1. Check browser compatibility
2. Ensure Clipboard API is available
3. Test in different browser

### Styles not loading
1. Check for theme conflicts
2. Verify plugin is activated
3. Clear browser cache

## Developer API

### PHP Functions

```php
// Check if highlighting is enabled
if (chc_is_enabled()) {
    // Code highlighting is active
}

// Get plugin option
$theme = chc_get_option('theme', 'prism-tomorrow');

// Detect language from file
$language = chc_detect_language_from_file('example.py'); // Returns 'python'

// Get code blocks from post
$blocks = chc_get_code_blocks($post_id, 'javascript');
```

### JavaScript API

```javascript
// Manually highlight code
Prism.highlightAll();

// Copy code programmatically
CHC.copyCode(elementId);

// Get all code blocks
const blocks = document.querySelectorAll('.chc-code-wrapper');
```

## Changelog

### Version 1.0.0
- Initial release
- Core highlighting functionality
- Copy button feature
- 8 themes included
- 20+ language support
- Admin settings panel
- Shortcode support
- Caching system
- Security hardening

## Support

For support, feature requests, or bug reports, please visit:
- Website: https://ailynx.ru
- Email: support@ailynx.ru

## License

GPL v2 or later

## Credits

- [Prism.js](https://prismjs.com/) - Syntax highlighting library
- [Clipboard.js](https://clipboardjs.com/) - Copy to clipboard library
- WordPress Community

## Contributing

Contributions are welcome! Please follow WordPress Coding Standards and include proper documentation for any changes.

---

Made with care by AI News Team