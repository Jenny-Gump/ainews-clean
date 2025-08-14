<?php
/**
 * Functionality Tests - Code Highlighter Copy Plugin
 * 
 * This file contains comprehensive functionality tests
 * for all plugin features and capabilities.
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

?>
<!DOCTYPE html>
<html>
<head>
    <title>Functionality Tests - Code Highlighter Copy</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 0;
            padding: 20px; 
            background: #f8f9fa;
            line-height: 1.6;
        }
        .test-suite {
            max-width: 1200px;
            margin: 0 auto;
        }
        .test-header {
            background: linear-gradient(135deg, #007cba 0%, #005a8b 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }
        .test-category {
            background: white;
            margin: 20px 0;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .category-header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            font-size: 1.2em;
            font-weight: 600;
        }
        .category-content {
            padding: 25px;
        }
        .test-case {
            margin: 25px 0;
            padding: 20px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        .test-case:hover {
            border-color: #007cba;
            box-shadow: 0 2px 10px rgba(0,123,186,0.1);
        }
        .test-title {
            color: #2c3e50;
            font-weight: 600;
            margin-bottom: 15px;
            font-size: 1.1em;
        }
        .test-description {
            color: #666;
            margin-bottom: 20px;
            line-height: 1.6;
        }
        .success { 
            color: #28a745; 
            font-weight: 600;
        }
        .warning { 
            color: #ffc107; 
            font-weight: 600;
        }
        .error { 
            color: #dc3545; 
            font-weight: 600;
        }
        .test-results {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
            border-left: 4px solid #007cba;
        }
        .responsive-test {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }
        @media (max-width: 768px) {
            .responsive-test {
                grid-template-columns: 1fr;
            }
        }
        .performance-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .metric-card {
            background: linear-gradient(135deg, #17a2b8, #138496);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .compatibility-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .compatibility-item {
            background: #fff;
            border: 1px solid #dee2e6;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
        .test-checklist {
            list-style: none;
            padding: 0;
        }
        .test-checklist li {
            padding: 8px 0;
            position: relative;
            padding-left: 30px;
        }
        .test-checklist li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #28a745;
            font-weight: bold;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="test-suite">
        <div class="test-header">
            <h1>🧪 Функциональное тестирование</h1>
            <p>Комплексная проверка всех возможностей плагина Code Highlighter Copy</p>
            <p><strong>Версия:</strong> 1.0.0 | <strong>Дата тестирования:</strong> <?php echo date('d.m.Y H:i'); ?></p>
        </div>

        <!-- Тест 1: Основная функциональность -->
        <div class="test-category">
            <div class="category-header">
                1. Основная функциональность шорткодов
            </div>
            <div class="category-content">
                <div class="test-case">
                    <div class="test-title">Тест базовых шорткодов</div>
                    <div class="test-description">
                        Проверка корректной работы основных шорткодов для популярных языков программирования.
                    </div>
                    
                    <!-- PHP Test -->
                    <h4>PHP код:</h4>
                    <?php echo do_shortcode('[php]<?php echo "Тест PHP"; ?>[/php]'); ?>
                    
                    <!-- JavaScript Test -->
                    <h4>JavaScript код:</h4>
                    <?php echo do_shortcode('[javascript]console.log("Тест JavaScript");[/javascript]'); ?>
                    
                    <!-- Python Test -->
                    <h4>Python код:</h4>
                    <?php echo do_shortcode('[python]print("Тест Python")[/python]'); ?>
                    
                    <div class="test-results">
                        <strong>Ожидаемый результат:</strong> Все блоки должны отображаться с корректной подсветкой синтаксиса
                    </div>
                </div>

                <div class="test-case">
                    <div class="test-title">Тест специальных символов и HTML-энтитей</div>
                    <div class="test-description">
                        Проверка корректной обработки специальных символов, HTML-тегов и экранирования.
                    </div>
                    
                    <?php echo do_shortcode('[html]<script>alert("XSS тест");</script>
<div class="test">&lt;специальные&gt; символы &amp; энтити</div>[/html]'); ?>
                    
                    <div class="test-results">
                        <strong>Ожидаемый результат:</strong> HTML-теги должны быть экранированы и безопасно отображены
                    </div>
                </div>
            </div>
        </div>

        <!-- Тест 2: Кнопка копирования -->
        <div class="test-category">
            <div class="category-header">
                2. Функциональность кнопки копирования
            </div>
            <div class="category-content">
                <div class="test-case">
                    <div class="test-title">Тест работы кнопки Copy</div>
                    <div class="test-description">
                        Проверьте, что кнопка копирования появляется и работает корректно.
                    </div>
                    
                    <?php echo do_shortcode('[javascript]// Нажмите кнопку "Copy" для тестирования
function testCopy() {
    return "Этот код должен скопироваться в буфер обмена";
}

console.log(testCopy());[/javascript]'); ?>
                    
                    <div class="test-results">
                        <ul class="test-checklist">
                            <li>Кнопка "Copy" видна в правом верхнем углу блока</li>
                            <li>При нажатии код копируется в буфер обмена</li>
                            <li>Появляется уведомление об успешном копировании</li>
                            <li>Кнопка меняет состояние на короткое время</li>
                        </ul>
                    </div>
                </div>

                <div class="test-case">
                    <div class="test-title">Тест копирования многострочного кода</div>
                    
                    <?php echo do_shortcode('[css]/* Многострочный CSS для тестирования копирования */
.test-block {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}

.test-block:hover {
    transform: translateY(-2px);
}[/css]'); ?>

                    <div class="test-results">
                        <strong>Тест:</strong> Скопированный текст должен сохранять все переносы строк и отступы
                    </div>
                </div>
            </div>
        </div>

        <!-- Тест 3: Полноэкранный режим -->
        <div class="test-category">
            <div class="category-header">
                3. Полноэкранный режим
            </div>
            <div class="category-content">
                <div class="test-case">
                    <div class="test-title">Тест полноэкранного просмотра</div>
                    <div class="test-description">
                        Проверка работы кнопки полноэкранного режима и корректного отображения.
                    </div>
                    
                    <?php echo do_shortcode('[python]#!/usr/bin/env python3
"""
Длинный пример кода для тестирования полноэкранного режима
Этот код должен комфортно читаться в полноэкранном режиме
"""

class TestFullscreen:
    def __init__(self, title):
        self.title = title
        self.data = []
    
    def add_item(self, item):
        """Добавление элемента в список"""
        self.data.append(item)
        print(f"Добавлен элемент: {item}")
    
    def display_all(self):
        """Отображение всех элементов"""
        print(f"\n=== {self.title} ===")
        for i, item in enumerate(self.data, 1):
            print(f"{i}. {item}")
    
    def remove_item(self, item):
        """Удаление элемента из списка"""
        if item in self.data:
            self.data.remove(item)
            print(f"Удален элемент: {item}")
        else:
            print(f"Элемент не найден: {item}")

# Пример использования
test = TestFullscreen("Тестовые данные")
test.add_item("Первый элемент")
test.add_item("Второй элемент")
test.add_item("Третий элемент")
test.display_all()
test.remove_item("Второй элемент")
test.display_all()[/python]'); ?>
                    
                    <div class="test-results">
                        <ul class="test-checklist">
                            <li>Кнопка полноэкранного режима видна</li>
                            <li>При нажатии код открывается в полноэкранном режиме</li>
                            <li>Есть кнопка для выхода из полноэкранного режима</li>
                            <li>Подсветка синтаксиса сохраняется</li>
                            <li>Кнопка копирования работает в полноэкранном режиме</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- Тест 4: Адаптивность -->
        <div class="test-category">
            <div class="category-header">
                4. Адаптивность и мобильная совместимость
            </div>
            <div class="category-content">
                <div class="test-case">
                    <div class="test-title">Тест отзывчивого дизайна</div>
                    <div class="test-description">
                        Проверьте отображение на различных размерах экрана (используйте Developer Tools браузера).
                    </div>
                    
                    <div class="responsive-test">
                        <div>
                            <h4>Десктоп версия:</h4>
                            <?php echo do_shortcode('[css].desktop-test {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}[/css]'); ?>
                        </div>
                        <div>
                            <h4>Мобильная версия:</h4>
                            <?php echo do_shortcode('[css]@media (max-width: 768px) {
    .mobile-test {
        padding: 10px;
        font-size: 14px;
    }
}[/css]'); ?>
                        </div>
                    </div>
                    
                    <div class="test-results">
                        <strong>Тестируемые разрешения:</strong>
                        <ul>
                            <li>1920x1080 (Desktop)</li>
                            <li>1366x768 (Laptop)</li>
                            <li>768x1024 (Tablet)</li>
                            <li>375x667 (Mobile)</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- Тест 5: Производительность -->
        <div class="test-category">
            <div class="category-header">
                5. Производительность
            </div>
            <div class="category-content">
                <div class="test-case">
                    <div class="test-title">Метрики производительности</div>
                    <div class="test-description">
                        Измерение времени загрузки и влияния плагина на производительность сайта.
                    </div>
                    
                    <div class="performance-metrics">
                        <div class="metric-card">
                            <h4>Размер CSS</h4>
                            <div id="css-size">Измеряется...</div>
                        </div>
                        <div class="metric-card">
                            <h4>Размер JS</h4>
                            <div id="js-size">Измеряется...</div>
                        </div>
                        <div class="metric-card">
                            <h4>Время загрузки</h4>
                            <div id="load-time">Измеряется...</div>
                        </div>
                        <div class="metric-card">
                            <h4>DOM элементы</h4>
                            <div id="dom-count">Измеряется...</div>
                        </div>
                    </div>
                    
                    <!-- Тест с большим количеством блоков -->
                    <h4>Тест производительности с множественными блоками:</h4>
                    <?php for ($i = 1; $i <= 5; $i++): ?>
                        <h5>Блок кода #<?php echo $i; ?>:</h5>
                        <?php echo do_shortcode("[php]<?php
// Блок кода номер $i для тестирования производительности
echo \"Это тестовый блок номер $i\";

\$data = array(
    'id' => $i,
    'name' => 'Test Block $i',
    'active' => true
);

foreach (\$data as \$key => \$value) {
    echo \"\$key: \$value\" . PHP_EOL;
}
?>[/php]"); ?>
                    <?php endfor; ?>
                </div>
            </div>
        </div>

        <!-- Тест 6: Совместимость -->
        <div class="test-category">
            <div class="category-header">
                6. Совместимость с темами и браузерами
            </div>
            <div class="category-content">
                <div class="test-case">
                    <div class="test-title">Браузерная совместимость</div>
                    <div class="compatibility-grid">
                        <div class="compatibility-item">
                            <h4>Chrome</h4>
                            <div id="chrome-test">Тестируется...</div>
                        </div>
                        <div class="compatibility-item">
                            <h4>Firefox</h4>
                            <div id="firefox-test">Тестируется...</div>
                        </div>
                        <div class="compatibility-item">
                            <h4>Safari</h4>
                            <div id="safari-test">Тестируется...</div>
                        </div>
                        <div class="compatibility-item">
                            <h4>Edge</h4>
                            <div id="edge-test">Тестируется...</div>
                        </div>
                    </div>
                </div>

                <div class="test-case">
                    <div class="test-title">Тест конфликтов с темой</div>
                    <div class="test-description">
                        Проверка стилевых конфликтов с популярными темами WordPress.
                    </div>
                    
                    <?php echo do_shortcode('[html]<!-- HTML для проверки конфликтов стилей -->
<div class="wp-theme-test">
    <h1>Заголовок темы</h1>
    <p>Обычный текст темы</p>
    <a href="#" class="button">Кнопка темы</a>
</div>[/html]'); ?>
                </div>
            </div>
        </div>

        <!-- Итоговый отчет -->
        <div class="test-category">
            <div class="category-header">
                7. Итоговый отчет тестирования
            </div>
            <div class="category-content">
                <div id="test-summary" class="test-results">
                    <h3>Результаты автоматических тестов:</h3>
                    <div id="auto-test-results">Выполняется...</div>
                </div>
                
                <div class="test-case">
                    <div class="test-title">Чек-лист для ручного тестирования</div>
                    <ul class="test-checklist">
                        <li>Все блоки кода отображаются с корректной подсветкой</li>
                        <li>Кнопки копирования работают во всех блоках</li>
                        <li>Полноэкранный режим функционирует правильно</li>
                        <li>Дизайн адаптивен на мобильных устройствах</li>
                        <li>Нет конфликтов стилей с темой WordPress</li>
                        <li>Производительность соответствует стандартам</li>
                        <li>Плагин работает во всех основных браузерах</li>
                        <li>Нет JavaScript ошибок в консоли</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Тест производительности
            const startTime = performance.now();
            
            // Подсчет DOM элементов
            const codeBlocks = document.querySelectorAll('pre[class*="language-"]');
            document.getElementById('dom-count').textContent = document.getElementsByTagName('*').length;
            
            // Определение браузера
            function detectBrowser() {
                const userAgent = navigator.userAgent;
                if (userAgent.includes('Chrome')) return 'Chrome';
                if (userAgent.includes('Firefox')) return 'Firefox';  
                if (userAgent.includes('Safari')) return 'Safari';
                if (userAgent.includes('Edge')) return 'Edge';
                return 'Unknown';
            }
            
            // Тест браузерной совместимости
            const browser = detectBrowser();
            const browserTests = ['chrome', 'firefox', 'safari', 'edge'];
            
            browserTests.forEach(b => {
                const element = document.getElementById(`${b}-test`);
                if (element) {
                    if (b === browser.toLowerCase()) {
                        element.innerHTML = '<span class="success">✓ Активный</span>';
                    } else {
                        element.innerHTML = '<span>Не активный</span>';
                    }
                }
            });
            
            // Измерение времени загрузки
            window.addEventListener('load', function() {
                const loadTime = performance.now() - startTime;
                document.getElementById('load-time').textContent = Math.round(loadTime) + ' мс';
            });
            
            // Проверка поддержки функций
            const features = {
                clipboard: !!navigator.clipboard,
                fullscreen: !!document.fullscreenEnabled,
                prism: typeof Prism !== 'undefined'
            };
            
            // Формирование итогового отчета
            setTimeout(() => {
                let report = '<ul>';
                report += `<li><strong>Браузер:</strong> ${browser}</li>`;
                report += `<li><strong>Блоков кода:</strong> ${codeBlocks.length}</li>`;
                report += `<li><strong>Clipboard API:</strong> ${features.clipboard ? '✓ Поддерживается' : '✗ Не поддерживается'}</li>`;
                report += `<li><strong>Fullscreen API:</strong> ${features.fullscreen ? '✓ Поддерживается' : '✗ Не поддерживается'}</li>`;
                report += `<li><strong>Prism.js:</strong> ${features.prism ? '✓ Загружен' : '✗ Не загружен'}</li>`;
                report += '</ul>';
                
                document.getElementById('auto-test-results').innerHTML = report;
            }, 1000);
            
            // Логирование результатов
            console.group('🧪 Code Highlighter Copy - Результаты тестирования');
            console.log('Браузер:', browser);
            console.log('Блоков кода найдено:', codeBlocks.length);
            console.log('Поддержка Clipboard API:', features.clipboard);
            console.log('Поддержка Fullscreen API:', features.fullscreen);
            console.log('Prism.js загружен:', features.prism);
            console.groupEnd();
        });
    </script>
</body>
</html>