#!/usr/bin/env python
"""
Test that the import fix resolves the Render deployment issue.
This test verifies the import structure without requiring full dependencies.
"""

import sys
import importlib.util
from pathlib import Path

def test_coaching_init_exports():
    """Test that coaching/__init__.py exports format_context_for_display."""
    
    print("Testing coaching/__init__.py exports...")
    
    # Load the __init__.py file
    init_path = Path(__file__).parent / 'coaching' / '__init__.py'
    
    spec = importlib.util.spec_from_file_location("coaching_init", init_path)
    if spec is None or spec.loader is None:
        print("❌ FAIL: Could not load coaching/__init__.py")
        return False
    
    # Read the file content
    with open(init_path, 'r') as f:
        content = f.read()
    
    # Check that format_context_for_display is imported
    if 'format_context_for_display' not in content:
        print("❌ FAIL: format_context_for_display not found in coaching/__init__.py")
        return False
    
    # Check that it's in the import statement
    if 'from .context import' not in content or 'format_context_for_display' not in content.split('from .context import')[1].split('\n')[0]:
        print("❌ FAIL: format_context_for_display not imported from .context")
        return False
    
    # Check that it's in __all__
    if '__all__' not in content:
        print("❌ FAIL: __all__ not found in coaching/__init__.py")
        return False
    
    all_section = content.split('__all__')[1].split(']')[0]
    if 'format_context_for_display' not in all_section:
        print("❌ FAIL: format_context_for_display not in __all__")
        return False
    
    print("✓ PASS: format_context_for_display is correctly exported")
    return True

def test_context_module_defines_function():
    """Test that coaching/context.py defines format_context_for_display."""
    
    print("Testing coaching/context.py defines function...")
    
    context_path = Path(__file__).parent / 'coaching' / 'context.py'
    
    with open(context_path, 'r') as f:
        content = f.read()
    
    if 'def format_context_for_display' not in content:
        print("❌ FAIL: format_context_for_display not defined in coaching/context.py")
        return False
    
    print("✓ PASS: format_context_for_display is defined in coaching/context.py")
    return True

def test_app_imports():
    """Test that app.py imports format_context_for_display from coaching."""
    
    print("Testing app.py imports...")
    
    app_path = Path(__file__).parent / 'app.py'
    
    with open(app_path, 'r') as f:
        content = f.read()
    
    if 'from coaching import' not in content:
        print("❌ FAIL: No imports from coaching in app.py")
        return False
    
    # Find the coaching import block
    import_started = False
    import_lines = []
    for line in content.split('\n'):
        if 'from coaching import' in line:
            import_started = True
        if import_started:
            import_lines.append(line)
            if ')' in line:
                break
    
    import_block = '\n'.join(import_lines)
    
    if 'format_context_for_display' not in import_block:
        print("❌ FAIL: format_context_for_display not imported in app.py")
        return False
    
    print("✓ PASS: format_context_for_display is imported in app.py")
    return True

def main():
    print("=" * 60)
    print("IMPORT FIX VERIFICATION")
    print("=" * 60)
    print()
    
    tests = [
        test_context_module_defines_function,
        test_coaching_init_exports,
        test_app_imports
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
    
    print("=" * 60)
    if all(results):
        print("✓ ALL TESTS PASSED")
        print()
        print("The import fix is correct. The application should now:")
        print("  1. Import successfully under Gunicorn")
        print("  2. Start without ImportError")
        print("  3. Deploy successfully to Render")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("The import issue is not fully resolved.")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
