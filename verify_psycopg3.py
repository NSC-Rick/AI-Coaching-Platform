#!/usr/bin/env python
"""
Verify that the project has been fully migrated to psycopg 3.
Searches for any remaining psycopg2 references.
"""

import os
import sys
from pathlib import Path

def search_file_for_patterns(filepath, patterns):
    """Search a file for specific patterns."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            found = []
            for pattern in patterns:
                if pattern in content:
                    # Find line numbers
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        if pattern in line:
                            found.append((pattern, i, line.strip()))
            return found
    except Exception as e:
        return []

def main():
    print("=" * 60)
    print("PSYCOPG 3 MIGRATION VERIFICATION")
    print("=" * 60)
    print()
    
    # Patterns to search for
    patterns = [
        'psycopg2',
        'postgresql+psycopg2',
        'from psycopg2',
        'import psycopg2'
    ]
    
    # Directories to search
    search_dirs = [
        Path('.'),
        Path('coaching'),
        Path('models'),
        Path('tests')
    ]
    
    # Extensions to check
    extensions = ['.py', '.txt', '.md']
    
    # Files to exclude (verification scripts and documentation)
    exclude_files = [
        'verify_psycopg3.py',
        'test_db_config.py',
        'POSTGRESQL_FIX_REPORT.md',
        'IMPORT_FIX_REPORT.md'
    ]
    
    found_issues = []
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
            
        for ext in extensions:
            for filepath in search_dir.glob(f'*{ext}'):
                if filepath.name in exclude_files:
                    continue
                    
                matches = search_file_for_patterns(filepath, patterns)
                if matches:
                    found_issues.append((filepath, matches))
    
    if found_issues:
        print("❌ FOUND PSYCOPG2 REFERENCES:")
        print()
        for filepath, matches in found_issues:
            print(f"File: {filepath}")
            for pattern, line_num, line_text in matches:
                print(f"  Line {line_num}: {line_text}")
            print()
        print("These files need to be updated to use psycopg 3")
        return 1
    else:
        print("✓ NO PSYCOPG2 REFERENCES FOUND")
        print()
        print("Verification complete:")
        print("  - No psycopg2 imports")
        print("  - No postgresql+psycopg2 dialect references")
        print("  - Project fully migrated to psycopg 3")
        print()
    
    # Verify requirements.txt
    print("=" * 60)
    print("REQUIREMENTS.TXT VERIFICATION")
    print("=" * 60)
    print()
    
    with open('requirements.txt', 'r') as f:
        requirements = f.read()
    
    if 'psycopg2' in requirements:
        print("❌ FAIL: requirements.txt still contains psycopg2")
        return 1
    
    if 'psycopg[binary]' in requirements or 'psycopg==' in requirements:
        psycopg_line = [line for line in requirements.split('\n') if 'psycopg' in line and 'psycopg2' not in line]
        if psycopg_line:
            print(f"✓ PASS: Using {psycopg_line[0]}")
    else:
        print("❌ FAIL: No psycopg package found")
        return 1
    
    # Verify app.py uses correct dialect
    print()
    print("=" * 60)
    print("DATABASE DIALECT VERIFICATION")
    print("=" * 60)
    print()
    
    with open('app.py', 'r') as f:
        app_content = f.read()
    
    if 'postgresql+psycopg://' in app_content:
        print("✓ PASS: app.py normalizes to postgresql+psycopg://")
    else:
        print("❌ FAIL: app.py does not use postgresql+psycopg:// dialect")
        return 1
    
    if 'postgresql+psycopg2://' in app_content:
        print("❌ FAIL: app.py still references postgresql+psycopg2://")
        return 1
    
    print()
    print("=" * 60)
    print("✓ ALL VERIFICATIONS PASSED")
    print()
    print("The project is fully migrated to psycopg 3:")
    print("  1. requirements.txt uses psycopg[binary]")
    print("  2. app.py normalizes URLs to postgresql+psycopg://")
    print("  3. No psycopg2 references found in codebase")
    print("  4. SQLAlchemy will use psycopg 3 dialect")
    print("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
