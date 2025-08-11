=== Custom Post Meta Endpoint (No Limits) ===
Contributors: asafeeson.dev
Tags: api, rest, yoast, seo, meta
Requires at least: 5.0
Tested up to: 6.4
Stable tag: 2.7.0
License: GPLv2 or later

REST API для создания WordPress постов с полной поддержкой SEO мета-полей БЕЗ ОГРАНИЧЕНИЙ НА ДЛИНУ.

== Description ==

Плагин предоставляет REST API эндпоинт для создания и обновления WordPress постов с полной поддержкой SEO мета-полей. 

**ОСОБЕННОСТИ:**
* Полная поддержка Yoast SEO мета-полей
* БЕЗ ОГРАНИЧЕНИЙ на длину SEO заголовков и описаний  
* Аутентификация через API ключ
* Поддержка категорий и тегов
* Совместимость с Open Graph и Twitter Cards

**API ЭНДПОИНТ:**
`POST /wp-json/custom-post-meta/v1/posts`

**ЗАГОЛОВКИ:**
* Content-Type: application/json
* X-API-Key: [ваш_ключ]

**ПОЛЯ (все необязательные, кроме title):**
* title - Заголовок поста (обязательно)
* content - HTML содержимое
* excerpt - Краткое описание  
* slug - URL слаг
* status - Статус поста
* categories - Массив ID категорий
* tags - Массив названий тегов

**SEO ПОЛЯ (БЕЗ ОГРАНИЧЕНИЙ):**
* seo_title - SEO заголовок
* seo_description - SEO описание
* focus_keyword - Ключевое слово
* canonical_url - Канонический URL
* og_title, og_description, og_image - Open Graph
* twitter_title, twitter_description - Twitter Cards

== Installation ==

1. Загрузите файлы плагина в папку `/wp-content/plugins/custom-post-meta-endpoint/`
2. Активируйте плагин через меню 'Плагины' в WordPress
3. Перейдите в Настройки > Post Meta API для настройки API ключа

== Changelog ==

= 2.7.0 =
* УБРАНЫ ВСЕ ОГРАНИЧЕНИЯ на длину SEO полей
* Упрощена валидация
* Улучшена совместимость

= 2.6.2 =
* Добавлена поддержка настройки длины полей
* Улучшена валидация параметров

= 2.0.0 =
* Начальная версия