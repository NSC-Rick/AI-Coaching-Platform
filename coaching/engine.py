import os
import yaml
import json
import logging
from pathlib import Path

class PathwayLoadError(Exception):
    pass

class PathwayValidationError(Exception):
    pass

def load_pathway(pathway_id):
    base_path = Path(__file__).parent.parent / 'pathways'
    
    pathway_map = {
        'PATHWAY-001': 'recovery_stabilization',
        'PATHWAY-002': 'senior_change_leadership'
    }
    
    if pathway_id not in pathway_map:
        raise PathwayLoadError(f"Unknown pathway_id: {pathway_id}")
    
    pathway_dir = base_path / pathway_map[pathway_id]
    
    if not pathway_dir.exists():
        raise PathwayLoadError(f"Pathway directory not found: {pathway_dir}")
    
    pathway_data = {}
    
    manifest_path = pathway_dir / 'pathway.yaml'
    if not manifest_path.exists():
        raise PathwayLoadError(f"Pathway manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        pathway_data['manifest'] = yaml.safe_load(f)
    
    methodology_path = pathway_dir / 'methodology.md'
    if methodology_path.exists():
        with open(methodology_path, 'r', encoding='utf-8') as f:
            pathway_data['methodology'] = f.read()
    
    guidance_path = pathway_dir / 'coaching_guidance.md'
    if guidance_path.exists():
        with open(guidance_path, 'r', encoding='utf-8') as f:
            pathway_data['coaching_guidance'] = f.read()
    
    guardrails_path = pathway_dir / 'guardrails.md'
    if guardrails_path.exists():
        with open(guardrails_path, 'r', encoding='utf-8') as f:
            pathway_data['guardrails'] = f.read()
    
    milestones_path = pathway_dir / 'milestones.json'
    if milestones_path.exists():
        with open(milestones_path, 'r', encoding='utf-8') as f:
            pathway_data['milestones'] = json.load(f)
    
    resources_path = pathway_dir / 'resources.json'
    if resources_path.exists():
        with open(resources_path, 'r', encoding='utf-8') as f:
            pathway_data['resources'] = json.load(f)
    
    validate_pathway(pathway_data)
    
    return pathway_data

def validate_pathway(pathway_data):
    manifest = pathway_data.get('manifest')
    
    if not manifest:
        raise PathwayValidationError("Pathway manifest is missing")
    
    required_fields = ['pathway_id', 'name', 'version', 'stages']
    for field in required_fields:
        if field not in manifest:
            raise PathwayValidationError(f"Required field '{field}' missing from manifest")
    
    if not manifest['stages']:
        raise PathwayValidationError("Pathway must contain at least one stage")
    
    stage_ids = [stage.get('stage_id') for stage in manifest['stages']]
    if len(stage_ids) != len(set(stage_ids)):
        raise PathwayValidationError("Stage IDs must be unique")
    
    for stage in manifest['stages']:
        if 'stage_id' not in stage:
            raise PathwayValidationError("Each stage must have a stage_id")
        if 'name' not in stage:
            raise PathwayValidationError(f"Stage {stage.get('stage_id')} missing name")
    
    return True

def get_stage_by_id(pathway_data, stage_id):
    manifest = pathway_data.get('manifest', {})
    stages = manifest.get('stages', [])
    
    for stage in stages:
        if stage.get('stage_id') == stage_id:
            return stage
    
    return None

def get_resources_for_stage(pathway_data, stage_id):
    resources_data = pathway_data.get('resources', {})
    all_resources = resources_data.get('resources', [])
    
    return [r for r in all_resources if r.get('stage_id') == stage_id]

def get_milestones_for_stage(pathway_data, stage_id):
    milestones_data = pathway_data.get('milestones', {})
    all_milestones = milestones_data.get('milestones', [])
    
    return [m for m in all_milestones if m.get('stage_id') == stage_id]


def is_pathway_runtime_ready(pathway_id):
    """
    Determine whether a registered pathway has an executable package.

    Returns True if load_pathway succeeds and validation passes.
    Returns False for any load or validation failure.
    """
    try:
        load_pathway(pathway_id)
        return True
    except Exception as e:
        logging.info(f"Pathway {pathway_id} is not runtime ready: {type(e).__name__}: {e}")
        return False
