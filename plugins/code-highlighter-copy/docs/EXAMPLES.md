# Примеры использования Code Highlighter Copy

Этот документ содержит практические примеры использования плагина Code Highlighter Copy для различных сценариев и языков программирования.

## 📚 Содержание

1. [Базовые примеры](#базовые-примеры)
2. [Веб-разработка](#веб-разработка) 
3. [Backend разработка](#backend-разработка)
4. [Мобильная разработка](#мобильная-разработка)
5. [Data Science и аналитика](#data-science-и-аналитика)
6. [DevOps и системное администрирование](#devops-и-системное-администрирование)
7. [Продвинутые примеры](#продвинутые-примеры)
8. [Лучшие практики](#лучшие-практики)

---

## Базовые примеры

### Простейший пример использования

Самый простой способ добавить код на страницу:

```
[php]
<?php
echo "Hello, World!";
?>
[/php]
```

**Результат:** Блок PHP кода с подсветкой синтаксиса, кнопкой копирования и возможностью полноэкранного просмотра.

### Многострочный код с комментариями

```
[python]
# Пример простого калькулятора на Python
def calculator(operation, num1, num2):
    """
    Выполняет базовые математические операции
    """
    if operation == '+':
        return num1 + num2
    elif operation == '-':
        return num1 - num2
    elif operation == '*':
        return num1 * num2
    elif operation == '/':
        if num2 != 0:
            return num1 / num2
        else:
            return "Ошибка: деление на ноль!"
    else:
        return "Неизвестная операция"

# Пример использования
result = calculator('+', 10, 5)
print(f"Результат: {result}")
[/python]
```

---

## Веб-разработка

### HTML страница с семантической разметкой

```
[html]
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Современная HTML5 страница</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <nav>
            <ul>
                <li><a href="#home">Главная</a></li>
                <li><a href="#about">О нас</a></li>
                <li><a href="#contact">Контакты</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        <section id="hero">
            <h1>Добро пожаловать на наш сайт</h1>
            <p>Это пример современной HTML5 разметки</p>
        </section>
        
        <article>
            <h2>Статья о веб-разработке</h2>
            <p>Содержание статьи...</p>
        </article>
    </main>
    
    <footer>
        <p>&copy; 2025 Наша компания. Все права защищены.</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>
[/html]
```

### CSS Grid макет с темной темой

```
[css]
/* Современный CSS Grid макет */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --primary-color: #007cba;
    --secondary-color: #e8f4fd;
    --dark-bg: #1a1a1a;
    --light-text: #ffffff;
    --border-radius: 8px;
    --box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.6;
    color: var(--light-text);
    background: var(--dark-bg);
}

.container {
    display: grid;
    grid-template-columns: 250px 1fr;
    grid-template-rows: 80px 1fr 60px;
    grid-template-areas: 
        "sidebar header"
        "sidebar main"
        "sidebar footer";
    min-height: 100vh;
    gap: 20px;
    padding: 20px;
}

.header {
    grid-area: header;
    background: linear-gradient(135deg, var(--primary-color), #005a8b);
    border-radius: var(--border-radius);
    display: flex;
    align-items: center;
    padding: 0 20px;
    box-shadow: var(--box-shadow);
}

.sidebar {
    grid-area: sidebar;
    background: #2c2c2c;
    border-radius: var(--border-radius);
    padding: 20px;
    box-shadow: var(--box-shadow);
}

.main-content {
    grid-area: main;
    background: #333;
    border-radius: var(--border-radius);
    padding: 30px;
    box-shadow: var(--box-shadow);
    overflow-y: auto;
}

.footer {
    grid-area: footer;
    background: #2c2c2c;
    border-radius: var(--border-radius);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--box-shadow);
}

/* Адаптивность */
@media (max-width: 768px) {
    .container {
        grid-template-columns: 1fr;
        grid-template-areas: 
            "header"
            "main"
            "sidebar"
            "footer";
    }
}
[/css]
```

### JavaScript ES6+ с современными возможностями

```
[javascript]
// Современный JavaScript с ES6+ возможностями
class TaskManager {
    constructor() {
        this.tasks = new Map();
        this.nextId = 1;
        this.observers = [];
    }
    
    // Добавление задачи с деструктуризацией
    addTask({ title, description, priority = 'medium', dueDate }) {
        if (!title?.trim()) {
            throw new Error('Название задачи обязательно');
        }
        
        const task = {
            id: this.nextId++,
            title: title.trim(),
            description: description?.trim() || '',
            priority,
            dueDate: dueDate ? new Date(dueDate) : null,
            completed: false,
            createdAt: new Date()
        };
        
        this.tasks.set(task.id, task);
        this.notifyObservers('taskAdded', task);
        return task;
    }
    
    // Получение задач с фильтрацией
    getTasks(filter = {}) {
        const { priority, completed, search } = filter;
        
        return Array.from(this.tasks.values())
            .filter(task => {
                if (priority && task.priority !== priority) return false;
                if (completed !== undefined && task.completed !== completed) return false;
                if (search && !task.title.toLowerCase().includes(search.toLowerCase())) return false;
                return true;
            })
            .sort((a, b) => b.createdAt - a.createdAt);
    }
    
    // Обновление задачи с spread оператором
    updateTask(id, updates) {
        const task = this.tasks.get(id);
        if (!task) {
            throw new Error(`Задача с ID ${id} не найдена`);
        }
        
        const updatedTask = { ...task, ...updates, id };
        this.tasks.set(id, updatedTask);
        this.notifyObservers('taskUpdated', updatedTask);
        return updatedTask;
    }
    
    // Асинхронное удаление с подтверждением
    async deleteTask(id) {
        const task = this.tasks.get(id);
        if (!task) return false;
        
        const confirmed = await this.confirmDeletion(task);
        if (confirmed) {
            this.tasks.delete(id);
            this.notifyObservers('taskDeleted', { id });
            return true;
        }
        return false;
    }
    
    // Паттерн Observer для уведомлений
    addObserver(callback) {
        this.observers.push(callback);
    }
    
    notifyObservers(event, data) {
        this.observers.forEach(callback => {
            try {
                callback(event, data);
            } catch (error) {
                console.error('Ошибка в observer:', error);
            }
        });
    }
    
    // Promise-based подтверждение
    confirmDeletion(task) {
        return new Promise(resolve => {
            const modal = document.createElement('div');
            modal.innerHTML = `
                <div class="confirmation-modal">
                    <h3>Подтверждение удаления</h3>
                    <p>Удалить задачу "${task.title}"?</p>
                    <button class="confirm">Да</button>
                    <button class="cancel">Отмена</button>
                </div>
            `;
            
            modal.querySelector('.confirm').onclick = () => {
                document.body.removeChild(modal);
                resolve(true);
            };
            
            modal.querySelector('.cancel').onclick = () => {
                document.body.removeChild(modal);
                resolve(false);
            };
            
            document.body.appendChild(modal);
        });
    }
    
    // Экспорт данных в JSON
    exportData() {
        return {
            tasks: Array.from(this.tasks.values()),
            exportDate: new Date().toISOString(),
            version: '1.0'
        };
    }
    
    // Импорт данных с валидацией
    async importData(data) {
        if (!data?.tasks || !Array.isArray(data.tasks)) {
            throw new Error('Неверный формат данных');
        }
        
        this.tasks.clear();
        let importedCount = 0;
        
        for (const taskData of data.tasks) {
            try {
                const task = {
                    ...taskData,
                    dueDate: taskData.dueDate ? new Date(taskData.dueDate) : null,
                    createdAt: new Date(taskData.createdAt)
                };
                this.tasks.set(task.id, task);
                this.nextId = Math.max(this.nextId, task.id + 1);
                importedCount++;
            } catch (error) {
                console.warn(`Не удалось импортировать задачу ${taskData.id}:`, error);
            }
        }
        
        this.notifyObservers('dataImported', { count: importedCount });
        return importedCount;
    }
}

// Пример использования
const taskManager = new TaskManager();

// Добавляем наблюдателя для логирования
taskManager.addObserver((event, data) => {
    console.log(`События: ${event}`, data);
});

// Создаем задачи
const task1 = taskManager.addTask({
    title: 'Изучить TypeScript',
    description: 'Пройти курс по TypeScript',
    priority: 'high',
    dueDate: '2025-08-20'
});

const task2 = taskManager.addTask({
    title: 'Написать тесты',
    priority: 'medium'
});

// Получаем задачи с фильтрацией
const highPriorityTasks = taskManager.getTasks({ priority: 'high' });
console.log('Задачи с высоким приоритетом:', highPriorityTasks);

// Обновляем задачу
taskManager.updateTask(task1.id, { completed: true });

// Экспортируем данные
const exportData = taskManager.exportData();
console.log('Экспорт:', exportData);
[/javascript]
```

### TypeScript с типами и интерфейсами

```
[typescript]
// TypeScript с строгой типизацией
interface User {
    id: number;
    name: string;
    email: string;
    role: 'admin' | 'user' | 'guest';
    createdAt: Date;
    preferences?: UserPreferences;
}

interface UserPreferences {
    theme: 'light' | 'dark';
    language: string;
    notifications: {
        email: boolean;
        push: boolean;
        sms: boolean;
    };
}

type CreateUserInput = Omit<User, 'id' | 'createdAt'> & {
    password: string;
};

type UserRole = User['role'];
type NotificationChannel = keyof UserPreferences['notifications'];

// Generic repository pattern
abstract class Repository<T extends { id: number }> {
    protected items: Map<number, T> = new Map();
    protected nextId = 1;
    
    create(data: Omit<T, 'id'>): T {
        const item = { ...data, id: this.nextId++ } as T;
        this.items.set(item.id, item);
        return item;
    }
    
    findById(id: number): T | undefined {
        return this.items.get(id);
    }
    
    findAll(predicate?: (item: T) => boolean): T[] {
        const items = Array.from(this.items.values());
        return predicate ? items.filter(predicate) : items;
    }
    
    update(id: number, updates: Partial<T>): T | undefined {
        const item = this.items.get(id);
        if (!item) return undefined;
        
        const updated = { ...item, ...updates, id };
        this.items.set(id, updated);
        return updated;
    }
    
    delete(id: number): boolean {
        return this.items.delete(id);
    }
    
    count(): number {
        return this.items.size;
    }
}

// User service с бизнес-логикой
class UserService extends Repository<User> {
    constructor(private readonly emailService: EmailService) {
        super();
    }
    
    async createUser(input: CreateUserInput): Promise<User> {
        // Валидация email
        if (!this.isValidEmail(input.email)) {
            throw new Error('Неверный формат email');
        }
        
        // Проверка уникальности email
        const existingUser = this.findAll(u => u.email === input.email);
        if (existingUser.length > 0) {
            throw new Error('Пользователь с таким email уже существует');
        }
        
        // Хеширование пароля (имитация)
        const hashedPassword = await this.hashPassword(input.password);
        
        const { password, ...userData } = input;
        const user = this.create({
            ...userData,
            createdAt: new Date(),
            preferences: this.getDefaultPreferences()
        });
        
        // Отправка приветственного email
        await this.emailService.sendWelcomeEmail(user);
        
        return user;
    }
    
    updateUserPreferences(
        userId: number,
        preferences: Partial<UserPreferences>
    ): User | undefined {
        const user = this.findById(userId);
        if (!user) return undefined;
        
        const updatedPreferences = {
            ...user.preferences,
            ...preferences
        };
        
        return this.update(userId, { preferences: updatedPreferences });
    }
    
    getUsersByRole(role: UserRole): User[] {
        return this.findAll(user => user.role === role);
    }
    
    async sendNotification(
        userId: number,
        channel: NotificationChannel,
        message: string
    ): Promise<boolean> {
        const user = this.findById(userId);
        if (!user?.preferences?.notifications[channel]) {
            return false;
        }
        
        switch (channel) {
            case 'email':
                return this.emailService.sendEmail(user.email, message);
            case 'push':
                return this.sendPushNotification(user, message);
            case 'sms':
                return this.sendSMSNotification(user, message);
        }
    }
    
    // Статистика пользователей
    getStatistics(): UserStatistics {
        const users = this.findAll();
        const roleStats = users.reduce((acc, user) => {
            acc[user.role] = (acc[user.role] || 0) + 1;
            return acc;
        }, {} as Record<UserRole, number>);
        
        return {
            totalUsers: users.length,
            roleDistribution: roleStats,
            recentUsers: users
                .filter(u => this.isRecent(u.createdAt))
                .length,
            activeUsers: users
                .filter(u => u.preferences !== undefined)
                .length
        };
    }
    
    private isValidEmail(email: string): boolean {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    private async hashPassword(password: string): Promise<string> {
        // Имитация хеширования
        return `hashed_${password}_${Date.now()}`;
    }
    
    private getDefaultPreferences(): UserPreferences {
        return {
            theme: 'light',
            language: 'ru',
            notifications: {
                email: true,
                push: false,
                sms: false
            }
        };
    }
    
    private isRecent(date: Date): boolean {
        const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        return date > weekAgo;
    }
    
    private async sendPushNotification(user: User, message: string): Promise<boolean> {
        // Имитация отправки push уведомления
        console.log(`Push для ${user.name}: ${message}`);
        return true;
    }
    
    private async sendSMSNotification(user: User, message: string): Promise<boolean> {
        // Имитация отправки SMS
        console.log(`SMS для ${user.name}: ${message}`);
        return true;
    }
}

interface UserStatistics {
    totalUsers: number;
    roleDistribution: Record<UserRole, number>;
    recentUsers: number;
    activeUsers: number;
}

// Email service interface
interface EmailService {
    sendEmail(to: string, message: string): Promise<boolean>;
    sendWelcomeEmail(user: User): Promise<boolean>;
}

// Mock email service implementation
class MockEmailService implements EmailService {
    async sendEmail(to: string, message: string): Promise<boolean> {
        console.log(`Email для ${to}: ${message}`);
        return true;
    }
    
    async sendWelcomeEmail(user: User): Promise<boolean> {
        const message = `Добро пожаловать, ${user.name}! Ваш аккаунт успешно создан.`;
        return this.sendEmail(user.email, message);
    }
}

// Пример использования
async function main() {
    const emailService = new MockEmailService();
    const userService = new UserService(emailService);
    
    try {
        // Создание пользователя
        const newUser = await userService.createUser({
            name: 'Иван Иванов',
            email: 'ivan@example.com',
            role: 'user',
            password: 'securePassword123'
        });
        
        console.log('Создан пользователь:', newUser);
        
        // Обновление настроек
        const updatedUser = userService.updateUserPreferences(newUser.id, {
            theme: 'dark',
            notifications: {
                email: true,
                push: true,
                sms: false
            }
        });
        
        console.log('Обновленный пользователь:', updatedUser);
        
        // Отправка уведомления
        await userService.sendNotification(newUser.id, 'email', 'Тестовое уведомление');
        
        // Статистика
        const stats = userService.getStatistics();
        console.log('Статистика:', stats);
        
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

main();
[/typescript]
```

---

## Backend разработка

### PHP Laravel Controller

```
[php]
<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\CreateUserRequest;
use App\Http\Requests\UpdateUserRequest;
use App\Http\Resources\UserResource;
use App\Models\User;
use App\Services\UserService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\AnonymousResourceCollection;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

/**
 * @group User Management
 * 
 * API для управления пользователями системы
 */
class UserController extends Controller
{
    public function __construct(
        private readonly UserService $userService
    ) {
        $this->middleware('auth:sanctum');
        $this->middleware('can:manage-users')->except(['show', 'profile']);
    }

    /**
     * Получить список пользователей
     * 
     * @queryParam page integer Номер страницы. Example: 1
     * @queryParam per_page integer Количество записей на странице. Example: 15
     * @queryParam search string Поиск по имени или email. Example: john
     * @queryParam role string Фильтр по роли. Example: admin
     * @queryParam status string Фильтр по статусу. Example: active
     */
    public function index(Request $request): AnonymousResourceCollection
    {
        $validated = $request->validate([
            'page' => 'integer|min:1',
            'per_page' => 'integer|min:1|max:100',
            'search' => 'string|max:255',
            'role' => 'string|in:admin,user,moderator',
            'status' => 'string|in:active,inactive,banned',
            'sort_by' => 'string|in:name,email,created_at',
            'sort_direction' => 'string|in:asc,desc'
        ]);

        $cacheKey = 'users_list_' . md5(serialize($validated));
        
        $users = Cache::remember($cacheKey, 300, function () use ($validated) {
            return $this->userService->getPaginatedUsers($validated);
        });

        Log::info('Users list accessed', [
            'user_id' => auth()->id(),
            'filters' => $validated
        ]);

        return UserResource::collection($users);
    }

    /**
     * Создать нового пользователя
     * 
     * @bodyParam name string required Имя пользователя. Example: John Doe
     * @bodyParam email string required Email адрес. Example: john@example.com
     * @bodyParam password string required Пароль (минимум 8 символов). Example: password123
     * @bodyParam role string required Роль пользователя. Example: user
     * @bodyParam phone string Номер телефона. Example: +7(999)123-45-67
     */
    public function store(CreateUserRequest $request): JsonResponse
    {
        try {
            $user = $this->userService->createUser($request->validated());

            Log::info('User created', [
                'created_by' => auth()->id(),
                'user_id' => $user->id,
                'user_email' => $user->email
            ]);

            // Очищаем кеш списка пользователей
            Cache::tags(['users'])->flush();

            return response()->json([
                'message' => 'Пользователь успешно создан',
                'data' => new UserResource($user)
            ], 201);

        } catch (\Illuminate\Validation\ValidationException $e) {
            return response()->json([
                'message' => 'Ошибка валидации',
                'errors' => $e->errors()
            ], 422);

        } catch (\Exception $e) {
            Log::error('Error creating user', [
                'error' => $e->getMessage(),
                'user_id' => auth()->id(),
                'request_data' => $request->safe()->except(['password'])
            ]);

            return response()->json([
                'message' => 'Произошла ошибка при создании пользователя'
            ], 500);
        }
    }

    /**
     * Показать информацию о пользователе
     * 
     * @urlParam user integer required ID пользователя. Example: 1
     */
    public function show(User $user): JsonResponse
    {
        $this->authorize('view', $user);

        // Загружаем связанные данные
        $user->load(['profile', 'roles.permissions', 'lastActivity']);

        return response()->json([
            'data' => new UserResource($user)
        ]);
    }

    /**
     * Обновить информацию о пользователе
     * 
     * @urlParam user integer required ID пользователя. Example: 1
     */
    public function update(UpdateUserRequest $request, User $user): JsonResponse
    {
        $this->authorize('update', $user);

        try {
            $updatedUser = $this->userService->updateUser($user, $request->validated());

            Log::info('User updated', [
                'updated_by' => auth()->id(),
                'user_id' => $user->id,
                'changes' => $request->validated()
            ]);

            // Очищаем кеш
            Cache::tags(['users', "user_{$user->id}"])->flush();

            return response()->json([
                'message' => 'Информация о пользователе обновлена',
                'data' => new UserResource($updatedUser)
            ]);

        } catch (\Exception $e) {
            Log::error('Error updating user', [
                'error' => $e->getMessage(),
                'user_id' => $user->id,
                'updated_by' => auth()->id()
            ]);

            return response()->json([
                'message' => 'Произошла ошибка при обновлении данных'
            ], 500);
        }
    }

    /**
     * Удалить пользователя
     * 
     * @urlParam user integer required ID пользователя. Example: 1
     */
    public function destroy(User $user): JsonResponse
    {
        $this->authorize('delete', $user);

        try {
            // Проверяем, может ли пользователь быть удален
            if (!$this->userService->canDeleteUser($user)) {
                return response()->json([
                    'message' => 'Этот пользователь не может быть удален'
                ], 403);
            }

            $this->userService->deleteUser($user);

            Log::warning('User deleted', [
                'deleted_by' => auth()->id(),
                'user_id' => $user->id,
                'user_email' => $user->email
            ]);

            // Очищаем кеш
            Cache::tags(['users', "user_{$user->id}"])->flush();

            return response()->json([
                'message' => 'Пользователь удален'
            ]);

        } catch (\Exception $e) {
            Log::error('Error deleting user', [
                'error' => $e->getMessage(),
                'user_id' => $user->id,
                'deleted_by' => auth()->id()
            ]);

            return response()->json([
                'message' => 'Произошла ошибка при удалении пользователя'
            ], 500);
        }
    }

    /**
     * Получить профиль текущего пользователя
     */
    public function profile(): JsonResponse
    {
        $user = auth()->user();
        $user->load(['profile', 'preferences', 'subscriptions']);

        return response()->json([
            'data' => new UserResource($user)
        ]);
    }

    /**
     * Заблокировать пользователя
     * 
     * @urlParam user integer required ID пользователя. Example: 1
     * @bodyParam reason string required Причина блокировки. Example: Нарушение правил
     * @bodyParam duration integer Продолжительность в днях (0 = навсегда). Example: 30
     */
    public function ban(Request $request, User $user): JsonResponse
    {
        $this->authorize('ban', $user);

        $validated = $request->validate([
            'reason' => 'required|string|max:500',
            'duration' => 'integer|min:0|max:365'
        ]);

        try {
            $this->userService->banUser($user, $validated);

            Log::warning('User banned', [
                'banned_by' => auth()->id(),
                'user_id' => $user->id,
                'reason' => $validated['reason'],
                'duration' => $validated['duration'] ?? 0
            ]);

            return response()->json([
                'message' => 'Пользователь заблокирован'
            ]);

        } catch (\Exception $e) {
            Log::error('Error banning user', [
                'error' => $e->getMessage(),
                'user_id' => $user->id
            ]);

            return response()->json([
                'message' => 'Произошла ошибка при блокировке'
            ], 500);
        }
    }

    /**
     * Разблокировать пользователя
     * 
     * @urlParam user integer required ID пользователя. Example: 1
     */
    public function unban(User $user): JsonResponse
    {
        $this->authorize('unban', $user);

        try {
            $this->userService->unbanUser($user);

            Log::info('User unbanned', [
                'unbanned_by' => auth()->id(),
                'user_id' => $user->id
            ]);

            return response()->json([
                'message' => 'Пользователь разблокирован'
            ]);

        } catch (\Exception $e) {
            return response()->json([
                'message' => 'Произошла ошибка при разблокировке'
            ], 500);
        }
    }

    /**
     * Экспорт пользователей в CSV
     * 
     * @queryParam format string Формат экспорта. Example: csv
     */
    public function export(Request $request)
    {
        $this->authorize('export-users');

        $format = $request->get('format', 'csv');
        
        try {
            return $this->userService->exportUsers($format);

        } catch (\Exception $e) {
            Log::error('Error exporting users', [
                'error' => $e->getMessage(),
                'user_id' => auth()->id(),
                'format' => $format
            ]);

            return response()->json([
                'message' => 'Произошла ошибка при экспорте данных'
            ], 500);
        }
    }

    /**
     * Статистика пользователей
     */
    public function stats(): JsonResponse
    {
        $this->authorize('view-user-stats');

        $stats = Cache::remember('user_stats', 3600, function () {
            return $this->userService->getUserStatistics();
        });

        return response()->json([
            'data' => $stats
        ]);
    }
}
[/php]
```

### Python Django REST API

```
[python]
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView

import json
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, UserProfile, ActivityLog
from .serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer
from .services import UserService, EmailService, NotificationService
from .utils import validate_email, hash_password, generate_token

logger = logging.getLogger(__name__)

class UserAPIView(APIView):
    """
    API для управления пользователями
    """
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Определяем разрешения в зависимости от метода"""
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get(self, request, user_id=None):
        """
        Получить пользователя или список пользователей
        """
        try:
            if user_id:
                # Получение конкретного пользователя
                user = get_object_or_404(User, id=user_id)
                
                # Проверяем права доступа
                if not request.user.is_staff and request.user.id != user.id:
                    return Response(
                        {'error': 'Недостаточно прав доступа'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                serializer = UserSerializer(user)
                return Response({
                    'success': True,
                    'data': serializer.data
                })
            
            else:
                # Получение списка пользователей
                return self._get_users_list(request)
                
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя: {str(e)}")
            return Response(
                {'error': 'Внутренняя ошибка сервера'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_users_list(self, request) -> Response:
        """Получить список пользователей с фильтрацией и пагинацией"""
        # Параметры запроса
        page = int(request.GET.get('page', 1))
        per_page = min(int(request.GET.get('per_page', 20)), 100)
        search = request.GET.get('search', '').strip()
        role = request.GET.get('role', '').strip()
        is_active = request.GET.get('is_active')
        sort_by = request.GET.get('sort_by', 'created_at')
        sort_order = request.GET.get('sort_order', 'desc')
        
        # Кеширование
        cache_key = f"users_list_{page}_{per_page}_{search}_{role}_{is_active}_{sort_by}_{sort_order}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return Response(cached_result)
        
        # Построение queryset
        queryset = User.objects.select_related('profile').prefetch_related('groups')
        
        # Фильтрация
        if search:
            queryset = queryset.filter(
                models.Q(username__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search)
            )
        
        if role:
            queryset = queryset.filter(groups__name=role)
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Сортировка
        order_prefix = '-' if sort_order == 'desc' else ''
        valid_sort_fields = ['username', 'email', 'created_at', 'last_login']
        
        if sort_by in valid_sort_fields:
            queryset = queryset.order_by(f"{order_prefix}{sort_by}")
        
        # Пагинация
        paginator = Paginator(queryset, per_page)
        
        try:
            users_page = paginator.page(page)
        except PageNotAnInteger:
            users_page = paginator.page(1)
        except EmptyPage:
            users_page = paginator.page(paginator.num_pages)
        
        # Сериализация
        serializer = UserSerializer(users_page.object_list, many=True)
        
        result = {
            'success': True,
            'data': serializer.data,
            'pagination': {
                'current_page': users_page.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'per_page': per_page,
                'has_next': users_page.has_next(),
                'has_previous': users_page.has_previous()
            }
        }
        
        # Кешируем результат на 5 минут
        cache.set(cache_key, result, 300)
        
        return Response(result)
    
    def post(self, request):
        """Создать нового пользователя"""
        try:
            serializer = UserCreateSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Создаем пользователя
                user_data = serializer.validated_data
                password = user_data.pop('password')
                
                user = User.objects.create_user(
                    password=password,
                    **user_data
                )
                
                # Создаем профиль пользователя
                UserProfile.objects.create(
                    user=user,
                    phone=request.data.get('phone', ''),
                    date_of_birth=request.data.get('date_of_birth')
                )
                
                # Логируем создание
                ActivityLog.objects.create(
                    user=request.user,
                    action='user_created',
                    target_user=user,
                    details=f"Создан пользователь {user.username}"
                )
                
                # Отправляем приветственное письмо
                EmailService.send_welcome_email(user)
                
                # Очищаем кеш
                cache.delete_pattern("users_list_*")
                
                logger.info(f"Создан пользователь {user.username} (ID: {user.id})")
                
                return Response({
                    'success': True,
                    'message': 'Пользователь успешно создан',
                    'data': UserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
                
        except ValidationError as e:
            return Response({
                'success': False,
                'errors': {'validation': str(e)}
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {str(e)}")
            return Response({
                'success': False,
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, user_id):
        """Обновить данные пользователя"""
        try:
            user = get_object_or_404(User, id=user_id)
            
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Сохраняем изменения
                old_data = {
                    'username': user.username,
                    'email': user.email,
                    'is_active': user.is_active
                }
                
                updated_user = serializer.save()
                
                # Обновляем профиль если нужно
                profile_data = {}
                if 'phone' in request.data:
                    profile_data['phone'] = request.data['phone']
                if 'date_of_birth' in request.data:
                    profile_data['date_of_birth'] = request.data['date_of_birth']
                
                if profile_data:
                    UserProfile.objects.filter(user=user).update(**profile_data)
                
                # Логируем изменения
                changes = []
                for field, old_value in old_data.items():
                    new_value = getattr(updated_user, field)
                    if old_value != new_value:
                        changes.append(f"{field}: {old_value} -> {new_value}")
                
                if changes:
                    ActivityLog.objects.create(
                        user=request.user,
                        action='user_updated',
                        target_user=user,
                        details=f"Изменения: {', '.join(changes)}"
                    )
                
                # Очищаем кеш
                cache.delete_pattern("users_list_*")
                cache.delete(f"user_{user_id}")
                
                return Response({
                    'success': True,
                    'message': 'Данные пользователя обновлены',
                    'data': UserSerializer(updated_user).data
                })
                
        except Exception as e:
            logger.error(f"Ошибка при обновлении пользователя {user_id}: {str(e)}")
            return Response({
                'success': False,
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, user_id):
        """Удалить пользователя"""
        try:
            user = get_object_or_404(User, id=user_id)
            
            # Проверяем, можно ли удалить пользователя
            if user.is_superuser:
                return Response({
                    'success': False,
                    'error': 'Нельзя удалить суперпользователя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            if user.id == request.user.id:
                return Response({
                    'success': False,
                    'error': 'Нельзя удалить самого себя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Деактивируем вместо удаления для сохранения данных
            with transaction.atomic():
                user.is_active = False
                user.username = f"deleted_{user.id}_{user.username}"
                user.email = f"deleted_{user.id}_{user.email}"
                user.save()
                
                # Логируем удаление
                ActivityLog.objects.create(
                    user=request.user,
                    action='user_deleted',
                    target_user=user,
                    details=f"Удален пользователь {user.username}"
                )
                
                # Отправляем уведомление о деактивации
                NotificationService.send_deactivation_notice(user)
                
                # Очищаем кеш
                cache.delete_pattern("users_list_*")
                cache.delete(f"user_{user_id}")
                
                logger.warning(f"Удален пользователь {user.username} (ID: {user_id})")
                
                return Response({
                    'success': True,
                    'message': 'Пользователь удален'
                })
                
        except Exception as e:
            logger.error(f"Ошибка при удалении пользователя {user_id}: {str(e)}")
            return Response({
                'success': False,
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])
def user_login(request):
    """Авторизация пользователя"""
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        remember_me = request.data.get('remember_me', False)
        
        if not username or not password:
            return Response({
                'success': False,
                'error': 'Логин и пароль обязательны'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем количество попыток входа
        login_attempts_key = f"login_attempts_{username}"
        attempts = cache.get(login_attempts_key, 0)
        
        if attempts >= 5:
            return Response({
                'success': False,
                'error': 'Слишком много попыток входа. Попробуйте позже.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                
                # Обновляем последний вход
                user.last_login = datetime.now()
                user.save(update_fields=['last_login'])
                
                # Устанавливаем время жизни сессии
                if not remember_me:
                    request.session.set_expiry(0)  # До закрытия браузера
                else:
                    request.session.set_expiry(1209600)  # 2 недели
                
                # Логируем вход
                ActivityLog.objects.create(
                    user=user,
                    action='user_login',
                    details=f"Вход с IP {request.META.get('REMOTE_ADDR')}"
                )
                
                # Очищаем счетчик попыток
                cache.delete(login_attempts_key)
                
                return Response({
                    'success': True,
                    'message': 'Успешная авторизация',
                    'user': UserSerializer(user).data
                })
            else:
                return Response({
                    'success': False,
                    'error': 'Аккаунт деактивирован'
                }, status=status.HTTP_403_FORBIDDEN)
        else:
            # Увеличиваем счетчик попыток
            cache.set(login_attempts_key, attempts + 1, 300)  # 5 минут
            
            return Response({
                'success': False,
                'error': 'Неверный логин или пароль'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        logger.error(f"Ошибка при авторизации: {str(e)}")
        return Response({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    """Выход из системы"""
    try:
        # Логируем выход
        ActivityLog.objects.create(
            user=request.user,
            action='user_logout',
            details="Выход из системы"
        )
        
        logout(request)
        
        return Response({
            'success': True,
            'message': 'Вы успешно вышли из системы'
        })
        
    except Exception as e:
        logger.error(f"Ошибка при выходе: {str(e)}")
        return Response({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_statistics(request):
    """Статистика пользователей"""
    try:
        cache_key = "user_statistics"
        stats = cache.get(cache_key)
        
        if not stats:
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            
            # Пользователи за последние 30 дней
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_users = User.objects.filter(
                date_joined__gte=thirty_days_ago
            ).count()
            
            # Пользователи онлайн (активность за последние 15 минут)
            fifteen_minutes_ago = datetime.now() - timedelta(minutes=15)
            online_users = User.objects.filter(
                last_login__gte=fifteen_minutes_ago
            ).count()
            
            # Статистика по ролям
            from django.contrib.auth.models import Group
            role_stats = {}
            for group in Group.objects.all():
                role_stats[group.name] = group.user_set.count()
            
            stats = {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': total_users - active_users,
                'recent_users': recent_users,
                'online_users': online_users,
                'role_distribution': role_stats,
                'generated_at': datetime.now().isoformat()
            }
            
            # Кешируем на 15 минут
            cache.set(cache_key, stats, 900)
        
        return Response({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {str(e)}")
        return Response({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
[/python]
```

---

## Мобильная разработка

### Swift iOS приложение

```
[swift]
import SwiftUI
import Combine
import Foundation

// MARK: - Models

struct User: Codable, Identifiable {
    let id: Int
    let username: String
    let email: String
    let firstName: String
    let lastName: String
    let avatar: String?
    let isActive: Bool
    let createdAt: Date
    
    var fullName: String {
        "\(firstName) \(lastName)".trimmingCharacters(in: .whitespaces)
    }
    
    var initials: String {
        let firstInitial = firstName.first?.uppercased() ?? ""
        let lastInitial = lastName.first?.uppercased() ?? ""
        return "\(firstInitial)\(lastInitial)"
    }
}

struct LoginRequest: Codable {
    let username: String
    let password: String
    let rememberMe: Bool
}

struct ApiResponse<T: Codable>: Codable {
    let success: Bool
    let data: T?
    let message: String?
    let errors: [String: [String]]?
}

// MARK: - Network Service

class NetworkService: ObservableObject {
    static let shared = NetworkService()
    private let baseURL = "https://api.example.com"
    private let session = URLSession.shared
    
    private init() {}
    
    private func createRequest(
        url: URL,
        method: HTTPMethod,
        body: Data? = nil
    ) -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(AuthManager.shared.token ?? "")", forHTTPHeaderField: "Authorization")
        request.httpBody = body
        return request
    }
    
    func request<T: Codable>(
        endpoint: String,
        method: HTTPMethod = .GET,
        body: Codable? = nil,
        responseType: T.Type
    ) -> AnyPublisher<T, NetworkError> {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else {
            return Fail(error: NetworkError.invalidURL)
                .eraseToAnyPublisher()
        }
        
        var requestBody: Data?
        if let body = body {
            do {
                requestBody = try JSONEncoder().encode(body)
            } catch {
                return Fail(error: NetworkError.encodingError)
                    .eraseToAnyPublisher()
            }
        }
        
        let request = createRequest(url: url, method: method, body: requestBody)
        
        return session.dataTaskPublisher(for: request)
            .map(\.data)
            .decode(type: ApiResponse<T>.self, decoder: JSONDecoder())
            .compactMap { response in
                if response.success {
                    return response.data
                } else {
                    throw NetworkError.apiError(response.message ?? "Unknown error")
                }
            }
            .mapError { error in
                if let networkError = error as? NetworkError {
                    return networkError
                } else if error is DecodingError {
                    return NetworkError.decodingError
                } else {
                    return NetworkError.networkError(error.localizedDescription)
                }
            }
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
}

enum HTTPMethod: String {
    case GET = "GET"
    case POST = "POST"
    case PUT = "PUT"
    case DELETE = "DELETE"
}

enum NetworkError: Error, LocalizedError {
    case invalidURL
    case encodingError
    case decodingError
    case networkError(String)
    case apiError(String)
    
    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Неверный URL"
        case .encodingError:
            return "Ошибка кодирования данных"
        case .decodingError:
            return "Ошибка декодирования ответа"
        case .networkError(let message):
            return "Сетевая ошибка: \(message)"
        case .apiError(let message):
            return "Ошибка API: \(message)"
        }
    }
}

// MARK: - Auth Manager

class AuthManager: ObservableObject {
    static let shared = AuthManager()
    
    @Published var isAuthenticated = false
    @Published var currentUser: User?
    @Published var token: String?
    
    private let keychain = KeychainHelper()
    private var cancellables = Set<AnyCancellable>()
    
    private init() {
        loadAuthState()
    }
    
    func login(username: String, password: String, rememberMe: Bool = false) -> AnyPublisher<Void, NetworkError> {
        let request = LoginRequest(username: username, password: password, rememberMe: rememberMe)
        
        return NetworkService.shared.request(
            endpoint: "/auth/login",
            method: .POST,
            body: request,
            responseType: LoginResponse.self
        )
        .map { [weak self] response in
            self?.handleLoginSuccess(response: response, rememberMe: rememberMe)
        }
        .eraseToAnyPublisher()
    }
    
    func logout() {
        NetworkService.shared.request(
            endpoint: "/auth/logout",
            method: .POST,
            responseType: EmptyResponse.self
        )
        .sink(
            receiveCompletion: { _ in },
            receiveValue: { [weak self] _ in
                self?.clearAuthState()
            }
        )
        .store(in: &cancellables)
        
        // Очищаем состояние независимо от ответа сервера
        clearAuthState()
    }
    
    func refreshToken() -> AnyPublisher<Void, NetworkError> {
        guard let refreshToken = keychain.get("refresh_token") else {
            return Fail(error: NetworkError.apiError("No refresh token"))
                .eraseToAnyPublisher()
        }
        
        return NetworkService.shared.request(
            endpoint: "/auth/refresh",
            method: .POST,
            body: ["refresh_token": refreshToken],
            responseType: LoginResponse.self
        )
        .map { [weak self] response in
            self?.handleTokenRefresh(response: response)
        }
        .eraseToAnyPublisher()
    }
    
    private func handleLoginSuccess(response: LoginResponse, rememberMe: Bool) {
        self.token = response.accessToken
        self.currentUser = response.user
        self.isAuthenticated = true
        
        // Сохраняем токены в keychain
        keychain.set(response.accessToken, forKey: "access_token")
        keychain.set(response.refreshToken, forKey: "refresh_token")
        
        // Сохраняем настройку "запомнить меня"
        UserDefaults.standard.set(rememberMe, forKey: "remember_me")
        
        // Планируем обновление токена
        scheduleTokenRefresh()
    }
    
    private func handleTokenRefresh(response: LoginResponse) {
        self.token = response.accessToken
        keychain.set(response.accessToken, forKey: "access_token")
        keychain.set(response.refreshToken, forKey: "refresh_token")
    }
    
    private func clearAuthState() {
        self.token = nil
        self.currentUser = nil
        self.isAuthenticated = false
        
        keychain.delete("access_token")
        keychain.delete("refresh_token")
        UserDefaults.standard.removeObject(forKey: "remember_me")
    }
    
    private func loadAuthState() {
        if let token = keychain.get("access_token") {
            self.token = token
            
            // Проверяем валидность токена
            validateToken()
        }
    }
    
    private func validateToken() {
        NetworkService.shared.request(
            endpoint: "/auth/me",
            method: .GET,
            responseType: User.self
        )
        .sink(
            receiveCompletion: { [weak self] completion in
                switch completion {
                case .failure:
                    // Токен невалиден, пробуем обновить
                    self?.refreshToken()
                        .sink(
                            receiveCompletion: { _ in },
                            receiveValue: { }
                        )
                        .store(in: &self?.cancellables ?? Set<AnyCancellable>())
                case .finished:
                    break
                }
            },
            receiveValue: { [weak self] user in
                self?.currentUser = user
                self?.isAuthenticated = true
            }
        )
        .store(in: &cancellables)
    }
    
    private func scheduleTokenRefresh() {
        // Обновляем токен каждые 50 минут (если токен живет час)
        Timer.scheduledTimer(withTimeInterval: 3000, repeats: true) { [weak self] _ in
            self?.refreshToken()
                .sink(
                    receiveCompletion: { _ in },
                    receiveValue: { }
                )
                .store(in: &self?.cancellables ?? Set<AnyCancellable>())
        }
    }
}

struct LoginResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let user: User
}

struct EmptyResponse: Codable {}

// MARK: - Keychain Helper

class KeychainHelper {
    func set(_ value: String, forKey key: String) {
        let data = value.data(using: .utf8)!
        let query = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data
        ] as [String: Any]
        
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }
    
    func get(_ key: String) -> String? {
        let query = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: kCFBooleanTrue!,
            kSecMatchLimit as String: kSecMatchLimitOne
        ] as [String: Any]
        
        var dataTypeRef: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &dataTypeRef)
        
        if status == noErr,
           let data = dataTypeRef as? Data,
           let value = String(data: data, encoding: .utf8) {
            return value
        }
        
        return nil
    }
    
    func delete(_ key: String) {
        let query = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key
        ] as [String: Any]
        
        SecItemDelete(query as CFDictionary)
    }
}

// MARK: - Views

struct ContentView: View {
    @StateObject private var authManager = AuthManager.shared
    
    var body: some View {
        Group {
            if authManager.isAuthenticated {
                MainTabView()
            } else {
                LoginView()
            }
        }
        .animation(.easeInOut, value: authManager.isAuthenticated)
    }
}

struct LoginView: View {
    @StateObject private var authManager = AuthManager.shared
    @State private var username = ""
    @State private var password = ""
    @State private var rememberMe = false
    @State private var isLoading = false
    @State private var errorMessage = ""
    @State private var showError = false
    
    var body: some View {
        NavigationView {
            VStack(spacing: 30) {
                // Логотип
                Image(systemName: "person.circle.fill")
                    .font(.system(size: 80))
                    .foregroundColor(.blue)
                    .padding(.top, 50)
                
                Text("Добро пожаловать")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                // Форма входа
                VStack(spacing: 20) {
                    // Поле username
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Имя пользователя")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        TextField("Введите логин", text: $username)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                    }
                    
                    // Поле password
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Пароль")
                            .font(.headline)
                            .foregroundColor(.secondary)
                        
                        SecureField("Введите пароль", text: $password)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    // Чекбокс "Запомнить меня"
                    HStack {
                        Toggle("Запомнить меня", isOn: $rememberMe)
                            .font(.subheadline)
                        
                        Spacer()
                        
                        Button("Забыли пароль?") {
                            // Обработка восстановления пароля
                        }
                        .font(.subheadline)
                        .foregroundColor(.blue)
                    }
                }
                .padding(.horizontal, 20)
                
                // Кнопка входа
                Button(action: login) {
                    HStack {
                        if isLoading {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                .scaleEffect(0.8)
                        }
                        
                        Text("Войти")
                            .fontWeight(.semibold)
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(loginButtonColor)
                    )
                    .foregroundColor(.white)
                }
                .disabled(!isFormValid || isLoading)
                .padding(.horizontal, 20)
                
                Spacer()
                
                // Ссылка на регистрацию
                HStack {
                    Text("Нет аккаунта?")
                        .foregroundColor(.secondary)
                    
                    Button("Зарегистрироваться") {
                        // Переход к регистрации
                    }
                    .foregroundColor(.blue)
                    .fontWeight(.medium)
                }
                .padding(.bottom, 30)
            }
            .navigationBarHidden(true)
            .alert("Ошибка", isPresented: $showError) {
                Button("OK") { showError = false }
            } message: {
                Text(errorMessage)
            }
        }
    }
    
    private var isFormValid: Bool {
        !username.isEmpty && !password.isEmpty
    }
    
    private var loginButtonColor: Color {
        isFormValid ? .blue : .gray
    }
    
    private func login() {
        guard isFormValid else { return }
        
        isLoading = true
        errorMessage = ""
        
        authManager.login(username: username, password: password, rememberMe: rememberMe)
            .sink(
                receiveCompletion: { [self] completion in
                    isLoading = false
                    
                    switch completion {
                    case .failure(let error):
                        errorMessage = error.localizedDescription
                        showError = true
                    case .finished:
                        break
                    }
                },
                receiveValue: {
                    // Успешная авторизация - состояние изменится автоматически
                }
            )
            .store(in: &authManager.cancellables)
    }
}

struct MainTabView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem {
                    Image(systemName: "house")
                    Text("Главная")
                }
            
            ProfileView()
                .tabItem {
                    Image(systemName: "person")
                    Text("Профиль")
                }
            
            SettingsView()
                .tabItem {
                    Image(systemName: "gearshape")
                    Text("Настройки")
                }
        }
    }
}

struct HomeView: View {
    @StateObject private var authManager = AuthManager.shared
    
    var body: some View {
        NavigationView {
            VStack {
                if let user = authManager.currentUser {
                    Text("Привет, \(user.firstName)!")
                        .font(.largeTitle)
                        .padding()
                    
                    // Здесь основной контент приложения
                    
                } else {
                    ProgressView("Загрузка...")
                }
                
                Spacer()
            }
            .navigationTitle("Главная")
        }
    }
}

struct ProfileView: View {
    @StateObject private var authManager = AuthManager.shared
    
    var body: some View {
        NavigationView {
            VStack {
                if let user = authManager.currentUser {
                    // Аватар пользователя
                    AsyncImage(url: URL(string: user.avatar ?? "")) { image in
                        image
                            .resizable()
                            .aspectRatio(contentMode: .fill)
                    } placeholder: {
                        Circle()
                            .fill(Color.blue.opacity(0.3))
                            .overlay(
                                Text(user.initials)
                                    .font(.system(size: 40, weight: .semibold))
                                    .foregroundColor(.blue)
                            )
                    }
                    .frame(width: 120, height: 120)
                    .clipShape(Circle())
                    .padding()
                    
                    Text(user.fullName)
                        .font(.title)
                        .fontWeight(.semibold)
                    
                    Text(user.email)
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                    
                    // Информация о пользователе
                    VStack(spacing: 16) {
                        ProfileRow(title: "Имя пользователя", value: user.username)
                        ProfileRow(title: "Email", value: user.email)
                        ProfileRow(title: "Дата регистрации", value: DateFormatter.localizedString(from: user.createdAt, dateStyle: .medium, timeStyle: .none))
                    }
                    .padding()
                    
                    Spacer()
                    
                    // Кнопка выхода
                    Button(action: {
                        authManager.logout()
                    }) {
                        Text("Выйти")
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.red)
                            .cornerRadius(12)
                    }
                    .padding()
                }
            }
            .navigationTitle("Профиль")
        }
    }
}

struct ProfileRow: View {
    let title: String
    let value: String
    
    var body: some View {
        HStack {
            Text(title)
                .fontWeight(.medium)
                .foregroundColor(.secondary)
            
            Spacer()
            
            Text(value)
                .fontWeight(.regular)
        }
        .padding(.vertical, 4)
    }
}

struct SettingsView: View {
    @StateObject private var authManager = AuthManager.shared
    
    var body: some View {
        NavigationView {
            List {
                Section("Аккаунт") {
                    NavigationLink(destination: EditProfileView()) {
                        Label("Редактировать профиль", systemImage: "person.crop.circle")
                    }
                    
                    NavigationLink(destination: ChangePasswordView()) {
                        Label("Изменить пароль", systemImage: "key")
                    }
                }
                
                Section("Приложение") {
                    NavigationLink(destination: NotificationSettingsView()) {
                        Label("Уведомления", systemImage: "bell")
                    }
                    
                    NavigationLink(destination: AboutView()) {
                        Label("О приложении", systemImage: "info.circle")
                    }
                }
                
                Section {
                    Button(action: {
                        authManager.logout()
                    }) {
                        Label("Выйти", systemImage: "power")
                            .foregroundColor(.red)
                    }
                }
            }
            .navigationTitle("Настройки")
        }
    }
}

// Заглушки для других экранов
struct EditProfileView: View {
    var body: some View {
        Text("Редактирование профиля")
            .navigationTitle("Редактировать")
            .navigationBarTitleDisplayMode(.inline)
    }
}

struct ChangePasswordView: View {
    var body: some View {
        Text("Изменение пароля")
            .navigationTitle("Пароль")
            .navigationBarTitleDisplayMode(.inline)
    }
}

struct NotificationSettingsView: View {
    var body: some View {
        Text("Настройки уведомлений")
            .navigationTitle("Уведомления")
            .navigationBarTitleDisplayMode(.inline)
    }
}

struct AboutView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "app")
                .font(.system(size: 80))
                .foregroundColor(.blue)
            
            Text("MyApp")
                .font(.title)
                .fontWeight(.bold)
            
            Text("Версия 1.0.0")
                .foregroundColor(.secondary)
            
            Text("© 2025 Наша компания")
                .font(.footnote)
                .foregroundColor(.secondary)
        }
        .navigationTitle("О приложении")
        .navigationBarTitleDisplayMode(.inline)
    }
}

// MARK: - App

@main
struct MyApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
[/swift]
```

### Kotlin Android приложение

```
[kotlin]
// MainActivity.kt
package com.example.myapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.myapp.ui.theme.MyAppTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    
    private val authViewModel: AuthViewModel by viewModels()
    
    override fun onCreate(savedInstanceState: Bundle?) {
        val splashScreen = installSplashScreen()
        super.onCreate(savedInstanceState)
        
        // Показываем splash screen пока загружается состояние аутентификации
        splashScreen.setKeepOnScreenCondition {
            authViewModel.isLoading.value
        }
        
        setContent {
            MyAppTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val authState = authViewModel.authState.collectAsStateWithLifecycle()
                    
                    MyAppNavigation(
                        isAuthenticated = authState.value.isAuthenticated,
                        user = authState.value.user
                    )
                }
            }
        }
    }
}

// AuthViewModel.kt
package com.example.myapp.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapp.data.models.User
import com.example.myapp.data.repositories.AuthRepository
import com.example.myapp.utils.Resource
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AuthState(
    val isAuthenticated: Boolean = false,
    val user: User? = null,
    val isLoading: Boolean = true,
    val error: String? = null
)

data class LoginState(
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    
    private val _authState = MutableStateFlow(AuthState())
    val authState: StateFlow<AuthState> = _authState.asStateFlow()
    
    private val _loginState = MutableStateFlow(LoginState())
    val loginState: StateFlow<LoginState> = _loginState.asStateFlow()
    
    val isLoading: StateFlow<Boolean> = _authState.asStateFlow()
        .map { it.isLoading }
    
    init {
        checkAuthStatus()
    }
    
    private fun checkAuthStatus() {
        viewModelScope.launch {
            try {
                val isAuthenticated = authRepository.isUserAuthenticated()
                if (isAuthenticated) {
                    val user = authRepository.getCurrentUser()
                    _authState.value = AuthState(
                        isAuthenticated = true,
                        user = user,
                        isLoading = false
                    )
                } else {
                    _authState.value = AuthState(
                        isAuthenticated = false,
                        isLoading = false
                    )
                }
            } catch (e: Exception) {
                _authState.value = AuthState(
                    isAuthenticated = false,
                    isLoading = false,
                    error = e.message
                )
            }
        }
    }
    
    fun login(username: String, password: String, rememberMe: Boolean = false) {
        viewModelScope.launch {
            _loginState.value = LoginState(isLoading = true)
            
            when (val result = authRepository.login(username, password, rememberMe)) {
                is Resource.Success -> {
                    _loginState.value = LoginState()
                    _authState.value = AuthState(
                        isAuthenticated = true,
                        user = result.data.user,
                        isLoading = false
                    )
                }
                is Resource.Error -> {
                    _loginState.value = LoginState(
                        isLoading = false,
                        error = result.message
                    )
                }
                is Resource.Loading -> {
                    _loginState.value = LoginState(isLoading = true)
                }
            }
        }
    }
    
    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
            _authState.value = AuthState(
                isAuthenticated = false,
                isLoading = false
            )
        }
    }
    
    fun clearLoginError() {
        _loginState.value = _loginState.value.copy(error = null)
    }
}

// AuthRepository.kt
package com.example.myapp.data.repositories

import com.example.myapp.data.local.PreferencesManager
import com.example.myapp.data.local.TokenManager
import com.example.myapp.data.models.LoginRequest
import com.example.myapp.data.models.LoginResponse
import com.example.myapp.data.models.User
import com.example.myapp.data.remote.ApiService
import com.example.myapp.utils.Resource
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val apiService: ApiService,
    private val tokenManager: TokenManager,
    private val preferencesManager: PreferencesManager
) {
    
    suspend fun login(username: String, password: String, rememberMe: Boolean): Resource<LoginResponse> {
        return try {
            val request = LoginRequest(username, password, rememberMe)
            val response = apiService.login(request)
            
            if (response.success && response.data != null) {
                // Сохраняем токены
                tokenManager.saveTokens(
                    accessToken = response.data.accessToken,
                    refreshToken = response.data.refreshToken
                )
                
                // Сохраняем настройку "запомнить меня"
                preferencesManager.setRememberMe(rememberMe)
                
                Resource.Success(response.data)
            } else {
                Resource.Error(response.message ?: "Неизвестная ошибка")
            }
        } catch (e: Exception) {
            Resource.Error(e.message ?: "Ошибка сети")
        }
    }
    
    suspend fun logout() {
        try {
            // Уведомляем сервер о выходе
            apiService.logout()
        } catch (e: Exception) {
            // Игнорируем ошибки при выходе
        }
        
        // Очищаем локальные данные
        tokenManager.clearTokens()
        preferencesManager.clearUserData()
    }
    
    suspend fun refreshToken(): Resource<String> {
        return try {
            val refreshToken = tokenManager.getRefreshToken()
            if (refreshToken != null) {
                val response = apiService.refreshToken(refreshToken)
                if (response.success && response.data != null) {
                    tokenManager.saveAccessToken(response.data.accessToken)
                    Resource.Success(response.data.accessToken)
                } else {
                    Resource.Error("Не удалось обновить токен")
                }
            } else {
                Resource.Error("Токен обновления не найден")
            }
        } catch (e: Exception) {
            Resource.Error(e.message ?: "Ошибка обновления токена")
        }
    }
    
    suspend fun isUserAuthenticated(): Boolean {
        val accessToken = tokenManager.getAccessToken()
        return accessToken != null && !tokenManager.isTokenExpired(accessToken)
    }
    
    suspend fun getCurrentUser(): User? {
        return try {
            val response = apiService.getCurrentUser()
            if (response.success) {
                response.data
            } else {
                null
            }
        } catch (e: Exception) {
            null
        }
    }
}

// TokenManager.kt
package com.example.myapp.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKeys
import com.auth0.android.jwt.JWT
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.Date
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TokenManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    
    private val masterKeyAlias = MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC)
    
    private val encryptedPrefs: SharedPreferences = EncryptedSharedPreferences.create(
        "secure_tokens",
        masterKeyAlias,
        context,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    
    companion object {
        private const val ACCESS_TOKEN_KEY = "access_token"
        private const val REFRESH_TOKEN_KEY = "refresh_token"
    }
    
    fun saveTokens(accessToken: String, refreshToken: String) {
        encryptedPrefs.edit()
            .putString(ACCESS_TOKEN_KEY, accessToken)
            .putString(REFRESH_TOKEN_KEY, refreshToken)
            .apply()
    }
    
    fun saveAccessToken(accessToken: String) {
        encryptedPrefs.edit()
            .putString(ACCESS_TOKEN_KEY, accessToken)
            .apply()
    }
    
    fun getAccessToken(): String? {
        return encryptedPrefs.getString(ACCESS_TOKEN_KEY, null)
    }
    
    fun getRefreshToken(): String? {
        return encryptedPrefs.getString(REFRESH_TOKEN_KEY, null)
    }
    
    fun clearTokens() {
        encryptedPrefs.edit()
            .remove(ACCESS_TOKEN_KEY)
            .remove(REFRESH_TOKEN_KEY)
            .apply()
    }
    
    fun isTokenExpired(token: String): Boolean {
        return try {
            val jwt = JWT(token)
            val expirationTime = jwt.expiresAt
            expirationTime?.before(Date()) ?: true
        } catch (e: Exception) {
            true
        }
    }
    
    fun getTokenExpirationTime(token: String): Date? {
        return try {
            val jwt = JWT(token)
            jwt.expiresAt
        } catch (e: Exception) {
            null
        }
    }
}

// ApiService.kt
package com.example.myapp.data.remote

import com.example.myapp.data.models.*
import retrofit2.http.*

interface ApiService {
    
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): ApiResponse<LoginResponse>
    
    @POST("auth/logout")
    suspend fun logout(): ApiResponse<Unit>
    
    @POST("auth/refresh")
    suspend fun refreshToken(@Body refreshToken: String): ApiResponse<TokenResponse>
    
    @GET("auth/me")
    suspend fun getCurrentUser(): ApiResponse<User>
    
    @GET("users")
    suspend fun getUsers(
        @Query("page") page: Int = 1,
        @Query("per_page") perPage: Int = 20,
        @Query("search") search: String? = null,
        @Query("role") role: String? = null
    ): ApiResponse<PaginatedResponse<User>>
    
    @GET("users/{id}")
    suspend fun getUser(@Path("id") userId: Int): ApiResponse<User>
    
    @POST("users")
    suspend fun createUser(@Body request: CreateUserRequest): ApiResponse<User>
    
    @PUT("users/{id}")
    suspend fun updateUser(
        @Path("id") userId: Int,
        @Body request: UpdateUserRequest
    ): ApiResponse<User>
    
    @DELETE("users/{id}")
    suspend fun deleteUser(@Path("id") userId: Int): ApiResponse<Unit>
}

// Models
data class User(
    val id: Int,
    val username: String,
    val email: String,
    val firstName: String,
    val lastName: String,
    val avatar: String? = null,
    val isActive: Boolean,
    val createdAt: String
) {
    val fullName: String
        get() = "$firstName $lastName".trim()
    
    val initials: String
        get() {
            val firstInitial = firstName.firstOrNull()?.toString()?.uppercase() ?: ""
            val lastInitial = lastName.firstOrNull()?.toString()?.uppercase() ?: ""
            return "$firstInitial$lastInitial"
        }
}

data class LoginRequest(
    val username: String,
    val password: String,
    val rememberMe: Boolean
)

data class LoginResponse(
    val accessToken: String,
    val refreshToken: String,
    val user: User
)

data class TokenResponse(
    val accessToken: String
)

data class ApiResponse<T>(
    val success: Boolean,
    val data: T? = null,
    val message: String? = null,
    val errors: Map<String, List<String>>? = null
)

data class PaginatedResponse<T>(
    val items: List<T>,
    val currentPage: Int,
    val totalPages: Int,
    val totalItems: Int,
    val perPage: Int
)

data class CreateUserRequest(
    val username: String,
    val email: String,
    val firstName: String,
    val lastName: String,
    val password: String
)

data class UpdateUserRequest(
    val username: String?,
    val email: String?,
    val firstName: String?,
    val lastName: String?
)

// UI Composables
@Composable
fun LoginScreen(
    onLoginSuccess: () -> Unit,
    authViewModel: AuthViewModel = hiltViewModel()
) {
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var rememberMe by remember { mutableStateOf(false) }
    var showPassword by remember { mutableStateOf(false) }
    
    val loginState by authViewModel.loginState.collectAsStateWithLifecycle()
    
    // Обрабатываем успешную авторизацию
    LaunchedEffect(authViewModel.authState.collectAsStateWithLifecycle().value.isAuthenticated) {
        if (authViewModel.authState.value.isAuthenticated) {
            onLoginSuccess()
        }
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Логотип
        Icon(
            imageVector = Icons.Default.AccountCircle,
            contentDescription = null,
            modifier = Modifier.size(120.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Text(
            text = "Добро пожаловать",
            style = MaterialTheme.typography.headlineLarge,
            fontWeight = FontWeight.Bold
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = "Войдите в свой аккаунт",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        // Поля ввода
        OutlinedTextField(
            value = username,
            onValueChange = { username = it },
            label = { Text("Имя пользователя") },
            leadingIcon = {
                Icon(Icons.Default.Person, contentDescription = null)
            },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Text,
                imeAction = ImeAction.Next
            ),
            isError = loginState.error != null
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("Пароль") },
            leadingIcon = {
                Icon(Icons.Default.Lock, contentDescription = null)
            },
            trailingIcon = {
                IconButton(onClick = { showPassword = !showPassword }) {
                    Icon(
                        imageVector = if (showPassword) Icons.Default.Visibility else Icons.Default.VisibilityOff,
                        contentDescription = if (showPassword) "Скрыть пароль" else "Показать пароль"
                    )
                }
            },
            visualTransformation = if (showPassword) VisualTransformation.None else PasswordVisualTransformation(),
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Password,
                imeAction = ImeAction.Done
            ),
            keyboardActions = KeyboardActions(
                onDone = {
                    if (username.isNotBlank() && password.isNotBlank()) {
                        authViewModel.login(username, password, rememberMe)
                    }
                }
            ),
            isError = loginState.error != null
        )
        
        // Показываем ошибку
        if (loginState.error != null) {
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = loginState.error,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall
            )
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Чекбокс "Запомнить меня"
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Checkbox(
                checked = rememberMe,
                onCheckedChange = { rememberMe = it }
            )
            Text(
                text = "Запомнить меня",
                modifier = Modifier.clickable { rememberMe = !rememberMe }
            )
            
            Spacer(modifier = Modifier.weight(1f))
            
            TextButton(onClick = { /* TODO: Восстановление пароля */ }) {
                Text("Забыли пароль?")
            }
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Кнопка входа
        Button(
            onClick = {
                authViewModel.clearLoginError()
                authViewModel.login(username, password, rememberMe)
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            enabled = username.isNotBlank() && password.isNotBlank() && !loginState.isLoading
        ) {
            if (loginState.isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    color = MaterialTheme.colorScheme.onPrimary
                )
            } else {
                Text("Войти")
            }
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Ссылка на регистрацию
        Row {
            Text(
                text = "Нет аккаунта? ",
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Text(
                text = "Зарегистрироваться",
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.clickable {
                    // TODO: Переход к регистрации
                }
            )
        }
    }
}

@Composable
fun MyAppNavigation(
    isAuthenticated: Boolean,
    user: User?
) {
    if (isAuthenticated && user != null) {
        MainScreen(user = user)
    } else {
        LoginScreen(
            onLoginSuccess = { /* Navigation handled by state change */ }
        )
    }
}

@Composable
fun MainScreen(user: User) {
    var selectedTab by remember { mutableStateOf(0) }
    
    val tabs = listOf(
        Triple("Главная", Icons.Default.Home, Icons.Outlined.Home),
        Triple("Профиль", Icons.Default.Person, Icons.Outlined.Person),
        Triple("Настройки", Icons.Default.Settings, Icons.Outlined.Settings)
    )
    
    Column {
        when (selectedTab) {
            0 -> HomeScreen(user = user)
            1 -> ProfileScreen(user = user)
            2 -> SettingsScreen(user = user)
        }
        
        NavigationBar {
            tabs.forEachIndexed { index, (title, selectedIcon, unselectedIcon) ->
                NavigationBarItem(
                    icon = {
                        Icon(
                            imageVector = if (selectedTab == index) selectedIcon else unselectedIcon,
                            contentDescription = title
                        )
                    },
                    label = { Text(title) },
                    selected = selectedTab == index,
                    onClick = { selectedTab = index }
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(user: User) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Главная") },
                actions = {
                    IconButton(onClick = { /* TODO: Notifications */ }) {
                        Icon(Icons.Default.Notifications, contentDescription = "Уведомления")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
        ) {
            Text(
                text = "Привет, ${user.firstName}!",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold
            )
            
            Text(
                text = "Добро пожаловать в приложение",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Здесь основной контент приложения
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(10) { index ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        onClick = { /* TODO: Handle item click */ }
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp)
                        ) {
                            Text(
                                text = "Элемент ${index + 1}",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Medium
                            )
                            Text(
                                text = "Описание элемента ${index + 1}",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }
        }
    }
}
[/kotlin]
```

---

## Лучшие практики

### Общие рекомендации по использованию плагина

1. **Выбор подходящего языка**: Всегда используйте правильный шорткод для вашего кода
2. **Форматирование**: Сохраняйте правильные отступы в коде
3. **Длинные блоки**: Для больших блоков кода используйте полноэкранный режим
4. **Мобильная оптимизация**: Проверяйте отображение на мобильных устройствах
5. **Производительность**: Не размещайте слишком много блоков кода на одной странице

### Советы по написанию кода для демонстрации

1. **Комментарии**: Добавляйте поясняющие комментарии
2. **Читаемость**: Используйте осмысленные названия переменных
3. **Примеры**: Включайте практические примеры использования
4. **Ошибки**: Показывайте как правильную реализацию, так и типичные ошибки
5. **Документация**: Добавляйте краткое описание к сложным блокам кода

Этот документ демонстрирует возможности плагина Code Highlighter Copy на реальных примерах кода из различных областей разработки. Каждый пример показывает не только синтаксис языка, но и лучшие практики программирования.