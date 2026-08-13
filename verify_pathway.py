#!/usr/bin/env python
"""
Simple verification script to test Pathway loading without full app dependencies.
This can be run before installing all requirements.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

try:
    import yaml
    import json
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

def verify_pathway_files():
    """Verify that all required Pathway files exist and are valid."""
    print("=" * 60)
    print("PATHWAY-001 VERIFICATION")
    print("=" * 60)
    print()
    
    pathway_dir = Path(__file__).parent / 'pathways' / 'recovery_stabilization'
    
    required_files = {
        'pathway.yaml': 'Pathway manifest',
        'methodology.md': 'Methodology documentation',
        'coaching_guidance.md': 'Coaching guidance',
        'guardrails.md': 'Guardrails',
        'milestones.json': 'Milestones',
        'resources.json': 'Resources'
    }
    
    print("Checking required files...")
    print()
    
    all_exist = True
    for filename, description in required_files.items():
        filepath = pathway_dir / filename
        exists = filepath.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {filename:25} - {description}")
        if not exists:
            all_exist = False
    
    print()
    
    if not all_exist:
        print("ERROR: Some required files are missing!")
        return False
    
    print("All required files present.")
    print()
    
    print("Validating pathway.yaml...")
    try:
        with open(pathway_dir / 'pathway.yaml', 'r', encoding='utf-8') as f:
            manifest = yaml.safe_load(f)
        
        required_fields = ['pathway_id', 'name', 'version', 'stages']
        missing_fields = [f for f in required_fields if f not in manifest]
        
        if missing_fields:
            print(f"  ✗ Missing required fields: {', '.join(missing_fields)}")
            return False
        
        print(f"  ✓ Pathway ID: {manifest['pathway_id']}")
        print(f"  ✓ Name: {manifest['name']}")
        print(f"  ✓ Version: {manifest['version']}")
        print(f"  ✓ Stages: {len(manifest['stages'])}")
        
        stage_ids = [s.get('stage_id') for s in manifest['stages']]
        if len(stage_ids) != len(set(stage_ids)):
            print("  ✗ Duplicate stage IDs found!")
            return False
        
        print(f"  ✓ Stage IDs: {', '.join(stage_ids)}")
        print()
        
    except Exception as e:
        print(f"  ✗ Error loading pathway.yaml: {e}")
        return False
    
    print("Validating milestones.json...")
    try:
        with open(pathway_dir / 'milestones.json', 'r', encoding='utf-8') as f:
            milestones_data = json.load(f)
        
        milestones = milestones_data.get('milestones', [])
        print(f"  ✓ Milestones defined: {len(milestones)}")
        
        stage_counts = {}
        for milestone in milestones:
            stage_id = milestone.get('stage_id')
            stage_counts[stage_id] = stage_counts.get(stage_id, 0) + 1
        
        for stage_id, count in sorted(stage_counts.items()):
            print(f"    - {stage_id}: {count} milestones")
        print()
        
    except Exception as e:
        print(f"  ✗ Error loading milestones.json: {e}")
        return False
    
    print("Validating resources.json...")
    try:
        with open(pathway_dir / 'resources.json', 'r', encoding='utf-8') as f:
            resources_data = json.load(f)
        
        resources = resources_data.get('resources', [])
        print(f"  ✓ Resources defined: {len(resources)}")
        
        for resource in resources:
            print(f"    - {resource.get('resource_id')}: {resource.get('title')}")
        print()
        
    except Exception as e:
        print(f"  ✗ Error loading resources.json: {e}")
        return False
    
    print("=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    print()
    print("✓ PATHWAY-001 is properly configured and ready to load.")
    print()
    
    return True

if __name__ == '__main__':
    success = verify_pathway_files()
    sys.exit(0 if success else 1)
