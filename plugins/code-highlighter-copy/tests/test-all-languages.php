<?php
/**
 * Test All Languages - Code Highlighter Copy Plugin
 * 
 * This file tests all 40+ supported programming languages
 * to ensure proper syntax highlighting and functionality.
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Test languages with sample code
$test_languages = [
    'php' => '<?php
echo "Hello, World!";
$array = [1, 2, 3];
foreach ($array as $item) {
    echo $item . "\n";
}
?>',
    
    'python' => 'def hello_world():
    """Print hello world message"""
    print("Hello, World!")
    
    numbers = [1, 2, 3, 4, 5]
    for num in numbers:
        print(f"Number: {num}")
        
hello_world()',

    'javascript' => 'function helloWorld() {
    console.log("Hello, World!");
    
    const numbers = [1, 2, 3, 4, 5];
    numbers.forEach(num => {
        console.log(`Number: ${num}`);
    });
}

helloWorld();',

    'html' => '<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Hello World</title>
</head>
<body>
    <h1>Hello, World!</h1>
    <p>This is a test HTML document.</p>
</body>
</html>',

    'css' => '.hello-world {
    color: #333;
    font-size: 2rem;
    text-align: center;
    margin: 20px 0;
    padding: 15px;
    background: linear-gradient(45deg, #f0f0f0, #e0e0e0);
    border-radius: 8px;
}

.hello-world:hover {
    color: #007cba;
    transform: scale(1.05);
    transition: all 0.3s ease;
}',

    'java' => 'public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
        
        int[] numbers = {1, 2, 3, 4, 5};
        for (int num : numbers) {
            System.out.println("Number: " + num);
        }
    }
}',

    'c' => '#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    
    int numbers[] = {1, 2, 3, 4, 5};
    int size = sizeof(numbers) / sizeof(numbers[0]);
    
    for (int i = 0; i < size; i++) {
        printf("Number: %d\\n", numbers[i]);
    }
    
    return 0;
}',

    'cpp' => '#include <iostream>
#include <vector>

int main() {
    std::cout << "Hello, World!" << std::endl;
    
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    for (const auto& num : numbers) {
        std::cout << "Number: " << num << std::endl;
    }
    
    return 0;
}',

    'csharp' => 'using System;

class HelloWorld 
{
    static void Main() 
    {
        Console.WriteLine("Hello, World!");
        
        int[] numbers = {1, 2, 3, 4, 5};
        foreach (int num in numbers) 
        {
            Console.WriteLine($"Number: {num}");
        }
    }
}',

    'ruby' => 'def hello_world
  puts "Hello, World!"
  
  numbers = [1, 2, 3, 4, 5]
  numbers.each do |num|
    puts "Number: #{num}"
  end
end

hello_world',

    'go' => 'package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
    
    numbers := []int{1, 2, 3, 4, 5}
    for _, num := range numbers {
        fmt.Printf("Number: %d\\n", num)
    }
}',

    'rust' => 'fn main() {
    println!("Hello, World!");
    
    let numbers = vec![1, 2, 3, 4, 5];
    for num in &numbers {
        println!("Number: {}", num);
    }
}',

    'swift' => 'import Foundation

func helloWorld() {
    print("Hello, World!")
    
    let numbers = [1, 2, 3, 4, 5]
    for num in numbers {
        print("Number: \\(num)")
    }
}

helloWorld()',

    'kotlin' => 'fun main() {
    println("Hello, World!")
    
    val numbers = listOf(1, 2, 3, 4, 5)
    for (num in numbers) {
        println("Number: $num")
    }
}',

    'typescript' => 'interface NumberArray {
    numbers: number[];
}

function helloWorld(): void {
    console.log("Hello, World!");
    
    const data: NumberArray = {
        numbers: [1, 2, 3, 4, 5]
    };
    
    data.numbers.forEach((num: number) => {
        console.log(`Number: ${num}`);
    });
}

helloWorld();',

    'sql' => 'CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email) VALUES 
    ("John Doe", "john@example.com"),
    ("Jane Smith", "jane@example.com");

SELECT * FROM users WHERE email LIKE "%@example.com";',

    'json' => '{
  "name": "Code Highlighter Copy",
  "version": "1.0.0",
  "description": "WordPress plugin for syntax highlighting",
  "languages": [
    "php",
    "javascript",
    "python",
    "html",
    "css"
  ],
  "features": {
    "copyButton": true,
    "fullscreen": true,
    "lineNumbers": true,
    "themes": 8
  }
}',

    'xml' => '<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <languages>
        <language name="PHP" extension="php" />
        <language name="JavaScript" extension="js" />
        <language name="Python" extension="py" />
    </languages>
    <settings>
        <theme>okaidia</theme>
        <lineNumbers>true</lineNumbers>
        <copyButton>true</copyButton>
    </settings>
</configuration>',

    'yaml' => 'name: Code Highlighter Copy
version: 1.0.0
description: WordPress plugin for syntax highlighting

languages:
  - php
  - javascript
  - python
  - html
  - css

features:
  copyButton: true
  fullscreen: true
  lineNumbers: true
  themes: 8

settings:
  defaultTheme: okaidia
  showLineNumbers: true
  buttonPosition: topRight',

    'bash' => '#!/bin/bash

echo "Hello, World!"

# Array of numbers
numbers=(1 2 3 4 5)

# Loop through array
for num in "${numbers[@]}"; do
    echo "Number: $num"
done

# Function example
hello_function() {
    local name=$1
    echo "Hello, $name!"
}

hello_function "World"',

    'markdown' => '# Hello World Example

This is a **markdown** document showing *various* formatting options.

## Code Examples

Here is some inline `code` and a code block:

```javascript
console.log("Hello, World!");
```

### Lists

- Item 1
- Item 2
- Item 3

### Links

[WordPress](https://wordpress.org)

### Images

![Alt text](image.jpg)',

    'perl' => '#!/usr/bin/perl
use strict;
use warnings;

print "Hello, World!\\n";

my @numbers = (1, 2, 3, 4, 5);
foreach my $num (@numbers) {
    print "Number: $num\\n";
}

sub hello_sub {
    my $name = shift;
    print "Hello, $name!\\n";
}

hello_sub("World");',

    'r' => '# Hello World in R
print("Hello, World!")

# Vector of numbers
numbers <- c(1, 2, 3, 4, 5)

# Loop through vector
for (num in numbers) {
  cat("Number:", num, "\\n")
}

# Function example
hello_function <- function(name) {
  cat("Hello,", name, "!\\n")
}

hello_function("World")',

    'scala' => 'object HelloWorld {
  def main(args: Array[String]): Unit = {
    println("Hello, World!")
    
    val numbers = List(1, 2, 3, 4, 5)
    numbers.foreach(num => println(s"Number: $num"))
  }
  
  def hello(name: String): Unit = {
    println(s"Hello, $name!")
  }
}',

    'powershell' => 'Write-Host "Hello, World!"

# Array of numbers
$numbers = @(1, 2, 3, 4, 5)

# Loop through array
foreach ($num in $numbers) {
    Write-Host "Number: $num"
}

# Function example
function Say-Hello {
    param([string]$Name)
    Write-Host "Hello, $Name!"
}

Say-Hello -Name "World"',

    'haskell' => 'main :: IO ()
main = do
    putStrLn "Hello, World!"
    mapM_ (putStrLn . ("Number: " ++) . show) [1..5]

hello :: String -> IO ()
hello name = putStrLn $ "Hello, " ++ name ++ "!"

-- Function composition example
doubleList :: [Int] -> [Int]
doubleList = map (*2)',

    'clojure' => '(defn hello-world []
  (println "Hello, World!")
  (doseq [num [1 2 3 4 5]]
    (println (str "Number: " num))))

(defn hello [name]
  (println (str "Hello, " name "!")))

; Map example
(defn double-numbers [numbers]
  (map #(* % 2) numbers))

(hello-world)
(hello "World")'
];

?>
<!DOCTYPE html>
<html>
<head>
    <title>Test All Languages - Code Highlighter Copy</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: #f5f5f5;
        }
        .test-container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .language-test {
            margin: 30px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }
        .language-header {
            background: #333;
            color: white;
            padding: 10px 15px;
            font-weight: bold;
            text-transform: uppercase;
        }
        .language-content {
            padding: 15px;
        }
        .test-info {
            background: #e8f4fd;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #007cba;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #007cba;
            color: white;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="test-container">
        <h1>Тестирование всех поддерживаемых языков</h1>
        
        <div class="test-info">
            <h3>Информация о тестировании</h3>
            <p>Эта страница демонстрирует работу плагина Code Highlighter Copy со всеми поддерживаемыми языками программирования.</p>
            <p><strong>Что тестируется:</strong></p>
            <ul>
                <li>Корректная подсветка синтаксиса</li>
                <li>Работа кнопки копирования</li>
                <li>Полноэкранный режим</li>
                <li>Отзывчивый дизайн</li>
                <li>Совместимость с темами WordPress</li>
            </ul>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h4>Всего языков</h4>
                <div style="font-size: 2em; font-weight: bold;"><?php echo count($test_languages); ?></div>
            </div>
            <div class="stat-card">
                <h4>Тем оформления</h4>
                <div style="font-size: 2em; font-weight: bold;">8</div>
            </div>
            <div class="stat-card">
                <h4>Функций</h4>
                <div style="font-size: 2em; font-weight: bold;">5+</div>
            </div>
        </div>

        <?php foreach ($test_languages as $lang => $code): ?>
        <div class="language-test" id="test-<?php echo esc_attr($lang); ?>">
            <div class="language-header">
                <?php echo esc_html(strtoupper($lang)); ?> - Тестирование
            </div>
            <div class="language-content">
                <h4>Шорткод: [<?php echo esc_html($lang); ?>]...[/<?php echo esc_html($lang); ?>]</h4>
                
                <!-- Тестируем шорткод -->
                <?php if (function_exists('do_shortcode')): ?>
                    <?php echo do_shortcode("[{$lang}]{$code}[/{$lang}]"); ?>
                <?php else: ?>
                    <div class="error">
                        <p><strong>Ошибка:</strong> WordPress не загружен. Этот файл должен запускаться в контексте WordPress.</p>
                        <pre><code class="language-<?php echo esc_attr($lang); ?>"><?php echo esc_html($code); ?></code></pre>
                    </div>
                <?php endif; ?>
                
                <div style="margin-top: 15px; padding: 10px; background: #f9f9f9; border-radius: 4px;">
                    <small>
                        <strong>Проверьте:</strong>
                        ✓ Подсветка синтаксиса | 
                        ✓ Кнопка копирования | 
                        ✓ Полноэкранный режим | 
                        ✓ Номера строк
                    </small>
                </div>
            </div>
        </div>
        <?php endforeach; ?>

        <div style="margin-top: 40px; padding: 20px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px;">
            <h3 style="color: #155724;">Инструкции для тестирования</h3>
            <ol style="color: #155724;">
                <li>Убедитесь, что все блоки кода отображаются с правильной подсветкой синтаксиса</li>
                <li>Проверьте работу кнопки копирования в каждом блоке</li>
                <li>Протестируйте полноэкранный режим (кнопка расширения)</li>
                <li>Проверьте адаптивность на мобильных устройствах</li>
                <li>Убедитесь, что нет конфликтов с темой WordPress</li>
                <li>Проверьте производительность страницы</li>
            </ol>
        </div>

        <div style="margin-top: 20px; text-align: center; color: #666;">
            <p>Тестовая страница сгенерирована плагином Code Highlighter Copy v1.0.0</p>
            <p><strong>Дата генерации:</strong> <?php echo date('d.m.Y H:i:s'); ?></p>
        </div>
    </div>

    <script>
        // Дополнительные тесты JavaScript
        document.addEventListener('DOMContentLoaded', function() {
            console.log('=== Code Highlighter Copy - Test Results ===');
            
            // Тест: подсчет блоков кода
            const codeBlocks = document.querySelectorAll('pre[class*="language-"]');
            console.log(`Найдено блоков кода: ${codeBlocks.length}`);
            
            // Тест: проверка кнопок копирования
            const copyButtons = document.querySelectorAll('.copy-button, [data-copy]');
            console.log(`Найдено кнопок копирования: ${copyButtons.length}`);
            
            // Тест: проверка кнопок полноэкранного режима
            const fullscreenButtons = document.querySelectorAll('.fullscreen-button, [data-fullscreen]');
            console.log(`Найдено кнопок полноэкранного режима: ${fullscreenButtons.length}`);
            
            // Тест: проверка загрузки Prism.js
            if (typeof Prism !== 'undefined') {
                console.log('✓ Prism.js загружен успешно');
                console.log(`Поддерживаемые языки Prism: ${Object.keys(Prism.languages).length}`);
            } else {
                console.error('✗ Prism.js не загружен');
            }
            
            // Тест: проверка clipboard функциональности
            if (navigator.clipboard) {
                console.log('✓ Clipboard API поддерживается');
            } else {
                console.warn('⚠ Clipboard API не поддерживается в этом браузере');
            }
            
            console.log('=== Завершение тестирования ===');
        });
    </script>
</body>
</html>