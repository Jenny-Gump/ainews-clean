<?php
/**
 * Test file for language shortcodes
 * 
 * This file contains examples of all supported language shortcodes
 * for the Code Highlighter Copy plugin.
 */

// Include WordPress
require_once('/path/to/wordpress/wp-load.php');

?>
<!DOCTYPE html>
<html>
<head>
    <title>Language Shortcodes Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h2 {
            margin-top: 30px;
            color: #333;
        }
        .test-section {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <h1>Code Highlighter Copy - Language Shortcodes Test</h1>
    
    <div class="test-section">
        <h2>PHP</h2>
        <?php echo do_shortcode('[php]
<?php
function hello_world() {
    echo "Hello, World!";
    $variable = 42;
    return $variable;
}
?>
[/php]'); ?>
    </div>

    <div class="test-section">
        <h2>Python (using [python] and [py])</h2>
        <?php echo do_shortcode('[python]
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)

print(factorial(5))
[/python]'); ?>
        
        <?php echo do_shortcode('[py]
# Short alias test
import numpy as np
data = np.array([1, 2, 3, 4, 5])
[/py]'); ?>
    </div>

    <div class="test-section">
        <h2>JavaScript (using [javascript] and [js])</h2>
        <?php echo do_shortcode('[javascript]
function calculateSum(arr) {
    return arr.reduce((sum, num) => sum + num, 0);
}

const numbers = [1, 2, 3, 4, 5];
console.log(calculateSum(numbers));
[/javascript]'); ?>
        
        <?php echo do_shortcode('[js]
// Short alias test
const greeting = "Hello, World!";
alert(greeting);
[/js]'); ?>
    </div>

    <div class="test-section">
        <h2>HTML</h2>
        <?php echo do_shortcode('[html]
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Sample Page</title>
</head>
<body>
    <h1>Welcome</h1>
    <p>This is a paragraph.</p>
</body>
</html>
[/html]'); ?>
    </div>

    <div class="test-section">
        <h2>CSS</h2>
        <?php echo do_shortcode('[css]
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.button {
    background-color: #007bff;
    color: white;
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.button:hover {
    background-color: #0056b3;
}
[/css]'); ?>
    </div>

    <div class="test-section">
        <h2>SQL</h2>
        <?php echo do_shortcode('[sql]
SELECT 
    u.id,
    u.username,
    COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
WHERE u.created_at > "2024-01-01"
GROUP BY u.id
ORDER BY post_count DESC
LIMIT 10;
[/sql]'); ?>
    </div>

    <div class="test-section">
        <h2>Bash/Shell (using [bash] and [shell])</h2>
        <?php echo do_shortcode('[bash]
#!/bin/bash

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y nginx mysql-server php-fpm

# Start services
sudo systemctl start nginx
sudo systemctl enable nginx
[/bash]'); ?>
        
        <?php echo do_shortcode('[shell]
# Using shell alias
echo "Current directory: $(pwd)"
ls -la
[/shell]'); ?>
    </div>

    <div class="test-section">
        <h2>C++</h2>
        <?php echo do_shortcode('[cpp]
#include <iostream>
#include <vector>

int main() {
    std::vector<int> numbers = {1, 2, 3, 4, 5};
    
    for(const auto& num : numbers) {
        std::cout << num << " ";
    }
    
    return 0;
}
[/cpp]'); ?>
    </div>

    <div class="test-section">
        <h2>C#</h2>
        <?php echo do_shortcode('[csharp]
using System;
using System.Collections.Generic;

public class Program
{
    public static void Main()
    {
        List<int> numbers = new List<int> {1, 2, 3, 4, 5};
        
        foreach(int num in numbers)
        {
            Console.WriteLine(num);
        }
    }
}
[/csharp]'); ?>
    </div>

    <div class="test-section">
        <h2>Java</h2>
        <?php echo do_shortcode('[java]
import java.util.ArrayList;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        List<String> items = new ArrayList<>();
        items.add("Apple");
        items.add("Banana");
        items.add("Orange");
        
        for(String item : items) {
            System.out.println(item);
        }
    }
}
[/java]'); ?>
    </div>

    <div class="test-section">
        <h2>Go (using [go] and [golang])</h2>
        <?php echo do_shortcode('[go]
package main

import "fmt"

func main() {
    numbers := []int{1, 2, 3, 4, 5}
    sum := 0
    
    for _, num := range numbers {
        sum += num
    }
    
    fmt.Printf("Sum: %d\n", sum)
}
[/go]'); ?>
    </div>

    <div class="test-section">
        <h2>Ruby</h2>
        <?php echo do_shortcode('[ruby]
class Person
  attr_accessor :name, :age
  
  def initialize(name, age)
    @name = name
    @age = age
  end
  
  def introduce
    puts "Hi, I\'m #{@name} and I\'m #{@age} years old."
  end
end

person = Person.new("Alice", 30)
person.introduce
[/ruby]'); ?>
    </div>

    <div class="test-section">
        <h2>Rust</h2>
        <?php echo do_shortcode('[rust]
fn main() {
    let numbers = vec![1, 2, 3, 4, 5];
    let sum: i32 = numbers.iter().sum();
    
    println!("Sum: {}", sum);
    
    for num in &numbers {
        println!("Number: {}", num);
    }
}
[/rust]'); ?>
    </div>

    <div class="test-section">
        <h2>Swift</h2>
        <?php echo do_shortcode('[swift]
import Foundation

struct Person {
    let name: String
    let age: Int
    
    func introduce() {
        print("Hi, I\'m \(name) and I\'m \(age) years old.")
    }
}

let person = Person(name: "Bob", age: 25)
person.introduce()
[/swift]'); ?>
    </div>

    <div class="test-section">
        <h2>Kotlin</h2>
        <?php echo do_shortcode('[kotlin]
data class Person(val name: String, val age: Int)

fun main() {
    val people = listOf(
        Person("Alice", 30),
        Person("Bob", 25),
        Person("Charlie", 35)
    )
    
    people.forEach { person ->
        println("${person.name} is ${person.age} years old")
    }
}
[/kotlin]'); ?>
    </div>

    <div class="test-section">
        <h2>YAML</h2>
        <?php echo do_shortcode('[yaml]
version: "3.8"
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./html:/usr/share/nginx/html
    
  database:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: myapp
    volumes:
      - db_data:/var/lib/mysql

volumes:
  db_data:
[/yaml]'); ?>
    </div>

    <div class="test-section">
        <h2>JSON</h2>
        <?php echo do_shortcode('[json]
{
  "name": "Code Highlighter Copy",
  "version": "1.0.0",
  "description": "WordPress plugin for code highlighting",
  "author": "Your Name",
  "dependencies": {
    "prismjs": "^1.29.0",
    "clipboard": "^2.0.11"
  },
  "scripts": {
    "build": "webpack --mode production",
    "dev": "webpack --mode development --watch"
  }
}
[/json]'); ?>
    </div>

    <div class="test-section">
        <h2>XML</h2>
        <?php echo do_shortcode('[xml]
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system>
        <webServer>
            <rewrite>
                <rules>
                    <rule name="WordPress" stopProcessing="true">
                        <match url=".*" />
                        <conditions>
                            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
                            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
                        </conditions>
                        <action type="Rewrite" url="index.php" />
                    </rule>
                </rules>
            </rewrite>
        </webServer>
    </system>
</configuration>
[/xml]'); ?>
    </div>

    <div class="test-section">
        <h2>PowerShell</h2>
        <?php echo do_shortcode('[powershell]
# Get all running processes
$processes = Get-Process

# Filter processes using more than 100MB of memory
$largeProcesses = $processes | Where-Object { $_.WorkingSet -gt 100MB }

# Display the results
$largeProcesses | Format-Table Name, Id, @{Label="Memory (MB)"; Expression={[math]::Round($_.WorkingSet / 1MB, 2)}}

# Export to CSV
$largeProcesses | Export-Csv -Path "large_processes.csv" -NoTypeInformation
[/powershell]'); ?>
    </div>

    <div class="test-section">
        <h2>Perl</h2>
        <?php echo do_shortcode('[perl]
#!/usr/bin/perl
use strict;
use warnings;

# Define a subroutine
sub factorial {
    my $n = shift;
    return 1 if $n == 0;
    return $n * factorial($n - 1);
}

# Calculate and print factorials
for my $i (0..10) {
    printf "%2d! = %d\n", $i, factorial($i);
}
[/perl]'); ?>
    </div>

    <div class="test-section">
        <h2>Diff/Patch</h2>
        <?php echo do_shortcode('[diff]
--- a/config.php
+++ b/config.php
@@ -10,7 +10,7 @@
 define("DB_HOST", "localhost");
 define("DB_NAME", "wordpress");
 define("DB_USER", "root");
-define("DB_PASSWORD", "old_password");
+define("DB_PASSWORD", "new_secure_password");
 
 // Site settings
 define("SITE_URL", "https://example.com");
@@ -20,6 +20,9 @@
 // Debug mode
 define("WP_DEBUG", false);
 
+// New security settings
+define("FORCE_SSL_ADMIN", true);
+
 // Table prefix
 $table_prefix = "wp_";
[/diff]'); ?>
    </div>

    <div class="test-section">
        <h2>LaTeX</h2>
        <?php echo do_shortcode('[latex]
\documentclass{article}
\usepackage{amsmath}

\begin{document}

\title{Mathematical Formulas}
\author{John Doe}
\date{\today}
\maketitle

\section{Introduction}
This document demonstrates various mathematical formulas.

\section{Equations}
The quadratic formula is:
\begin{equation}
    x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
\end{equation}

\end{document}
[/latex]'); ?>
    </div>

    <div class="test-section">
        <h2>Plain Text</h2>
        <?php echo do_shortcode('[plain]
This is plain text without any syntax highlighting.
It preserves formatting and spacing.

    - Indented content
    - Lists work fine
    - Special characters: < > & " \'
    
No syntax coloring is applied.
[/plain]'); ?>
    </div>

</body>
</html>