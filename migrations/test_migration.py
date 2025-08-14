#!/usr/bin/env python3
"""
Test Migration Script
Validates data migration from SQLite to Supabase
"""

import sqlite3
import logging
from typing import Dict, List, Any, Tuple
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client, Client
from core.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MigrationTester:
    def __init__(self):
        """Initialize connections"""
        self.config = Config()
        
        # SQLite connections
        self.ainews_db = sqlite3.connect('../data/ainews.db')
        self.ainews_db.row_factory = sqlite3.Row
        self.monitoring_db = sqlite3.connect('../data/monitoring.db')
        self.monitoring_db.row_factory = sqlite3.Row
        
        # Supabase connection
        self.supabase: Client = create_client(
            self.config.SUPABASE_URL,
            self.config.SUPABASE_KEY
        )
        
        self.test_results = []
    
    def close_connections(self):
        """Close database connections"""
        self.ainews_db.close()
        self.monitoring_db.close()
    
    def test_record_counts(self) -> List[Dict]:
        """Compare record counts between SQLite and Supabase"""
        results = []
        
        tables = [
            ('sources', self.ainews_db),
            ('articles', self.ainews_db),
            ('media_files', self.ainews_db),
            ('wordpress_articles', self.ainews_db),
            ('related_links', self.ainews_db),
            ('tracked_articles', self.ainews_db),
            ('tracked_urls', self.ainews_db),
            ('pipeline_operations', self.ainews_db),
            ('global_config', self.ainews_db)
        ]
        
        for table_name, db_conn in tables:
            # Get SQLite count
            cursor = db_conn.cursor()
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            sqlite_count = cursor.fetchone()['count']
            
            # Get Supabase count
            try:
                response = self.supabase.table(table_name).select('id', count='exact').execute()
                supabase_count = response.count if response.count is not None else 0
            except Exception as e:
                logger.error(f"Failed to get count for {table_name}: {e}")
                supabase_count = 0
            
            match = sqlite_count == supabase_count
            results.append({
                'table': table_name,
                'sqlite_count': sqlite_count,
                'supabase_count': supabase_count,
                'match': match,
                'difference': abs(sqlite_count - supabase_count)
            })
            
            status = "✓" if match else "✗"
            logger.info(f"{status} {table_name}: SQLite={sqlite_count}, Supabase={supabase_count}")
        
        return results
    
    def test_sample_data(self) -> List[Dict]:
        """Test sample records from each table"""
        results = []
        
        # Test sources
        logger.info("\nTesting sample data from sources...")
        cursor = self.ainews_db.cursor()
        cursor.execute("SELECT * FROM sources WHERE active = 1 LIMIT 5")
        sqlite_sources = cursor.fetchall()
        
        for source in sqlite_sources:
            try:
                response = self.supabase.table('sources').select('*').eq('id', source['id']).execute()
                if response.data:
                    pg_source = response.data[0]
                    # Compare key fields
                    match = (
                        pg_source['name'] == source['name'] and
                        pg_source['rss_url'] == source['rss_url'] and
                        pg_source['category'] == source['category']
                    )
                    results.append({
                        'table': 'sources',
                        'id': source['id'],
                        'field': 'name',
                        'sqlite_value': source['name'],
                        'pg_value': pg_source['name'],
                        'match': match
                    })
            except Exception as e:
                logger.error(f"Failed to test source {source['id']}: {e}")
        
        # Test articles
        logger.info("Testing sample data from articles...")
        cursor.execute("SELECT * FROM articles ORDER BY created_at DESC LIMIT 10")
        sqlite_articles = cursor.fetchall()
        
        for article in sqlite_articles:
            try:
                response = self.supabase.table('articles').select('*').eq('id', article['id']).execute()
                if response.data:
                    pg_article = response.data[0]
                    # Compare key fields
                    title_match = pg_article['title'] == article['title']
                    url_match = pg_article['url'] == article['url']
                    source_match = pg_article['source_id'] == article['source_id']
                    
                    results.append({
                        'table': 'articles',
                        'id': article['id'],
                        'checks': {
                            'title': title_match,
                            'url': url_match,
                            'source_id': source_match
                        },
                        'match': all([title_match, url_match, source_match])
                    })
            except Exception as e:
                logger.error(f"Failed to test article {article['id']}: {e}")
        
        return results
    
    def test_foreign_keys(self) -> List[Dict]:
        """Test foreign key relationships"""
        results = []
        
        # Test articles -> sources
        logger.info("\nTesting foreign key: articles -> sources...")
        try:
            response = self.supabase.table('articles').select('id, source_id').limit(100).execute()
            for article in response.data:
                source_response = self.supabase.table('sources').select('id').eq('id', article['source_id']).execute()
                exists = len(source_response.data) > 0
                if not exists:
                    results.append({
                        'constraint': 'articles.source_id -> sources.id',
                        'article_id': article['id'],
                        'source_id': article['source_id'],
                        'valid': False
                    })
        except Exception as e:
            logger.error(f"Failed to test articles->sources FK: {e}")
        
        # Test media_files -> articles
        logger.info("Testing foreign key: media_files -> articles...")
        try:
            response = self.supabase.table('media_files').select('id, article_id').limit(100).execute()
            for media in response.data:
                article_response = self.supabase.table('articles').select('id').eq('id', media['article_id']).execute()
                exists = len(article_response.data) > 0
                if not exists:
                    results.append({
                        'constraint': 'media_files.article_id -> articles.id',
                        'media_id': media['id'],
                        'article_id': media['article_id'],
                        'valid': False
                    })
        except Exception as e:
            logger.error(f"Failed to test media_files->articles FK: {e}")
        
        return results
    
    def test_data_types(self) -> List[Dict]:
        """Test data type conversions"""
        results = []
        
        # Test datetime conversions
        logger.info("\nTesting datetime conversions...")
        try:
            response = self.supabase.table('articles').select('id, published_date, created_at').limit(10).execute()
            for article in response.data:
                # Check if dates are valid ISO format
                try:
                    if article['published_date']:
                        datetime.fromisoformat(article['published_date'].replace('Z', '+00:00'))
                    if article['created_at']:
                        datetime.fromisoformat(article['created_at'].replace('Z', '+00:00'))
                    results.append({
                        'table': 'articles',
                        'id': article['id'],
                        'field': 'datetime',
                        'valid': True
                    })
                except Exception as e:
                    results.append({
                        'table': 'articles',
                        'id': article['id'],
                        'field': 'datetime',
                        'valid': False,
                        'error': str(e)
                    })
        except Exception as e:
            logger.error(f"Failed to test datetime types: {e}")
        
        # Test JSONB conversions
        logger.info("Testing JSONB conversions...")
        try:
            response = self.supabase.table('articles').select('id, tags, key_points').limit(10).execute()
            for article in response.data:
                # Check if JSON fields are properly converted
                tags_valid = article['tags'] is None or isinstance(article['tags'], (list, dict))
                points_valid = article['key_points'] is None or isinstance(article['key_points'], (list, dict))
                
                results.append({
                    'table': 'articles',
                    'id': article['id'],
                    'field': 'jsonb',
                    'tags_valid': tags_valid,
                    'key_points_valid': points_valid,
                    'valid': tags_valid and points_valid
                })
        except Exception as e:
            logger.error(f"Failed to test JSONB types: {e}")
        
        return results
    
    def run_tests(self) -> Dict:
        """Run all migration tests"""
        logger.info("="*60)
        logger.info("MIGRATION VALIDATION TESTS")
        logger.info("="*60)
        
        all_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        try:
            # Test 1: Record counts
            logger.info("\n--- Test 1: Record Counts ---")
            count_results = self.test_record_counts()
            all_results['tests']['record_counts'] = count_results
            
            # Test 2: Sample data
            logger.info("\n--- Test 2: Sample Data Validation ---")
            sample_results = self.test_sample_data()
            all_results['tests']['sample_data'] = sample_results
            
            # Test 3: Foreign keys
            logger.info("\n--- Test 3: Foreign Key Constraints ---")
            fk_results = self.test_foreign_keys()
            all_results['tests']['foreign_keys'] = fk_results
            
            # Test 4: Data types
            logger.info("\n--- Test 4: Data Type Conversions ---")
            type_results = self.test_data_types()
            all_results['tests']['data_types'] = type_results
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            all_results['error'] = str(e)
        finally:
            self.close_connections()
        
        # Calculate summary
        total_tests = 0
        passed_tests = 0
        
        # Count record matches
        for result in all_results['tests'].get('record_counts', []):
            total_tests += 1
            if result.get('match'):
                passed_tests += 1
        
        # Count sample data matches
        for result in all_results['tests'].get('sample_data', []):
            total_tests += 1
            if result.get('match'):
                passed_tests += 1
        
        # Count valid foreign keys (all should be valid)
        fk_issues = len(all_results['tests'].get('foreign_keys', []))
        if fk_issues == 0:
            passed_tests += 1
            total_tests += 1
        else:
            total_tests += 1
        
        # Count valid data types
        for result in all_results['tests'].get('data_types', []):
            total_tests += 1
            if result.get('valid'):
                passed_tests += 1
        
        all_results['summary'] = {
            'total_tests': total_tests,
            'passed': passed_tests,
            'failed': total_tests - passed_tests,
            'success_rate': f"{(passed_tests/total_tests*100):.2f}%" if total_tests > 0 else "0%"
        }
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {all_results['summary']['success_rate']}")
        
        if fk_issues > 0:
            logger.warning(f"Foreign Key Issues Found: {fk_issues}")
        
        logger.info("="*60)
        
        return all_results


if __name__ == "__main__":
    tester = MigrationTester()
    results = tester.run_tests()
    
    # Save results
    import json
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    if results['summary']['failed'] == 0:
        logger.info("\n✅ All tests passed!")
        sys.exit(0)
    else:
        logger.warning(f"\n⚠️ {results['summary']['failed']} tests failed!")
        sys.exit(1)