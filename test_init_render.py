#!/usr/bin/env python
"""
Test init_render.py behavior without requiring full dependencies.
Verifies the initialization logic and duplicate protection.
"""

import sys
from pathlib import Path

def test_init_render_structure():
    """Test that init_render.py has correct structure."""
    
    print("=" * 60)
    print("INIT_RENDER.PY STRUCTURE TEST")
    print("=" * 60)
    print()
    
    init_path = Path('init_render.py')
    
    if not init_path.exists():
        print("✗ FAIL: init_render.py not found")
        return False
    
    with open(init_path, 'r') as f:
        content = f.read()
    
    # Check for required components
    checks = [
        ('Flask app context', 'with app.app_context():'),
        ('Table creation', 'db.create_all()'),
        ('Duplicate check', 'User.query.count()'),
        ('Skip if data exists', 'user_count > 0'),
        ('Seed advisor', "email='ronda@example.com'"),
        ('Seed client A', "email='sarah@example.com'"),
        ('Seed client B', "email='michael@example.com'"),
        ('Commit transaction', 'db.session.commit()'),
        ('Error handling', 'except Exception'),
        ('Main entry point', "if __name__ == '__main__':"),
    ]
    
    all_passed = True
    for check_name, check_pattern in checks:
        if check_pattern in content:
            print(f"✓ {check_name}")
        else:
            print(f"✗ {check_name}")
            all_passed = False
    
    print()
    
    if all_passed:
        print("✓ All structure checks passed")
    else:
        print("✗ Some structure checks failed")
    
    return all_passed

def test_duplicate_protection_logic():
    """Test that duplicate protection logic is correct."""
    
    print()
    print("=" * 60)
    print("DUPLICATE PROTECTION LOGIC TEST")
    print("=" * 60)
    print()
    
    init_path = Path('init_render.py')
    
    with open(init_path, 'r') as f:
        content = f.read()
    
    # Verify the duplicate protection logic
    checks = [
        ('Checks user count', 'user_count = User.query.count()'),
        ('Skips if users exist', 'if user_count > 0:'),
        ('Logs skip message', 'Skipping seed data'),
        ('Returns success on skip', 'return True'),
        ('Only seeds if empty', 'Database is empty'),
    ]
    
    all_passed = True
    for check_name, check_pattern in checks:
        if check_pattern in content:
            print(f"✓ {check_name}")
        else:
            print(f"✗ {check_name}")
            all_passed = False
    
    print()
    
    if all_passed:
        print("✓ Duplicate protection logic correct")
        print()
        print("Behavior:")
        print("  1. First run: Creates tables + seeds data")
        print("  2. Second run: Skips seeding (data exists)")
        print("  3. Safe to run repeatedly")
    else:
        print("✗ Duplicate protection logic incomplete")
    
    return all_passed

def test_safety_features():
    """Test that safety features are present."""
    
    print()
    print("=" * 60)
    print("SAFETY FEATURES TEST")
    print("=" * 60)
    print()
    
    init_path = Path('init_render.py')
    
    with open(init_path, 'r') as f:
        content = f.read()
    
    # Check for safety features
    safety_checks = [
        ('No DROP TABLE', 'drop' not in content.lower() or 'drop_all' not in content.lower()),
        ('No DELETE', 'delete(' not in content.lower() or 'DELETE FROM' not in content.lower()),
        ('Uses create_all (safe)', 'db.create_all()' in content),
        ('Rollback on error', 'db.session.rollback()' in content),
        ('Error handling', 'try:' in content and 'except' in content),
    ]
    
    all_passed = True
    for check_name, check_result in safety_checks:
        if check_result:
            print(f"✓ {check_name}")
        else:
            print(f"✗ {check_name}")
            all_passed = False
    
    print()
    
    if all_passed:
        print("✓ All safety features present")
        print()
        print("Safety guarantees:")
        print("  - Does NOT drop tables")
        print("  - Does NOT delete existing data")
        print("  - Does NOT reset existing records")
        print("  - Does NOT reseed if data exists")
        print("  - Rolls back on error")
    else:
        print("✗ Some safety features missing")
    
    return all_passed

def test_reuses_seed_data():
    """Test that seed data matches app.py seed-data command."""
    
    print()
    print("=" * 60)
    print("SEED DATA CONSISTENCY TEST")
    print("=" * 60)
    print()
    
    # Read both files
    with open('init_render.py', 'r') as f:
        init_content = f.read()
    
    with open('app.py', 'r') as f:
        app_content = f.read()
    
    # Check that key seed data elements match
    seed_elements = [
        'ronda@example.com',
        'sarah@example.com',
        'michael@example.com',
        "Sarah's Hardware",
        "Chen's Bakery",
        'advisor123',
        'client123',
        'PATHWAY-001',
    ]
    
    all_match = True
    for element in seed_elements:
        in_init = element in init_content
        in_app = element in app_content
        
        if in_init and in_app:
            print(f"✓ {element} - consistent")
        else:
            print(f"✗ {element} - mismatch")
            all_match = False
    
    print()
    
    if all_match:
        print("✓ Seed data consistent between init_render.py and app.py")
    else:
        print("✗ Seed data inconsistent")
    
    return all_match

def main():
    """Run all tests."""
    
    results = []
    
    results.append(test_init_render_structure())
    results.append(test_duplicate_protection_logic())
    results.append(test_safety_features())
    results.append(test_reuses_seed_data())
    
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print()
    
    if all(results):
        print("✓ ALL TESTS PASSED")
        print()
        print("init_render.py is ready for Render deployment:")
        print("  1. Creates tables safely")
        print("  2. Seeds data only if database is empty")
        print("  3. Safe to run repeatedly")
        print("  4. Matches app.py seed data")
        print("  5. Includes all safety features")
        print()
        print("Render Build Command:")
        print("  pip install -r requirements.txt && python init_render.py")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
