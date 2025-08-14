# Устранение проблем - Code Highlighter Copy

Этот документ поможет вам решить наиболее распространенные проблемы при использовании плагина Code Highlighter Copy.

## 📚 Содержание

1. [Проблемы с подсветкой синтаксиса](#проблемы-с-подсветкой-синтаксиса)
2. [Проблемы с кнопкой копирования](#проблемы-с-кнопкой-копирования)  
3. [Проблемы с полноэкранным режимом](#проблемы-с-полноэкранным-режимом)
4. [Проблемы совместимости с темами](#проблемы-совместимости-с-темами)
5. [Проблемы производительности](#проблемы-производительности)
6. [Проблемы на мобильных устройствах](#проблемы-на-мобильных-устройствах)
7. [Проблемы с браузерами](#проблемы-с-браузерами)
8. [Проблемы настроек плагина](#проблемы-настроек-плагина)
9. [Диагностика и отладка](#диагностика-и-отладка)

---

## Проблемы с подсветкой синтаксиса

### ❌ Код не подсвечивается

**Возможные причины и решения:**

#### 1. Неправильное имя шорткода
```
❌ Неправильно:
[code language="php"]<?php echo "Hello"; ?>[/code]

✅ Правильно:  
[php]<?php echo "Hello"; ?>[/php]
```

#### 2. JavaScript отключен или не загружается
**Проверьте:**
- Включен ли JavaScript в браузере
- Загружаются ли файлы Prism.js в консоли разработчика (F12)
- Нет ли ошибок JavaScript на странице

**Решение:**
```javascript
// Проверить в консоли браузера:
console.log('Prism объект:', typeof Prism);
console.log('Prism языки:', Object.keys(Prism.languages || {}));
```

#### 3. Конфликт с другими плагинами
**Диагностика:**
1. Деактивируйте все плагины кроме Code Highlighter Copy
2. Если проблема исчезла - активируйте плагины по одному
3. Найдите конфликтующий плагин

**Решение:**
- Обновите конфликтующий плагин
- Обратитесь к разработчикам плагина
- Используйте альтернативный плагин

#### 4. Кеширование 
**Решение:**
1. Очистите кеш WordPress (если используется плагин кеширования)
2. Очистите кеш браузера (Ctrl+F5 или Cmd+Shift+R)
3. Проверьте в режиме инкогнито

### ❌ Неправильная подсветка синтаксиса

**Причины:**

#### 1. Неподдерживаемый язык
**Проверьте список поддерживаемых языков:**
- PHP: `[php]`
- JavaScript: `[javascript]`
- Python: `[python]`
- HTML: `[html]`
- CSS: `[css]`
- И другие (см. документацию)

#### 2. Смешанный код
```
❌ Избегайте смешивания языков в одном блоке:
[php]
<?php echo "PHP код"; ?>
<script>console.log("JavaScript");</script>
[/php]

✅ Используйте отдельные блоки:
[php]<?php echo "PHP код"; ?>[/php]
[javascript]console.log("JavaScript");[/javascript]
```

### ❌ Блоки кода отображаются как обычный текст

**Решение:**

#### 1. Проверьте активацию плагина
```php
// Проверьте в админке WordPress:
// Плагины → Установленные плагины
// Code Highlighter Copy должен быть активен
```

#### 2. Проверьте настройки плагина
1. Перейдите в **Настройки** → **Code Highlighter**
2. Убедитесь что включена подсветка на фронтенде
3. Сохраните настройки

#### 3. Проверьте права доступа к файлам
```bash
# На сервере проверьте права доступа:
ls -la /wp-content/plugins/code-highlighter-copy/
# Файлы должны быть доступны для чтения
```

---

## Проблемы с кнопкой копирования

### ❌ Кнопка копирования не появляется

**Причины и решения:**

#### 1. Отключена в настройках
1. **Настройки** → **Code Highlighter** → **Внешний вид**
2. Убедитесь что включена "Показывать кнопку копирования"
3. Сохраните настройки

#### 2. CSS конфликт
**Диагностика в консоли браузера (F12):**
```javascript
// Проверьте наличие кнопки в DOM:
document.querySelectorAll('.copy-button, [data-copy]');
```

**Решение:**
```css
/* Добавьте в настройки плагина или в style.css темы: */
.chc-code-wrapper .copy-button {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}
```

### ❌ Кнопка копирования не работает

**Возможные причины:**

#### 1. Браузер не поддерживает Clipboard API
**Проверьте в консоли:**
```javascript
console.log('Clipboard API:', !!navigator.clipboard);
console.log('HTTPS:', location.protocol === 'https:');
```

**Требования для Clipboard API:**
- HTTPS соединение (или localhost для разработки)  
- Современный браузер (Chrome 66+, Firefox 63+, Safari 13.1+)

#### 2. JavaScript ошибки
**Откройте консоль браузера (F12) и проверьте:**
- Есть ли красные ошибки JavaScript
- Загружается ли clipboard.js

**Решение:**
```javascript
// Временное решение - добавьте в код страницы:
if (!navigator.clipboard) {
    // Fallback для старых браузеров
    function fallbackCopyTextToClipboard(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            const successful = document.execCommand('copy');
            console.log('Fallback: Copying text command was ' + (successful ? 'successful' : 'unsuccessful'));
        } catch (err) {
            console.error('Fallback: Unable to copy', err);
        }
        document.body.removeChild(textArea);
    }
}
```

### ❌ Копируется лишний текст или HTML

**Причина:** Копируется HTML разметка вместо чистого кода

**Решение:**
1. Обновите плагин до последней версии
2. Проверьте настройки копирования в **Настройки** → **Code Highlighter**

---

## Проблемы с полноэкранным режимом

### ❌ Полноэкранный режим не работает

**Проверьте:**

#### 1. Поддержка браузером
```javascript
// В консоли браузера:
console.log('Fullscreen API:', !!document.fullscreenEnabled);
```

#### 2. Настройки плагина
1. **Настройки** → **Code Highlighter** → **Внешний вид**
2. Включите "Показывать кнопку полноэкранного режима"

### ❌ Неправильное отображение в полноэкранном режиме

**Решение:**
```css
/* Добавьте в настройки плагина: */
.chc-fullscreen {
    background: #1e1e1e !important;
    color: #d4d4d4 !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
}

.chc-fullscreen .chc-code-block {
    max-height: none !important;
    width: 100% !important;
    height: 100vh !important;
}
```

---

## Проблемы совместимости с темами

### ❌ Стили темы конфликтуют с плагином

**Наиболее частые конфликты:**

#### 1. Переопределение стилей кода
```css
/* Частая проблема в темах: */
pre, code {
    background: #f5f5f5 !important;
    color: #333 !important;
}

/* Решение - добавьте более специфичный селектор: */
.chc-code-wrapper pre[class*="language-"] {
    background: var(--prism-background) !important;
    color: var(--prism-color) !important;
}
```

#### 2. Конфликт с CSS Grid/Flexbox
```css
/* Если блоки кода нарушают макет: */
.chc-code-wrapper {
    width: 100%;
    max-width: 100%;
    overflow-x: auto;
    margin: 20px 0;
}
```

#### 3. Неправильные z-index
```css
/* Если кнопки скрываются за элементами темы: */
.chc-code-toolbar {
    z-index: 999 !important;
}

.chc-fullscreen {
    z-index: 9999 !important;
}
```

### ❌ Проблемы с популярными темами

#### Astra Theme
```css
/* Добавьте в Настройки → Дополнительный CSS: */
.ast-container .chc-code-wrapper {
    width: 100%;
    max-width: none;
}
```

#### GeneratePress
```css
.inside-article .chc-code-wrapper {
    margin: 1.5em 0;
    width: 100%;
}
```

#### Elementor
```css
.elementor-widget-text-editor .chc-code-wrapper {
    overflow: visible;
}
```

---

## Проблемы производительности

### ❌ Медленная загрузка страницы

**Причины и решения:**

#### 1. Много блоков кода на странице
**Рекомендации:**
- Максимум 10-15 блоков кода на страницу
- Используйте сворачиваемые секции для длинных примеров
- Разбивайте контент на несколько страниц

#### 2. Большие блоки кода
```php
// Вместо одного огромного блока:
[php]
// 1000+ строк кода
[/php]

// Разбейте на логические части:
[php]
// Часть 1: Конфигурация (50 строк)
[/php]

[php]  
// Часть 2: Основная логика (100 строк)
[/php]
```

#### 3. Оптимизация загрузки ресурсов
1. **Настройки** → **Code Highlighter** → **Производительность**
2. Включите "Загружать стили только при необходимости"
3. Включите минификацию CSS и JS

### ❌ Высокое потребление памяти

**Решение:**
```javascript
// Если на странице много блоков кода, используйте ленивую загрузку:
// (Добавьте в functions.php темы)

function lazy_load_code_highlighting() {
    ?>
    <script>
    // Подсвечиваем код только когда он становится видимым
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                Prism.highlightElement(entry.target);
                observer.unobserve(entry.target);
            }
        });
    });
    
    document.querySelectorAll('pre[class*="language-"]').forEach(block => {
        observer.observe(block);
    });
    </script>
    <?php
}
add_action('wp_footer', 'lazy_load_code_highlighting');
```

---

## Проблемы на мобильных устройствах

### ❌ Горизонтальная прокрутка не работает

**Решение:**
```css
/* Добавьте в настройки плагина: */
@media (max-width: 768px) {
    .chc-code-wrapper {
        margin: 0 -20px;
        width: calc(100% + 40px);
    }
    
    .chc-code-wrapper pre {
        padding: 15px 20px;
        border-radius: 0;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
    }
}
```

### ❌ Кнопки слишком маленькие на мобильных

```css
@media (max-width: 768px) {
    .chc-code-toolbar button {
        min-height: 44px !important;
        min-width: 44px !important;
        font-size: 16px !important;
    }
    
    .copy-button, .fullscreen-button {
        padding: 12px !important;
    }
}
```

### ❌ Текст кода слишком мелкий

```css
@media (max-width: 768px) {
    .chc-code-wrapper pre,
    .chc-code-wrapper code {
        font-size: 14px !important;
        line-height: 1.6 !important;
    }
}
```

---

## Проблемы с браузерами

### Chrome

#### ❌ Кнопка копирования работает только на HTTPS
**Решение:** Используйте HTTPS для сайта или локальный домен для разработки

#### ❌ Проблемы с автозаполнением в блоках кода
```css
.chc-code-wrapper input,
.chc-code-wrapper textarea {
    -webkit-autofill: none !important;
}
```

### Firefox

#### ❌ Неправильное отображение скроллбара
```css
/* Firefox-specific стили: */
@-moz-document url-prefix() {
    .chc-code-wrapper pre {
        scrollbar-width: thin;
        scrollbar-color: #888 transparent;
    }
}
```

### Safari

#### ❌ Проблемы с Clipboard API
```javascript
// Используйте полифилл для Safari < 13.1:
if (!navigator.clipboard && window.ClipboardItem) {
    // Fallback implementation
}
```

#### ❌ Неправильное отображение в полноэкранном режиме
```css
@supports (-webkit-appearance: none) {
    .chc-fullscreen {
        -webkit-transform: translate3d(0,0,0);
        transform: translate3d(0,0,0);
    }
}
```

### Internet Explorer (если поддерживается)

#### ❌ JavaScript ошибки
```javascript
// Проверка поддержки современных функций:
if (!Array.from) {
    // Полифилл или альтернативная реализация
}
```

---

## Проблемы настроек плагина

### ❌ Настройки не сохраняются

**Возможные причины:**

#### 1. Проблемы с правами доступа
```php
// Проверьте права пользователя в WordPress:
// Пользователь должен иметь права 'manage_options'
```

#### 2. Конфликт с кешированием
1. Отключите временно плагины кеширования
2. Сохраните настройки
3. Включите кеширование обратно
4. Очистите кеш

#### 3. Проблемы с nonce
**В консоли браузера проверьте ошибки AJAX запросов**

### ❌ Настройки сбрасываются после обновления

**Решение:**
1. Создайте резервную копию настроек:
   - **Настройки** → **Code Highlighter** → **Инструменты** 
   - **Экспорт настроек**

2. После обновления импортируйте настройки обратно

### ❌ Предварительный просмотр не работает

**Проверьте:**
1. Включен ли JavaScript
2. Нет ли ошибок в консоли браузера
3. Загружается ли AJAX

---

## Диагностика и отладка

### 🔍 Инструменты диагностики

#### 1. Встроенная страница диагностики
1. **Настройки** → **Code Highlighter** → **Инструменты**
2. **Информация о системе** - проверьте все параметры
3. **Тест функциональности** - запустите автоматические тесты

#### 2. Консоль браузера (F12)
```javascript
// Базовая диагностика в консоли:
console.log('=== Code Highlighter Copy Диагностика ===');
console.log('Prism загружен:', typeof Prism !== 'undefined');
console.log('jQuery загружен:', typeof $ !== 'undefined');
console.log('Clipboard API:', !!navigator.clipboard);
console.log('Fullscreen API:', !!document.fullscreenEnabled);
console.log('Блоки кода:', document.querySelectorAll('[class*="language-"]').length);
console.log('Кнопки копирования:', document.querySelectorAll('.copy-button').length);
```

#### 3. PHP диагностика
```php
// Добавьте в functions.php для отладки:
function chc_debug_info() {
    if (current_user_can('manage_options')) {
        echo '<div style="background: #fff; padding: 10px; border: 1px solid #ccc; margin: 10px 0;">';
        echo '<strong>Code Highlighter Copy Debug:</strong><br>';
        echo 'Plugin активен: ' . (is_plugin_active('code-highlighter-copy/code-highlighter-copy.php') ? 'Да' : 'Нет') . '<br>';
        echo 'WordPress версия: ' . get_bloginfo('version') . '<br>';
        echo 'PHP версия: ' . phpversion() . '<br>';
        echo 'Тема: ' . get_template() . '<br>';
        echo '</div>';
    }
}
// Uncomment для отладки:
// add_action('wp_footer', 'chc_debug_info');
```

### 🔧 Частые исправления

#### Сброс настроек к умолчаниям
1. **Настройки** → **Code Highlighter** → **Инструменты**
2. **Сброс настроек** → **Подтвердить**

#### Переустановка плагина
1. Деактивируйте плагин
2. Удалите папку плагина
3. Установите заново
4. Импортируйте сохраненные настройки

#### Очистка конфликтов
```php
// Временно добавьте в functions.php для изоляции:
function chc_conflict_test() {
    // Отключаем все остальные стили и скрипты
    if (isset($_GET['chc_debug'])) {
        remove_all_actions('wp_enqueue_scripts');
        remove_all_actions('wp_head');
        // Загружаем только наш плагин
    }
}
// add_action('init', 'chc_conflict_test');
// Используйте: yoursite.com/?chc_debug=1
```

---

## 📞 Получение помощи

### Если проблема не решена:

1. **Проверьте FAQ** в документации плагина
2. **Создайте тестовую страницу** с одним блоком кода для изоляции проблемы  
3. **Соберите информацию о системе:**
   - Версия WordPress
   - Версия PHP
   - Активная тема
   - Список активных плагинов
   - Версия браузера
   - Консольные ошибки (скриншот)

4. **Обратитесь в поддержку:**
   - Email: support@ailynx.ru
   - Сайт: https://ailynx.ru
   - Приложите всю собранную информацию

### Полезные ссылки

- [Документация WordPress](https://ru.wordpress.org/support/)
- [Prism.js документация](https://prismjs.com/)
- [Справка по HTML/CSS](https://developer.mozilla.org/)
- [Инструменты разработчика браузера](https://developers.google.com/web/tools/chrome-devtools)

---

**Помните:** Большинство проблем решается правильной настройкой плагина и устранением конфликтов с темой или другими плагинами. Если проблема критическая, всегда можно временно переключиться на стандартные HTML теги `<pre><code>` до решения вопроса.