#!/usr/bin/env python3
"""
Fix SQL syntax for PostgreSQL/Supabase compatibility
Replaces SQLite syntax with PostgreSQL equivalents
"""
import re
import os
from pathlib import Path

def fix_sql_file(filepath):
    """Fix SQL syntax in a single file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # 1. Replace ? placeholders with %s
    # Pattern to match execute statements with ?
    pattern = r'(cursor\.execute\([^)]+\?[^)]*\))'
    matches = re.findall(pattern, content)
    for match in matches:
        # Count number of ? in the match
        count = match.count('?')
        if count > 0:
            # Replace all ? with %s in this match
            new_match = match.replace('?', '%s')
            content = content.replace(match, new_match)
            changes.append(f"Replaced {count} ? with %s in execute statement")
    
    # 2. Replace datetime('now') with NOW()
    patterns = [
        (r"datetime\('now'\)", "NOW()"),
        (r"datetime\('now', '(-?\d+) hours?'\)", r"NOW() - INTERVAL '\1 hours'"),
        (r"datetime\('now', '(-?\d+) days?'\)", r"NOW() - INTERVAL '\1 days'"),
        (r"date\('now'\)", "CURRENT_DATE"),
    ]
    
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes.append(f"Replaced {pattern} with {replacement}")
    
    # 3. Replace DATE() function with ::date cast
    # Pattern: DATE(column_name) -> column_name::date
    pattern = r'DATE\(([a-zA-Z_\.]+)\)'
    if re.search(pattern, content):
        content = re.sub(pattern, r'\1::date', content)
        changes.append("Replaced DATE() with ::date cast")
    
    # 4. Replace strftime with TO_CHAR
    strftime_patterns = [
        (r"strftime\('%Y-%m-%d %H:00:00', ([^)]+)\)", r"TO_CHAR(\1, 'YYYY-MM-DD HH24:00:00')"),
        (r"strftime\('%Y-%m-%d', ([^)]+)\)", r"TO_CHAR(\1, 'YYYY-MM-DD')"),
        (r"strftime\('%H:%M:%S', ([^)]+)\)", r"TO_CHAR(\1, 'HH24:MI:SS')"),
    ]
    
    for pattern, replacement in strftime_patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes.append(f"Replaced strftime with TO_CHAR")
    
    # 5. Fix LIMIT with parameter
    # LIMIT ? -> LIMIT %s (already handled by ? replacement)
    
    # Write back if changes were made
    if content != original_content:
        # Create backup
        backup_path = str(filepath) + '.sqlite_backup'
        if not os.path.exists(backup_path):
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
        
        # Write fixed content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath, changes
    
    return None, []

def main():
    """Fix all SQL files in monitoring/api directory"""
    monitoring_dir = Path('/Users/skynet/Desktop/AI DEV/ainews-clean/monitoring/api')
    
    files_to_fix = [
        'articles.py',
        'control.py',
        'memory.py',
        'context_enrichment.py',
        'core.py',
        '__init__.py'
    ]
    
    print("🔧 Fixing SQL syntax for PostgreSQL/Supabase compatibility...")
    print("=" * 60)
    
    total_changes = 0
    for filename in files_to_fix:
        filepath = monitoring_dir / filename
        if filepath.exists():
            fixed_path, changes = fix_sql_file(filepath)
            if fixed_path:
                print(f"\n✅ Fixed: {filename}")
                for change in changes:
                    print(f"   - {change}")
                total_changes += len(changes)
            else:
                print(f"⏭️  No changes needed: {filename}")
    
    print("\n" + "=" * 60)
    print(f"✨ Total changes made: {total_changes}")
    print("📝 Backups created with .sqlite_backup extension")
    
    # Also fix migrate_monitoring.py if it exists
    migrate_file = Path('/Users/skynet/Desktop/AI DEV/ainews-clean/monitoring/migrate_monitoring.py')
    if migrate_file.exists():
        fixed_path, changes = fix_sql_file(migrate_file)
        if fixed_path:
            print(f"\n✅ Also fixed: migrate_monitoring.py")
            for change in changes:
                print(f"   - {change}")

if __name__ == "__main__":
    main()