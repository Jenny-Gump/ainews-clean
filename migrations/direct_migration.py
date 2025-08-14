#!/usr/bin/env python3
"""
Direct Data Migration using MCP
Migrates data from SQLite to Supabase with proper data transformation
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

def generate_uuid():
    """Generate a new UUID for records"""
    return str(uuid.uuid4())

def convert_datetime(dt_string: Optional[str]) -> Optional[str]:
    """Convert SQLite datetime to PostgreSQL timestamp"""
    if not dt_string:
        return None
    try:
        if 'T' in dt_string:
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        return dt.isoformat()
    except Exception:
        return None

def convert_json(json_string: Optional[str]) -> Optional[Dict]:
    """Convert JSON string to dictionary for JSONB"""
    if not json_string:
        return None
    try:
        if isinstance(json_string, str):
            return json.loads(json_string)
        return json_string
    except:
        return None

def prepare_sources_for_supabase(sqlite_sources: List[Dict]) -> List[Dict]:
    """Transform SQLite sources to Supabase format"""
    supabase_sources = []
    
    for source in sqlite_sources:
        # Create metadata object with all extra fields
        metadata = {
            'type': source.get('type'),
            'has_rss': bool(source.get('has_rss', 0)),
            'last_status': source.get('last_status'),
            'last_error': source.get('last_error'),
            'success_rate': source.get('success_rate', 0),
            'last_parsed': source.get('last_parsed'),
            'total_articles': source.get('total_articles', 0),
            'selectors': convert_json(source.get('selectors')),
            'validation_status': source.get('validation_status'),
            'circuit_breaker_failures': source.get('circuit_breaker_failures', 0),
            'circuit_breaker_reset_time': source.get('circuit_breaker_reset_time'),
            'last_article_discovery': source.get('last_article_discovery'),
            'consecutive_failures': source.get('consecutive_failures', 0),
            'last_rss_check': source.get('last_rss_check'),
            'rss_fetch_frequency': source.get('rss_fetch_frequency', 3600)
        }
        
        # Remove None values from metadata
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        supabase_record = {
            'id': generate_uuid(),
            'source_id': source['source_id'],
            'name': source['name'],
            'url': source.get('url'),
            'feed_url': source.get('rss_url'),
            'language': 'en',  # Default language
            'category': source.get('category'),
            'active': source.get('last_status') == 'active' if source.get('last_status') else True,
            'last_checked': convert_datetime(source.get('last_rss_check')),
            'error_count': source.get('consecutive_failures', 0),
            'metadata': metadata,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        supabase_sources.append(supabase_record)
    
    return supabase_sources

# SQL queries for batch insertion
SOURCES_INSERT_SQL = """
INSERT INTO sources (
    id, source_id, name, url, feed_url, language, category, 
    active, last_checked, error_count, metadata, created_at, updated_at
) VALUES {}
ON CONFLICT (source_id) DO UPDATE SET
    name = EXCLUDED.name,
    url = EXCLUDED.url,
    feed_url = EXCLUDED.feed_url,
    category = EXCLUDED.category,
    metadata = EXCLUDED.metadata,
    updated_at = EXCLUDED.updated_at
"""

def generate_sources_values(sources: List[Dict]) -> str:
    """Generate VALUES clause for sources insertion"""
    values = []
    for s in sources:
        values.append(f"""(
            '{s['id']}',
            '{s['source_id'].replace("'", "''")}',
            '{s['name'].replace("'", "''")}',
            {f"'{s['url'].replace('\'', '\'\'')}'" if s['url'] else 'NULL'},
            {f"'{s['feed_url'].replace('\'', '\'\'')}'" if s['feed_url'] else 'NULL'},
            '{s['language']}',
            {f"'{s['category']}'" if s['category'] else 'NULL'},
            {s['active']},
            {f"'{s['last_checked']}'" if s['last_checked'] else 'NULL'},
            {s['error_count']},
            '{json.dumps(s['metadata']).replace("'", "''")}',
            '{s['created_at']}',
            '{s['updated_at']}'
        )""")
    return ', '.join(values)

print("""
=============================================================
DIRECT MIGRATION SCRIPT FOR SUPABASE
=============================================================

This script contains transformation functions for migrating data.
Use the following steps with MCP tools:

STEP 1: MIGRATE SOURCES
------------------------
1. Get SQLite sources (already done above)
2. Transform using prepare_sources_for_supabase()
3. Insert into Supabase using batch SQL

STEP 2: MIGRATE ARTICLES
------------------------
Will need to:
1. Check Supabase articles table structure
2. Transform SQLite articles data
3. Insert with proper foreign keys

STEP 3: MIGRATE MEDIA FILES
---------------------------
Will need to:
1. Check Supabase media_files structure
2. Transform data with article_id references
3. Insert in batches

Continue with migration...
""")