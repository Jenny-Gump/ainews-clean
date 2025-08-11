<?php

/**
 * Класс для валидации параметров API создания постов с мета-полями
 * БЕЗ ОГРАНИЧЕНИЙ НА ДЛИНУ ПОЛЕЙ
 */

if (!defined('ABSPATH')) {
    exit;
}

class Post_Meta_Endpoint_Validator
{

    /**
     * Валидация параметров для создания поста
     */
    public static function get_create_args()
    {
        return [
            'title' => [
                'required' => true,
                'type' => 'string',
                'sanitize_callback' => 'sanitize_text_field',
                'validate_callback' => [self::class, 'validate_title']
            ],
            'slug' => [
                'required' => false,
                'type' => 'string',
                'sanitize_callback' => [self::class, 'sanitize_slug']
            ],
            'author' => [
                'required' => false,
                'type' => ['integer', 'string'],
                'sanitize_callback' => [self::class, 'sanitize_author'],
                'validate_callback' => [self::class, 'validate_author']
            ],
            'content' => [
                'required' => false,
                'type' => 'string',
                'sanitize_callback' => [self::class, 'sanitize_content']
            ],
            'excerpt' => [
                'required' => false,
                'type' => 'string',
                'sanitize_callback' => 'sanitize_textarea_field'
            ],
            'post_type' => [
                'required' => false,
                'type' => 'string',
                'default' => 'post',
                'enum' => ['post', 'page'],
                'sanitize_callback' => 'sanitize_key'
            ],
            'status' => [
                'required' => false,
                'type' => 'string',
                'default' => 'draft',
                'enum' => ['draft', 'publish', 'private', 'pending'],
                'sanitize_callback' => 'sanitize_key'
            ],
            // SEO мета-поля (совместимые с Yoast SEO) - БЕЗ ОГРАНИЧЕНИЙ
            'seo_title' => [
                'required' => false,
                'type' => 'string',
                'sanitize_callback' => 'sanitize_text_field'
            ],
            'seo_description' => [
                'required' => false,
                'type' => 'string',
                'sanitize_callback' => 'sanitize_textarea_field'
            ],
            'focus_keyword' => [
                'required' => false,
                'type' => 'string',
                'sanitize_callback' => 'sanitize_text_field'
            ],
            'canonical_url' => [
                'required' => false,
                'type' => 'string',
                'sanitize_callback' => 'esc_url_raw',
                'validate_callback' => [self::class, 'validate_url']
            ],
            'noindex' => [
                'required' => false,
                'type' => 'boolean'
            ],
            'nofollow' => [
                'required' => false,
                'type' => 'boolean'
            ],
            // Дополнительные мета-поля
            'og_title' => [
                'required' => false,
                'type' => 'string',
                'sanitize_callback' => 'sanitize_text_field'
            ],
            'og_description' => [
                'required' => false,
                'type' => 'string',
                'sanitize_callback' => 'sanitize_textarea_field'
            ],
            'og_image' => [
                'required' => false,
                'type' => 'string',
                'sanitize_callback' => 'esc_url_raw',
                'validate_callback' => [self::class, 'validate_url']
            ],
            'twitter_title' => [
                'required' => false,
                'type' => 'string',
                'sanitize_callback' => 'sanitize_text_field'
            ],
            'twitter_description' => [
                'required' => false,
                'type' => 'string',
                'sanitize_callback' => 'sanitize_textarea_field'
            ],
            // Категории и теги
            'categories' => [
                'required' => false,
                'type' => 'array',
                'items' => ['type' => 'integer'],
                'sanitize_callback' => [self::class, 'sanitize_categories']
            ],
            'tags' => [
                'required' => false,
                'type' => 'array',
                'items' => ['type' => 'string'],
                'sanitize_callback' => [self::class, 'sanitize_tags']
            ]
        ];
    }

    /**
     * Валидация для обновления поста
     */
    public static function get_update_args()
    {
        $args = self::get_create_args();
        $args['title']['required'] = false;
        return $args;
    }

    /**
     * Валидация заголовка - БЕЗ ОГРАНИЧЕНИЙ НА ДЛИНУ
     */
    public static function validate_title($param)
    {
        if (empty(trim($param))) {
            return new WP_Error('empty_title', 'Заголовок не может быть пустым');
        }
        return true;
    }

    /**
     * Валидация URL
     */
    public static function validate_url($param)
    {
        if (empty($param)) {
            return true;
        }

        if (!filter_var($param, FILTER_VALIDATE_URL)) {
            return new WP_Error('invalid_url', 'Неверный формат URL');
        }

        return true;
    }

    /**
     * Санитизация slug
     */
    public static function sanitize_slug($param)
    {
        if (empty($param)) {
            return '';
        }

        // Используем WordPress функцию для создания slug
        return sanitize_title($param);
    }

    /**
     * Валидация автора поста
     */
    public static function validate_author($param)
    {
        if (empty($param)) {
            return true;
        }

        // Если передан ID пользователя
        if (is_numeric($param)) {
            $user = get_user_by('ID', intval($param));
            if (!$user) {
                return new WP_Error(
                    'invalid_author_id', 
                    'Пользователь с указанным ID не найден'
                );
            }
            return true;
        }

        // Если передан email пользователя
        if (is_string($param) && is_email($param)) {
            $user = get_user_by('email', $param);
            if (!$user) {
                return new WP_Error(
                    'invalid_author_email', 
                    'Пользователь с указанным email не найден'
                );
            }
            return true;
        }

        return new WP_Error(
            'invalid_author_format', 
            'Автор должен быть указан как ID пользователя (число) или email'
        );
    }

    /**
     * Санитизация автора поста
     */
    public static function sanitize_author($param)
    {
        if (empty($param)) {
            return null;
        }

        // Если передан ID пользователя
        if (is_numeric($param)) {
            return intval($param);
        }

        // Если передан email - находим ID по email
        if (is_string($param) && is_email($param)) {
            $user = get_user_by('email', sanitize_email($param));
            return $user ? $user->ID : null;
        }

        return null;
    }

    /**
     * Санитизация контента
     */
    public static function sanitize_content($param)
    {
        return wp_kses_post($param);
    }

    /**
     * Санитизация категорий
     */
    public static function sanitize_categories($param)
    {
        if (!is_array($param)) {
            return [];
        }

        return array_map('intval', array_filter($param, function ($cat) {
            return is_numeric($cat) && $cat > 0 && term_exists($cat, 'category');
        }));
    }

    /**
     * Санитизация тегов
     */
    public static function sanitize_tags($param)
    {
        if (!is_array($param)) {
            return [];
        }

        return array_map('sanitize_text_field', array_filter($param, function ($tag) {
            return !empty(trim($tag));
        }));
    }

    /**
     * Валидация всех параметров перед сохранением - УПРОЩЕННАЯ ВЕРСИЯ
     */
    public static function validate_all_params($params)
    {
        $errors = [];

        // Проверяем обязательные поля для создания
        if (empty($params['title']) && !isset($params['ID'])) {
            $errors[] = 'Заголовок обязателен для создания нового поста';
        }

        // Проверяем URL поля
        $url_fields = ['canonical_url', 'og_image'];
        foreach ($url_fields as $field) {
            if (!empty($params[$field]) && !filter_var($params[$field], FILTER_VALIDATE_URL)) {
                $errors[] = "Неверный формат URL в поле {$field}";
            }
        }

        // Проверяем существование категорий
        if (!empty($params['categories'])) {
            foreach ($params['categories'] as $cat_id) {
                if (!term_exists($cat_id, 'category')) {
                    $errors[] = "Категория с ID {$cat_id} не существует";
                }
            }
        }

        return empty($errors) ? true : $errors;
    }

    /**
     * Получение описаний полей для документации
     */
    public static function get_fields_documentation()
    {
        return [
            'basic_fields' => [
                'title' => 'Заголовок поста (обязательное для создания)',
                'slug' => 'URL-слаг поста. Если не указан - создается автоматически из заголовка',
                'author' => 'Автор поста. Можно указать ID пользователя (число) или email',
                'content' => 'HTML содержимое поста',
                'excerpt' => 'Краткое описание поста',
                'post_type' => 'Тип поста: post, page',
                'status' => 'Статус: draft, publish, private, pending'
            ],
            'seo_fields' => [
                'seo_title' => 'SEO заголовок для поисковиков (без ограничений)',
                'seo_description' => 'SEO описание для поисковиков (без ограничений)',
                'focus_keyword' => 'Ключевое слово для SEO анализа',
                'canonical_url' => 'Канонический URL страницы',
                'noindex' => 'Запретить индексацию (true/false)',
                'nofollow' => 'Запретить переход по ссылкам (true/false)'
            ],
            'social_fields' => [
                'og_title' => 'Заголовок для Open Graph (Facebook)',
                'og_description' => 'Описание для Open Graph',
                'og_image' => 'Изображение для Open Graph (URL)',
                'twitter_title' => 'Заголовок для Twitter Card',
                'twitter_description' => 'Описание для Twitter Card'
            ],
            'taxonomy_fields' => [
                'categories' => 'Массив ID категорий',
                'tags' => 'Массив названий тегов'
            ]
        ];
    }
}