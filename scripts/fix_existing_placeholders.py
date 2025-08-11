#!/usr/bin/env python3
"""
Скрипт для очистки существующих статей от неудаленных плейсхолдеров [IMAGE_N]
"""

import sys
import os
import re
import json
import time
import requests
from requests.auth import HTTPBasicAuth
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.config import Config
from core.database import Database

def get_wordpress_posts_with_placeholders(config):
    """Получает все посты из WordPress и проверяет наличие плейсхолдеров"""
    posts_with_placeholders = []
    
    try:
        # Get all posts (up to 100)
        url = f"{config.wordpress_api_url}/posts"
        auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
        
        response = requests.get(url, auth=auth, params={'per_page': 100, 'status': 'any'})
        
        if response.status_code != 200:
            print(f"Failed to fetch posts: {response.status_code}")
            return posts_with_placeholders
            
        posts = response.json()
        placeholder_pattern = r'\[IMAGE_\d+\]'
        
        for post in posts:
            content = post.get('content', {}).get('rendered', '')
            placeholders = re.findall(placeholder_pattern, content)
            
            if placeholders:
                posts_with_placeholders.append({
                    'id': post['id'],
                    'title': post['title']['rendered'],
                    'link': post['link'],
                    'placeholders': placeholders,
                    'placeholder_count': len(placeholders)
                })
                
        return posts_with_placeholders
        
    except Exception as e:
        print(f"Error fetching WordPress posts: {e}")
        return posts_with_placeholders

def clean_post_content(post_id, config):
    """Удаляет плейсхолдеры из контента поста"""
    try:
        # Get post content
        url = f"{config.wordpress_api_url}/posts/{post_id}"
        auth = HTTPBasicAuth(config.wordpress_username, config.wordpress_app_password)
        
        response = requests.get(url, auth=auth, params={'context': 'edit'})
        
        if response.status_code != 200:
            print(f"Failed to fetch post {post_id}: {response.status_code}")
            return False
            
        post = response.json()
        content = post.get('content', {}).get('raw', '')
        
        # Remove placeholders
        placeholder_pattern = r'\[IMAGE_\d+\]'
        cleaned_content = re.sub(placeholder_pattern, '', content)
        
        # If content changed, update the post
        if cleaned_content != content:
            # Count removed placeholders
            removed_count = len(re.findall(placeholder_pattern, content))
            
            # Update post
            update_data = {
                'content': cleaned_content
            }
            
            response = requests.post(
                url,
                json=update_data,
                auth=auth,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Post {post_id} updated: removed {removed_count} placeholders")
                return True
            else:
                print(f"❌ Failed to update post {post_id}: {response.status_code}")
                return False
        else:
            print(f"ℹ️ Post {post_id} has no placeholders in raw content")
            return True
            
    except Exception as e:
        print(f"Error cleaning post {post_id}: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("Fix Existing Placeholders Script")
    print("=" * 60)
    
    # Initialize config
    config = Config()
    
    # Check WordPress configuration
    if not all([config.wordpress_api_url, 
               config.wordpress_username, 
               config.wordpress_app_password]):
        print("❌ WordPress API configuration missing in .env file")
        return
    
    print(f"WordPress API: {config.wordpress_api_url}")
    print()
    
    # Get posts with placeholders
    print("Scanning WordPress posts for placeholders...")
    posts_with_placeholders = get_wordpress_posts_with_placeholders(config)
    
    if not posts_with_placeholders:
        print("✅ No posts with placeholders found!")
        return
    
    print(f"\nFound {len(posts_with_placeholders)} posts with placeholders:")
    print("-" * 60)
    
    for post in posts_with_placeholders:
        print(f"ID: {post['id']} | Title: {post['title'][:50]}...")
        print(f"   Placeholders: {post['placeholder_count']} | {', '.join(post['placeholders'][:5])}")
        print(f"   URL: {post['link']}")
        print()
    
    # Ask for confirmation
    print("-" * 60)
    response = input(f"Do you want to clean {len(posts_with_placeholders)} posts? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Operation cancelled")
        return
    
    # Clean posts
    print("\nCleaning posts...")
    print("-" * 60)
    
    success_count = 0
    failed_count = 0
    
    for post in posts_with_placeholders:
        success = clean_post_content(post['id'], config)
        
        if success:
            success_count += 1
        else:
            failed_count += 1
        
        # Small delay to avoid overwhelming the API
        time.sleep(1)
    
    # Summary
    print()
    print("=" * 60)
    print("Summary:")
    print(f"✅ Successfully cleaned: {success_count} posts")
    print(f"❌ Failed: {failed_count} posts")
    print(f"📊 Total processed: {len(posts_with_placeholders)} posts")
    print("=" * 60)

if __name__ == "__main__":
    main()