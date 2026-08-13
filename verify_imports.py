#!/usr/bin/env python
"""
Verify that all imports from the coaching package are correctly exported.
This script checks the import structure without requiring dependencies.
"""

import ast
import sys
from pathlib import Path

def get_imports_from_file(filepath):
    """Extract imports from a Python file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module == 'coaching':
                for alias in node.names:
                    imports.append(alias.name)
    
    return imports

def get_exports_from_init(init_path):
    """Extract __all__ exports from __init__.py."""
    with open(init_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '__all__':
                    if isinstance(node.value, ast.List):
                        return [elt.s if isinstance(elt, ast.Str) else elt.value for elt in node.value.elts]
    
    return []

def main():
    base_path = Path(__file__).parent
    
    print("=" * 60)
    print("IMPORT VERIFICATION")
    print("=" * 60)
    print()
    
    # Get imports from app.py
    app_imports = get_imports_from_file(base_path / 'app.py')
    print(f"Imports from 'coaching' in app.py:")
    for imp in sorted(app_imports):
        print(f"  - {imp}")
    print()
    
    # Get exports from coaching/__init__.py
    coaching_exports = get_exports_from_init(base_path / 'coaching' / '__init__.py')
    print(f"Exports from coaching/__init__.py:")
    for exp in sorted(coaching_exports):
        print(f"  - {exp}")
    print()
    
    # Check for missing exports
    missing = set(app_imports) - set(coaching_exports)
    
    if missing:
        print("❌ MISSING EXPORTS:")
        for m in sorted(missing):
            print(f"  - {m}")
        print()
        print("These imports are used in app.py but not exported from coaching/__init__.py")
        return 1
    else:
        print("✓ All imports are correctly exported")
        print()
        return 0

if __name__ == '__main__':
    sys.exit(main())
