<?php

/**
 * Класс для работы с SEO мета-полями
 */

if (!defined('ABSPATH')) {
    exit;
}

class Post_Meta_Endpoint_SEO_Meta
{
    
    /**
     * Сохранение SEO мета-полей
     */
    public static function save_seo_meta($post_id, $params)
    {
        $seo_fields = [
            'seo_title' => '_yoast_wpseo_title',
            'seo_description' => '_yoast_wpseo_metadesc',
            'focus_keyword' => '_yoast_wpseo_focuskw',
            'canonical_url' => '_yoast_wpseo_canonical',
            'og_title' => '_yoast_wpseo_opengraph-title',
            'og_description' => '_yoast_wpseo_opengraph-description',
            'og_image' => '_yoast_wpseo_opengraph-image',
            'twitter_title' => '_yoast_wpseo_twitter-title',
            'twitter_description' => '_yoast_wpseo_twitter-description'
        ];
        
        // Сохраняем SEO поля
        foreach ($seo_fields as $param_name => $meta_key) {
            if (isset($params[$param_name]) && !empty($params[$param_name])) {
                update_post_meta($post_id, $meta_key, $params[$param_name]);
            }
        }
        
        // Обработка noindex/nofollow
        if (isset($params['noindex']) || isset($params['nofollow'])) {
            $meta_robots = [];
            
            if (!empty($params['noindex'])) {
                $meta_robots[] = 'noindex';
            }
            if (!empty($params['nofollow'])) {
                $meta_robots[] = 'nofollow';
            }
            
            if (!empty($meta_robots)) {
                update_post_meta($post_id, '_yoast_wpseo_meta-robots-noindex', 1);
                update_post_meta($post_id, '_yoast_wpseo_meta-robots-nofollow', 1);
            }
        }
        
        // Дополнительные мета-поля для совместимости с другими SEO плагинами
        if (isset($params['seo_title'])) {
            update_post_meta($post_id, '_aioseop_title', $params['seo_title']);
        }
        
        if (isset($params['seo_description'])) {
            update_post_meta($post_id, '_aioseop_description', $params['seo_description']);
        }
    }
    
    /**
     * Получение SEO мета-полей
     */
    public static function get_seo_meta($post_id)
    {
        $seo_fields = [
            'seo_title' => '_yoast_wpseo_title',
            'seo_description' => '_yoast_wpseo_metadesc',
            'focus_keyword' => '_yoast_wpseo_focuskw',
            'canonical_url' => '_yoast_wpseo_canonical',
            'og_title' => '_yoast_wpseo_opengraph-title',
            'og_description' => '_yoast_wpseo_opengraph-description',
            'og_image' => '_yoast_wpseo_opengraph-image',
            'twitter_title' => '_yoast_wpseo_twitter-title',
            'twitter_description' => '_yoast_wpseo_twitter-description'
        ];
        
        $meta_data = [];
        
        foreach ($seo_fields as $param_name => $meta_key) {
            $value = get_post_meta($post_id, $meta_key, true);
            if (!empty($value)) {
                $meta_data[$param_name] = $value;
            }
        }
        
        // Получаем данные о noindex/nofollow
        $noindex = get_post_meta($post_id, '_yoast_wpseo_meta-robots-noindex', true);
        $nofollow = get_post_meta($post_id, '_yoast_wpseo_meta-robots-nofollow', true);
        
        if ($noindex) {
            $meta_data['noindex'] = true;
        }
        if ($nofollow) {
            $meta_data['nofollow'] = true;
        }
        
        return $meta_data;
    }
}