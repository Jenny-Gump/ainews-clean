<?php
/**
 * Test file for Prism.js integration
 * 
 * This file tests the Prism.js integration with various programming languages
 * Usage: Add this as a WordPress page template or include in a test page
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

get_header(); 
?>

<div class="wrap" style="max-width: 1200px; margin: 50px auto; padding: 20px;">
    <h1>Code Highlighter Copy - Prism.js Integration Test</h1>
    
    <p>Testing Prism.js syntax highlighting with various programming languages:</p>
    
    <hr style="margin: 30px 0;">
    
    <!-- Test JavaScript -->
    <h2>JavaScript Example</h2>
    <pre class="language-javascript line-numbers"><code>// JavaScript async/await example
async function fetchUserData(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        const data = await response.json();
        
        // Process the data
        const processedData = {
            ...data,
            timestamp: Date.now(),
            processed: true
        };
        
        console.log('User data:', processedData);
        return processedData;
    } catch (error) {
        console.error('Error fetching user:', error);
        throw new Error(`Failed to fetch user ${userId}`);
    }
}

// Call the function
fetchUserData(123).then(data => {
    console.log('Success!', data);
});</code></pre>
    
    <!-- Test Python -->
    <h2>Python Example</h2>
    <pre class="language-python line-numbers"><code># Python decorator example
import functools
import time

def timer_decorator(func):
    """Decorator that measures function execution time"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper

@timer_decorator
def fibonacci(n):
    """Calculate fibonacci number recursively"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Test the decorated function
result = fibonacci(10)
print(f"Fibonacci(10) = {result}")</code></pre>
    
    <!-- Test PHP -->
    <h2>PHP Example</h2>
    <pre class="language-php line-numbers"><code>&lt;?php
// PHP class example with namespace
namespace App\Services;

use App\Models\User;
use Illuminate\Support\Facades\Cache;

class UserService
{
    private $cachePrefix = 'user:';
    
    /**
     * Get user by ID with caching
     *
     * @param int $id
     * @return User|null
     */
    public function getUserById(int $id): ?User
    {
        $cacheKey = $this->cachePrefix . $id;
        
        return Cache::remember($cacheKey, 3600, function () use ($id) {
            return User::find($id);
        });
    }
    
    /**
     * Update user data
     *
     * @param int $id
     * @param array $data
     * @return bool
     */
    public function updateUser(int $id, array $data): bool
    {
        $user = User::find($id);
        
        if (!$user) {
            throw new \Exception("User not found");
        }
        
        $updated = $user->update($data);
        
        // Clear cache
        Cache::forget($this->cachePrefix . $id);
        
        return $updated;
    }
}</code></pre>
    
    <!-- Test SQL -->
    <h2>SQL Example</h2>
    <pre class="language-sql line-numbers"><code>-- Complex SQL query with CTEs and window functions
WITH monthly_sales AS (
    SELECT 
        DATE_TRUNC('month', order_date) AS month,
        product_id,
        SUM(quantity * price) AS total_sales,
        COUNT(DISTINCT customer_id) AS unique_customers
    FROM orders o
    JOIN order_items oi ON o.id = oi.order_id
    WHERE order_date >= DATE_SUB(CURRENT_DATE, INTERVAL 12 MONTH)
    GROUP BY DATE_TRUNC('month', order_date), product_id
),
ranked_products AS (
    SELECT 
        month,
        product_id,
        total_sales,
        unique_customers,
        ROW_NUMBER() OVER (PARTITION BY month ORDER BY total_sales DESC) AS sales_rank,
        LAG(total_sales) OVER (PARTITION BY product_id ORDER BY month) AS prev_month_sales
    FROM monthly_sales
)
SELECT 
    rp.month,
    p.product_name,
    rp.total_sales,
    rp.unique_customers,
    rp.sales_rank,
    ROUND(((rp.total_sales - rp.prev_month_sales) / rp.prev_month_sales) * 100, 2) AS growth_percentage
FROM ranked_products rp
JOIN products p ON rp.product_id = p.id
WHERE rp.sales_rank <= 10
ORDER BY rp.month DESC, rp.sales_rank;</code></pre>
    
    <!-- Test CSS -->
    <h2>CSS Example</h2>
    <pre class="language-css line-numbers"><code>/* Modern CSS with Grid and Custom Properties */
:root {
    --primary-color: #3498db;
    --secondary-color: #2ecc71;
    --text-color: #333;
    --spacing-unit: 1rem;
    --border-radius: 8px;
}

.container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: calc(var(--spacing-unit) * 2);
    padding: var(--spacing-unit);
    max-width: 1200px;
    margin: 0 auto;
}

.card {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    border-radius: var(--border-radius);
    padding: calc(var(--spacing-unit) * 1.5);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
}

@media (prefers-color-scheme: dark) {
    :root {
        --text-color: #f0f0f0;
        --primary-color: #2980b9;
    }
    
    body {
        background-color: #1a1a1a;
        color: var(--text-color);
    }
}</code></pre>
    
    <!-- Test Bash -->
    <h2>Bash/Shell Example</h2>
    <pre class="language-bash line-numbers"><code>#!/bin/bash
# Bash script for automated backup with error handling

set -euo pipefail  # Exit on error, undefined variable, or pipe failure

# Configuration
BACKUP_DIR="/var/backups"
SOURCE_DIR="/var/www/html"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${DATE}.tar.gz"
LOG_FILE="/var/log/backup.log"
RETENTION_DAYS=30

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to perform backup
perform_backup() {
    log_message "Starting backup of $SOURCE_DIR"
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Create compressed archive
    if tar -czf "${BACKUP_DIR}/${BACKUP_NAME}" -C "$SOURCE_DIR" .; then
        log_message "Backup created successfully: ${BACKUP_NAME}"
        
        # Calculate backup size
        BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}" | cut -f1)
        log_message "Backup size: ${BACKUP_SIZE}"
    else
        log_message "ERROR: Backup failed!"
        exit 1
    fi
}

# Function to clean old backups
cleanup_old_backups() {
    log_message "Removing backups older than ${RETENTION_DAYS} days"
    
    find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
    
    REMAINING_BACKUPS=$(ls -1 "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | wc -l)
    log_message "Remaining backups: ${REMAINING_BACKUPS}"
}

# Main execution
main() {
    log_message "=== Backup Script Started ==="
    perform_backup
    cleanup_old_backups
    log_message "=== Backup Script Completed ==="
}

# Run main function
main "$@"</code></pre>
    
    <!-- Test JSON -->
    <h2>JSON Example</h2>
    <pre class="language-json line-numbers"><code>{
    "name": "code-highlighter-copy",
    "version": "1.0.0",
    "description": "WordPress plugin for syntax highlighting with copy functionality",
    "config": {
        "languages": [
            "javascript",
            "python",
            "php",
            "sql",
            "css",
            "bash"
        ],
        "themes": {
            "default": "tomorrow-night",
            "available": [
                "tomorrow-night",
                "okaidia",
                "solarized-light",
                "dracula"
            ]
        },
        "features": {
            "lineNumbers": true,
            "copyButton": true,
            "showLanguage": true,
            "autoDetect": false
        }
    },
    "dependencies": {
        "prismjs": "^1.29.0",
        "clipboard": "^2.0.11"
    },
    "author": {
        "name": "Your Name",
        "email": "email@example.com",
        "url": "https://example.com"
    }
}</code></pre>
    
    <!-- Test Go -->
    <h2>Go Example</h2>
    <pre class="language-go line-numbers"><code>package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "time"
)

// User represents a user in the system
type User struct {
    ID        int       `json:"id"`
    Name      string    `json:"name"`
    Email     string    `json:"email"`
    CreatedAt time.Time `json:"created_at"`
}

// UserService handles user-related operations
type UserService struct {
    users map[int]*User
}

// NewUserService creates a new user service
func NewUserService() *UserService {
    return &UserService{
        users: make(map[int]*User),
    }
}

// GetUser retrieves a user by ID
func (s *UserService) GetUser(ctx context.Context, id int) (*User, error) {
    select {
    case <-ctx.Done():
        return nil, ctx.Err()
    default:
        if user, exists := s.users[id]; exists {
            return user, nil
        }
        return nil, fmt.Errorf("user %d not found", id)
    }
}

// HandleGetUser is an HTTP handler for getting users
func (s *UserService) HandleGetUser(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()
    
    // Parse user ID from request
    var id int
    if _, err := fmt.Sscanf(r.URL.Path, "/users/%d", &id); err != nil {
        http.Error(w, "Invalid user ID", http.StatusBadRequest)
        return
    }
    
    user, err := s.GetUser(ctx, id)
    if err != nil {
        http.Error(w, err.Error(), http.StatusNotFound)
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(user)
}

func main() {
    service := NewUserService()
    
    http.HandleFunc("/users/", service.HandleGetUser)
    
    log.Println("Server starting on :8080")
    if err := http.ListenAndServe(":8080", nil); err != nil {
        log.Fatal(err)
    }
}</code></pre>
    
    <!-- Test Rust -->
    <h2>Rust Example</h2>
    <pre class="language-rust line-numbers"><code>use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use tokio::time::{sleep, Duration};

#[derive(Debug, Clone)]
struct Cache<T> {
    data: Arc<Mutex<HashMap<String, T>>>,
    ttl: Duration,
}

impl<T: Clone> Cache<T> {
    /// Create a new cache with the specified TTL
    pub fn new(ttl_seconds: u64) -> Self {
        Self {
            data: Arc::new(Mutex::new(HashMap::new())),
            ttl: Duration::from_secs(ttl_seconds),
        }
    }
    
    /// Insert a value into the cache
    pub async fn insert(&self, key: String, value: T) {
        let data = self.data.clone();
        let ttl = self.ttl;
        let key_clone = key.clone();
        
        // Insert the value
        {
            let mut cache = data.lock().unwrap();
            cache.insert(key, value);
        }
        
        // Schedule removal after TTL
        tokio::spawn(async move {
            sleep(ttl).await;
            let mut cache = data.lock().unwrap();
            cache.remove(&key_clone);
        });
    }
    
    /// Get a value from the cache
    pub fn get(&self, key: &str) -> Option<T> {
        let cache = self.data.lock().unwrap();
        cache.get(key).cloned()
    }
}

#[tokio::main]
async fn main() {
    let cache = Cache::new(60); // 60 second TTL
    
    // Insert some data
    cache.insert("user:1".to_string(), "Alice").await;
    cache.insert("user:2".to_string(), "Bob").await;
    
    // Retrieve data
    if let Some(user) = cache.get("user:1") {
        println!("Found user: {}", user);
    }
    
    // Wait for expiration
    sleep(Duration::from_secs(61)).await;
    
    if cache.get("user:1").is_none() {
        println!("User expired from cache");
    }
}</code></pre>
    
    <!-- Test TypeScript -->
    <h2>TypeScript Example</h2>
    <pre class="language-typescript line-numbers"><code>// TypeScript with generics and decorators
interface ApiResponse<T> {
    data: T;
    status: number;
    message: string;
    timestamp: Date;
}

class ApiError extends Error {
    constructor(public statusCode: number, message: string) {
        super(message);
        this.name = 'ApiError';
    }
}

// Decorator for logging method calls
function LogMethod(target: any, propertyName: string, descriptor: PropertyDescriptor) {
    const method = descriptor.value;
    
    descriptor.value = async function(...args: any[]) {
        console.log(`Calling ${propertyName} with args:`, args);
        const start = Date.now();
        
        try {
            const result = await method.apply(this, args);
            const duration = Date.now() - start;
            console.log(`${propertyName} completed in ${duration}ms`);
            return result;
        } catch (error) {
            console.error(`${propertyName} failed:`, error);
            throw error;
        }
    };
}

// Generic repository class
class Repository<T extends { id: number }> {
    private items: Map<number, T> = new Map();
    
    @LogMethod
    async create(item: T): Promise<ApiResponse<T>> {
        this.items.set(item.id, item);
        
        return {
            data: item,
            status: 201,
            message: 'Created successfully',
            timestamp: new Date()
        };
    }
    
    @LogMethod
    async findById(id: number): Promise<ApiResponse<T | null>> {
        const item = this.items.get(id) || null;
        
        if (!item) {
            throw new ApiError(404, `Item with id ${id} not found`);
        }
        
        return {
            data: item,
            status: 200,
            message: 'Found',
            timestamp: new Date()
        };
    }
    
    @LogMethod
    async update(id: number, updates: Partial<T>): Promise<ApiResponse<T>> {
        const existing = this.items.get(id);
        
        if (!existing) {
            throw new ApiError(404, `Item with id ${id} not found`);
        }
        
        const updated = { ...existing, ...updates };
        this.items.set(id, updated);
        
        return {
            data: updated,
            status: 200,
            message: 'Updated successfully',
            timestamp: new Date()
        };
    }
}

// Usage example
interface User {
    id: number;
    name: string;
    email: string;
    role: 'admin' | 'user';
}

async function main() {
    const userRepo = new Repository<User>();
    
    const newUser: User = {
        id: 1,
        name: 'John Doe',
        email: 'john@example.com',
        role: 'user'
    };
    
    const createResponse = await userRepo.create(newUser);
    console.log('Created:', createResponse);
    
    const findResponse = await userRepo.findById(1);
    console.log('Found:', findResponse);
}

main().catch(console.error);</code></pre>
    
    <hr style="margin: 30px 0;">
    
    <h2>Test Summary</h2>
    <p>This page demonstrates Prism.js integration with the following features:</p>
    <ul>
        <li>✅ Syntax highlighting for multiple languages</li>
        <li>✅ Line numbers</li>
        <li>✅ Copy to clipboard functionality</li>
        <li>✅ Language labels</li>
        <li>✅ Responsive design</li>
        <li>✅ Dark/Light theme support</li>
    </ul>
    
    <p><strong>Note:</strong> The copy buttons and other interactive features will appear when the page is loaded with the plugin active.</p>
</div>

<?php get_footer(); ?>