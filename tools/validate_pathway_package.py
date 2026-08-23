#!/usr/bin/env python
"""
Standalone Pathway Package v1 structural validator.

Does NOT modify the production runtime loader.
Does NOT replace coaching.engine.validate_pathway().

Usage:
    python tools/validate_pathway_package.py <package_path>
    python tools/validate_pathway_package.py --self-test
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


def load_yaml(path):
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Failed to load or parse YAML file: {path} ({e})")


def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load or parse JSON file: {path} ({e})")


def load_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


REQUIRED_FILES = {
    'pathway.yaml': 'Package manifest',
    'methodology.md': 'Methodology / knowledge',
    'coaching_guidance.md': 'Coaching guidance',
    'capabilities.yaml': 'Capabilities',
    'stages.yaml': 'Stages',
    'activities.json': 'Activities',
    'evidence.yaml': 'Evidence',
    'progression.yaml': 'Progression',
    'resources.json': 'Resources',
    'guardrails.md': 'Guardrails',
    'completion.yaml': 'Completion',
}

VALID_EVIDENCE_TYPES = {'observation', 'milestone', 'metric', 'reflection', 'artifact', 'advisor_assessment'}
VALID_PROGRESSION_TYPES = {'time_based', 'evidence_based', 'milestone_based', 'advisor_decision', 'hybrid'}


class PackageValidator:
    def __init__(self, package_path):
        self.package_path = Path(package_path)
        self.errors = []
        self.warnings = []
        self.data = {}

    def add_error(self, section, message):
        self.errors.append(f"[{section}] {message}")

    def add_warning(self, section, message):
        self.warnings.append(f"[{section}] {message}")

    def validate(self):
        self.data = {}

        # Package files
        self._validate_package_files()
        if self.errors:
            return False, self.errors, self.warnings

        # Identity
        self._validate_identity()

        # Capabilities
        self._validate_capabilities()

        # Stages
        self._validate_stages()

        # Activities
        self._validate_activities()

        # Evidence
        self._validate_evidence()

        # Progression
        self._validate_progression()

        # Resources
        self._validate_resources()

        # Completion
        self._validate_completion()

        # Guardrails and coaching guidance
        self._validate_narrative_files()

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_package_files(self):
        section = 'PACKAGE'
        if not self.package_path.exists():
            self.add_error(section, f"Package path does not exist: {self.package_path}")
            return

        for filename, description in REQUIRED_FILES.items():
            filepath = self.package_path / filename
            if not filepath.exists():
                self.add_error(section, f"Missing required file: {filename} ({description})")
            elif not filepath.is_file():
                self.add_error(section, f"Required path is not a file: {filename}")
            else:
                if filename.endswith('.yaml'):
                    try:
                        self.data[filename] = load_yaml(filepath)
                    except ValueError as e:
                        self.add_error(section, str(e))
                elif filename.endswith('.json'):
                    try:
                        self.data[filename] = load_json(filepath)
                    except ValueError as e:
                        self.add_error(section, str(e))
                elif filename.endswith('.md'):
                    try:
                        self.data[filename] = load_text(filepath)
                    except Exception as e:
                        self.add_error(section, f"Failed to read {filename}: {e}")

    def _validate_identity(self):
        section = 'IDENTITY'
        manifest = self.data.get('pathway.yaml') or {}

        required = ['pathway_id', 'slug', 'name', 'version', 'status', 'domain', 'purpose', 'target_user', 'entry_context', 'expected_outcome']
        for field in required:
            if field not in manifest or not manifest[field]:
                self.add_error(section, f"Missing required field: {field}")

        self._check_type(section, manifest, 'pathway_id', str)
        self._check_type(section, manifest, 'slug', str)
        self._check_type(section, manifest, 'name', str)
        self._check_type(section, manifest, 'version', (str,))
        self._check_type(section, manifest, 'status', str)
        self._check_type(section, manifest, 'domain', str)

    def _validate_capabilities(self):
        section = 'CAPABILITIES'
        cap_data = self.data.get('capabilities.yaml') or {}
        capabilities = cap_data.get('capabilities') or []

        if not capabilities:
            self.add_error(section, "At least one capability is required")
            return

        ids = set()
        for i, cap in enumerate(capabilities):
            prefix = f"capabilities[{i}]"
            for field in ['capability_id', 'name', 'description', 'target_behaviors']:
                if field not in cap or not cap[field]:
                    self.add_error(section, f"{prefix} missing or empty field: {field}")

            cap_id = cap.get('capability_id')
            if cap_id:
                if cap_id in ids:
                    self.add_error(section, f"Duplicate capability_id: {cap_id}")
                ids.add(cap_id)

            tb = cap.get('target_behaviors')
            if tb is not None and not isinstance(tb, list):
                self.add_error(section, f"{prefix} target_behaviors must be a list")

        self.data['capability_ids'] = ids

    def _validate_stages(self):
        section = 'STAGES'
        stage_data = self.data.get('stages.yaml') or {}
        stages = stage_data.get('stages') or []

        if not stages:
            self.add_error(section, "At least one stage is required")
            return

        ids = set()
        capability_ids = self.data.get('capability_ids', set())
        for i, stage in enumerate(stages):
            prefix = f"stages[{i}]"
            for field in ['stage_id', 'name', 'description', 'objectives', 'exit_conditions']:
                if field not in stage or not stage[field]:
                    self.add_error(section, f"{prefix} missing or empty field: {field}")

            stage_id = stage.get('stage_id')
            if stage_id:
                if stage_id in ids:
                    self.add_error(section, f"Duplicate stage_id: {stage_id}")
                ids.add(stage_id)

            for field in ['objectives', 'exit_conditions']:
                val = stage.get(field)
                if val is not None and not isinstance(val, list):
                    self.add_error(section, f"{prefix} {field} must be a list")

            # Legacy capability_focus support with warning
            cap_focus = stage.get('capability_focus')
            if cap_focus:
                self.add_warning(section, f"{prefix} uses deprecated 'capability_focus'; use 'primary_capabilities' and 'reinforcing_capabilities'")
                if cap_focus not in capability_ids:
                    self.add_error(section, f"{prefix} references unknown capability_id: {cap_focus}")

            # Primary / reinforcing capabilities
            self._validate_capability_list(
                section, prefix, 'primary_capabilities', stage, capability_ids, required=True
            )
            self._validate_capability_list(
                section, prefix, 'reinforcing_capabilities', stage, capability_ids, required=False
            )

            primary = stage.get('primary_capabilities') or []
            reinforcing = stage.get('reinforcing_capabilities') or []
            overlap = set(primary) & set(reinforcing)
            if overlap:
                self.add_error(section, f"{prefix} capabilities appear in both primary and reinforcing: {sorted(overlap)}")

        self.data['stage_ids'] = ids

    def _validate_activities(self):
        section = 'ACTIVITIES'
        act_data = self.data.get('activities.json') or {}
        activities = act_data.get('activities') or []

        stage_ids = self.data.get('stage_ids', set())
        capability_ids = self.data.get('capability_ids', set())
        ids = set()

        for i, act in enumerate(activities):
            prefix = f"activities[{i}]"
            for field in ['activity_id', 'title', 'description']:
                if field not in act or not act[field]:
                    self.add_error(section, f"{prefix} missing or empty field: {field}")

            act_id = act.get('activity_id')
            if act_id:
                if act_id in ids:
                    self.add_error(section, f"Duplicate activity_id: {act_id}")
                ids.add(act_id)

            stage_id = act.get('stage_id')
            if stage_id and stage_id not in stage_ids:
                self.add_error(section, f"{prefix} references unknown stage_id: {stage_id}")

            # Legacy related_capability support with warning
            legacy = act.get('related_capability')
            if legacy:
                self.add_warning(section, f"{prefix} uses deprecated 'related_capability'; use 'primary_capabilities' and 'reinforcing_capabilities'")
                if legacy not in capability_ids:
                    self.add_error(section, f"{prefix} references unknown capability_id: {legacy}")

            # Primary / reinforcing capabilities
            self._validate_capability_list(
                section, prefix, 'primary_capabilities', act, capability_ids, required=True
            )
            self._validate_capability_list(
                section, prefix, 'reinforcing_capabilities', act, capability_ids, required=False
            )

            primary = act.get('primary_capabilities') or []
            reinforcing = act.get('reinforcing_capabilities') or []
            overlap = set(primary) & set(reinforcing)
            if overlap:
                self.add_error(section, f"{prefix} capabilities appear in both primary and reinforcing: {sorted(overlap)}")

        self.data['activity_ids'] = ids

    def _validate_evidence(self):
        section = 'EVIDENCE'
        ev_data = self.data.get('evidence.yaml') or {}
        evidence = ev_data.get('evidence') or []

        stage_ids = self.data.get('stage_ids', set())
        capability_ids = self.data.get('capability_ids', set())
        ids = set()

        for i, ev in enumerate(evidence):
            prefix = f"evidence[{i}]"
            for field in ['evidence_id', 'description', 'evidence_type']:
                if field not in ev or not ev[field]:
                    self.add_error(section, f"{prefix} missing or empty field: {field}")

            ev_id = ev.get('evidence_id')
            if ev_id:
                if ev_id in ids:
                    self.add_error(section, f"Duplicate evidence_id: {ev_id}")
                ids.add(ev_id)

            etype = ev.get('evidence_type')
            if etype and etype not in VALID_EVIDENCE_TYPES:
                self.add_error(section, f"{prefix} invalid evidence_type: {etype} (valid: {sorted(VALID_EVIDENCE_TYPES)})")

            cap_id = ev.get('capability_id')
            if cap_id and cap_id not in capability_ids:
                self.add_error(section, f"{prefix} references unknown capability_id: {cap_id}")

            stage_id = ev.get('stage_id')
            if stage_id and stage_id not in stage_ids:
                self.add_error(section, f"{prefix} references unknown stage_id: {stage_id}")

        self.data['evidence_ids'] = ids

    def _validate_progression(self):
        section = 'PROGRESSION'
        prog_data = self.data.get('progression.yaml') or {}
        progressions = prog_data.get('progression') or []

        stage_ids = self.data.get('stage_ids', set())
        evidence_ids = self.data.get('evidence_ids', set())

        for i, prog in enumerate(progressions):
            prefix = f"progression[{i}]"
            for field in ['from_stage', 'to_stage', 'progression_type', 'description']:
                if field not in prog or not prog[field]:
                    self.add_error(section, f"{prefix} missing or empty field: {field}")

            from_stage = prog.get('from_stage')
            if from_stage and from_stage not in stage_ids:
                self.add_error(section, f"{prefix} references unknown from_stage: {from_stage}")

            to_stage = prog.get('to_stage')
            if to_stage and to_stage not in stage_ids:
                self.add_error(section, f"{prefix} references unknown to_stage: {to_stage}")

            ptype = prog.get('progression_type')
            if ptype and ptype not in VALID_PROGRESSION_TYPES:
                self.add_error(section, f"{prefix} invalid progression_type: {ptype} (valid: {sorted(VALID_PROGRESSION_TYPES)})")

            # Reject deprecated evidence_required
            if 'evidence_required' in prog:
                self.add_error(section, f"{prefix} uses deprecated 'evidence_required'; use 'evidence_considered'")

            ev_considered = prog.get('evidence_considered') or []
            if not isinstance(ev_considered, list):
                self.add_error(section, f"{prefix} evidence_considered must be a list")
                continue

            for ev_id in ev_considered:
                if ev_id not in evidence_ids:
                    self.add_error(section, f"{prefix} references unknown evidence_id: {ev_id}")

    def _validate_resources(self):
        section = 'RESOURCES'
        res_data = self.data.get('resources.json') or {}
        resources = res_data.get('resources') or []

        stage_ids = self.data.get('stage_ids', set())
        capability_ids = self.data.get('capability_ids', set())
        ids = set()

        for i, res in enumerate(resources):
            prefix = f"resources[{i}]"
            for field in ['resource_id', 'title', 'resource_type', 'description', 'learning_objective']:
                if field not in res or not res[field]:
                    self.add_error(section, f"{prefix} missing or empty field: {field}")

            res_id = res.get('resource_id')
            if res_id:
                if res_id in ids:
                    self.add_error(section, f"Duplicate resource_id: {res_id}")
                ids.add(res_id)

            cap_id = res.get('related_capability')
            if cap_id and cap_id not in capability_ids:
                self.add_error(section, f"{prefix} references unknown capability_id: {cap_id}")

            stage_id = res.get('related_stage')
            if stage_id and stage_id not in stage_ids:
                self.add_error(section, f"{prefix} references unknown stage_id: {stage_id}")

            location = res.get('location')
            if location is not None and not isinstance(location, str):
                self.add_error(section, f"{prefix} location must be a string or null")

    def _validate_completion(self):
        section = 'COMPLETION'
        comp_data = self.data.get('completion.yaml') or {}
        criteria = comp_data.get('completion') or []

        evidence_ids = self.data.get('evidence_ids', set())

        if not criteria:
            self.add_warning(section, "No completion criteria defined")

        ids = set()
        for i, crit in enumerate(criteria):
            prefix = f"completion[{i}]"
            for field in ['criterion_id', 'description']:
                if field not in crit or not crit[field]:
                    self.add_error(section, f"{prefix} missing or empty field: {field}")

            cid = crit.get('criterion_id')
            if cid:
                if cid in ids:
                    self.add_error(section, f"Duplicate criterion_id: {cid}")
                ids.add(cid)

            ev_list = crit.get('evidence') or []
            if not isinstance(ev_list, list):
                self.add_error(section, f"{prefix} evidence must be a list")
                continue

            for ev_id in ev_list:
                if ev_id not in evidence_ids:
                    self.add_error(section, f"{prefix} references unknown evidence_id: {ev_id}")

    def _validate_narrative_files(self):
        for filename in ['methodology.md', 'coaching_guidance.md', 'guardrails.md']:
            section = filename.replace('.md', '').replace('_', ' ').upper()
            text = self.data.get(filename)
            if text is not None and len(text.strip()) < 50:
                self.add_error(section, f"File is too short or empty: {filename}")

    def _validate_capability_list(self, section, prefix, field, obj, capability_ids, required=False):
        value = obj.get(field)
        if value is None:
            if required:
                self.add_error(section, f"{prefix} missing required field: {field}")
            return

        if not isinstance(value, list):
            self.add_error(section, f"{prefix} {field} must be a list")
            return

        if required and not value:
            self.add_error(section, f"{prefix} {field} must contain at least one capability")

        seen = set()
        for cap_id in value:
            if cap_id in seen:
                self.add_error(section, f"{prefix} {field} contains duplicate: {cap_id}")
            seen.add(cap_id)
            if cap_id not in capability_ids:
                self.add_error(section, f"{prefix} {field} references unknown capability_id: {cap_id}")

    def _check_type(self, section, obj, field, expected):
        if field in obj and obj[field] is not None:
            if not isinstance(obj[field], expected):
                self.add_error(section, f"Field {field} must be of type {expected}")


def print_report(package_path, manifest, is_valid, errors, warnings):
    print("=" * 60)
    print("PATHWAY PACKAGE VALIDATION")
    print("=" * 60)
    print()
    print(f"Package: {Path(package_path).name}")
    print(f"Path:    {package_path}")
    if manifest and 'pathway_id' in manifest:
        print(f"Pathway: {manifest.get('pathway_id')} — {manifest.get('name')}")
        print(f"Version: {manifest.get('version')}")
        print(f"Status:  {manifest.get('status')}")
    print()

    sections = ['PACKAGE', 'IDENTITY', 'CAPABILITIES', 'STAGES', 'METHODOLOGY',
                'COACHING GUIDANCE', 'ACTIVITIES', 'EVIDENCE', 'PROGRESSION',
                'RESOURCES', 'GUARDRAILS', 'COMPLETION']

    for section in sections:
        section_errors = [e for e in errors if e.startswith(f"[{section}]")]
        status = "PASS" if not section_errors else "FAIL"
        print(f"{section:25} {status}")

    if warnings:
        print()
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print()
        print("Errors:")
        for e in errors:
            print(f"  - {e}")

    print()
    print("-" * 60)
    if is_valid:
        print("STRUCTURAL VALIDATION: PASS")
    else:
        print("STRUCTURAL VALIDATION: FAIL")
    print("-" * 60)
    print()
    print("RUNTIME STATUS:        NOT INTEGRATED")
    print("ASSIGNMENT STATUS:     NOT AVAILABLE")


def run_validation(package_path):
    validator = PackageValidator(package_path)
    is_valid, errors, warnings = validator.validate()
    manifest = validator.data.get('pathway.yaml') if validator.data else {}
    print_report(package_path, manifest, is_valid, errors, warnings)
    return is_valid


def write_yaml(base, filename, data):
    import yaml
    with open(base / filename, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def write_json(base, filename, data):
    with open(base / filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def write_text(base, filename, text):
    with open(base / filename, 'w', encoding='utf-8') as f:
        f.write(text)


def self_test():
    """Run validator against a suite of intentionally invalid packages."""
    import yaml

    good_manifest = """pathway_id: TEST-001
slug: test_good
name: Test Good
version: "0.1"
status: draft
domain: Test Domain
purpose: test
target_user: test
entry_context: test
expected_outcome: test
"""

    cap_c1 = {'capability_id': 'C1', 'name': 'C', 'description': 'D', 'target_behaviors': ['b']}
    cap_c2 = {'capability_id': 'C2', 'name': 'C2', 'description': 'D', 'target_behaviors': ['b']}
    cap_c3 = {'capability_id': 'C3', 'name': 'C3', 'description': 'D', 'target_behaviors': ['b']}
    cap_c4 = {'capability_id': 'C4', 'name': 'C4', 'description': 'D', 'target_behaviors': ['b']}
    caps = [cap_c1, cap_c2, cap_c3, cap_c4]

    results = []

    def make_good_stage(stage_id, primary=None, reinforcing=None):
        stage = {
            'stage_id': stage_id,
            'name': stage_id,
            'description': 'D',
            'primary_capabilities': primary or ['C1'],
            'reinforcing_capabilities': reinforcing or [],
            'objectives': ['o'],
            'exit_conditions': ['e']
        }
        return stage

    def make_good_evidence(ev_id, cap, stage):
        return {'evidence_id': ev_id, 'capability_id': cap, 'stage_id': stage, 'description': 'D', 'evidence_type': 'observation'}

    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Reusable minimal package generator
        def minimal_with(extras=None, stages=None, activities=None, evidence=None, progression=None, resources=None, completion=None):
            d = base / extras if isinstance(extras, str) and extras else base / 'pkg'
            d.mkdir(exist_ok=True, parents=True)
            write_text(d, 'methodology.md', 'Valid methodology content.')
            write_text(d, 'coaching_guidance.md', 'Valid coaching guidance content.')
            write_text(d, 'guardrails.md', 'Valid guardrail content.')
            with open(d / 'pathway.yaml', 'w', encoding='utf-8') as f:
                f.write(good_manifest)
            write_yaml(d, 'capabilities.yaml', {'capabilities': caps})
            write_yaml(d, 'stages.yaml', {'stages': stages or [make_good_stage('S1')]})
            write_json(d, 'activities.json', {'activities': activities or []})
            write_yaml(d, 'evidence.yaml', {'evidence': evidence or []})
            write_yaml(d, 'progression.yaml', {'progression': progression or []})
            write_json(d, 'resources.json', {'resources': resources or []})
            write_yaml(d, 'completion.yaml', {'completion': completion or []})
            return d

        # Test 1: missing pathway.yaml
        d = base / 'missing_manifest'
        d.mkdir()
        write_text(d, 'methodology.md', 'some')
        write_text(d, 'coaching_guidance.md', 'some')
        write_text(d, 'guardrails.md', 'some')
        write_yaml(d, 'capabilities.yaml', {'capabilities': []})
        write_yaml(d, 'stages.yaml', {'stages': []})
        write_json(d, 'activities.json', {'activities': []})
        write_yaml(d, 'evidence.yaml', {'evidence': []})
        write_yaml(d, 'progression.yaml', {'progression': []})
        write_json(d, 'resources.json', {'resources': []})
        write_yaml(d, 'completion.yaml', {'completion': []})
        results.append(('missing pathway.yaml', not PackageValidator(d).validate()[0]))

        # Test 2: malformed YAML
        d = base / 'malformed_yaml'
        d.mkdir()
        for fn in ['methodology.md', 'coaching_guidance.md', 'guardrails.md']:
            write_text(d, fn, 'valid content to avoid empty')
        with open(d / 'pathway.yaml', 'w', encoding='utf-8') as f:
            f.write('pathway_id: TEST\n  bad: : :\n')
        write_yaml(d, 'capabilities.yaml', {'capabilities': [cap_c1]})
        write_yaml(d, 'stages.yaml', {'stages': [make_good_stage('S1')]})
        write_json(d, 'activities.json', {'activities': []})
        write_yaml(d, 'evidence.yaml', {'evidence': []})
        write_yaml(d, 'progression.yaml', {'progression': []})
        write_json(d, 'resources.json', {'resources': []})
        write_yaml(d, 'completion.yaml', {'completion': []})
        results.append(('malformed YAML', not PackageValidator(d).validate()[0]))

        # Test 3: duplicate capability_id
        d = minimal_with('dup_cap')
        write_yaml(d, 'capabilities.yaml', {'capabilities': [cap_c1, cap_c1]})
        results.append(('duplicate capability_id', not PackageValidator(d).validate()[0]))

        # Test 4: duplicate stage_id
        d = minimal_with('dup_stage')
        write_yaml(d, 'stages.yaml', {'stages': [make_good_stage('S1'), make_good_stage('S1')]})
        results.append(('duplicate stage_id', not PackageValidator(d).validate()[0]))

        # Test 5: stage references nonexistent primary capability
        d = minimal_with('bad_stage_primary')
        write_yaml(d, 'stages.yaml', {'stages': [make_good_stage('S1', primary=['UNKNOWN'])]})
        results.append(('stage references nonexistent primary capability', not PackageValidator(d).validate()[0]))

        # Test 6: stage missing primary_capabilities
        d = minimal_with('missing_primary')
        write_yaml(d, 'stages.yaml', {'stages': [{'stage_id': 'S1', 'name': 'S', 'description': 'D', 'objectives': ['o'], 'exit_conditions': ['e']}]})
        results.append(('stage missing primary_capabilities', not PackageValidator(d).validate()[0]))

        # Test 7: stage references nonexistent reinforcing capability
        d = minimal_with('bad_reinforce')
        write_yaml(d, 'stages.yaml', {'stages': [make_good_stage('S1', primary=['C1'], reinforcing=['UNKNOWN'])]})
        results.append(('stage references nonexistent reinforcing capability', not PackageValidator(d).validate()[0]))

        # Test 8: same capability in primary and reinforcing
        d = minimal_with('overlap_cap')
        write_yaml(d, 'stages.yaml', {'stages': [make_good_stage('S1', primary=['C1'], reinforcing=['C1'])]})
        results.append(('same capability in primary and reinforcing', not PackageValidator(d).validate()[0]))

        # Test 9: activity references nonexistent stage
        d = minimal_with('bad_act_stage')
        write_json(d, 'activities.json', {'activities': [
            {'activity_id': 'A1', 'stage_id': 'NOPE', 'title': 'T', 'description': 'D', 'primary_capabilities': ['C1']}
        ]})
        results.append(('activity references nonexistent stage', not PackageValidator(d).validate()[0]))

        # Test 10: activity references nonexistent capability
        d = minimal_with('bad_act_cap')
        write_json(d, 'activities.json', {'activities': [
            {'activity_id': 'A1', 'stage_id': 'S1', 'title': 'T', 'description': 'D', 'primary_capabilities': ['UNKNOWN']}
        ]})
        results.append(('activity references nonexistent capability', not PackageValidator(d).validate()[0]))

        # Test 11: activity duplicates capability reference
        d = minimal_with('dup_act_cap')
        write_json(d, 'activities.json', {'activities': [
            {'activity_id': 'A1', 'stage_id': 'S1', 'title': 'T', 'description': 'D', 'primary_capabilities': ['C1', 'C1']}
        ]})
        results.append(('activity duplicates capability reference', not PackageValidator(d).validate()[0]))

        # Test 12: invalid evidence_type
        d = minimal_with('bad_ev_type')
        write_yaml(d, 'evidence.yaml', {'evidence': [
            {'evidence_id': 'E1', 'capability_id': 'C1', 'stage_id': 'S1', 'description': 'D', 'evidence_type': 'bad_type'}
        ]})
        results.append(('invalid evidence_type', not PackageValidator(d).validate()[0]))

        # Test 13: invalid progression_type
        d = minimal_with('bad_prog_type')
        write_yaml(d, 'evidence.yaml', {'evidence': [make_good_evidence('E1', 'C1', 'S1')]})
        write_yaml(d, 'progression.yaml', {'progression': [
            {'from_stage': 'S1', 'to_stage': 'S1', 'progression_type': 'bad', 'description': 'D', 'evidence_considered': []}
        ]})
        results.append(('invalid progression_type', not PackageValidator(d).validate()[0]))

        # Test 14: progression evidence references nonexistent evidence ID
        d = minimal_with('bad_prog_evidence')
        write_yaml(d, 'progression.yaml', {'progression': [
            {'from_stage': 'S1', 'to_stage': 'S1', 'progression_type': 'evidence_based', 'description': 'D', 'evidence_considered': ['NOPE']}
        ]})
        results.append(('progression evidence references nonexistent evidence ID', not PackageValidator(d).validate()[0]))

        # Test 15: deprecated evidence_required used instead of evidence_considered
        d = minimal_with('deprecated_required')
        write_yaml(d, 'evidence.yaml', {'evidence': [make_good_evidence('E1', 'C1', 'S1')]})
        write_yaml(d, 'progression.yaml', {'progression': [
            {'from_stage': 'S1', 'to_stage': 'S1', 'progression_type': 'evidence_based', 'description': 'D', 'evidence_required': ['E1']}
        ]})
        results.append(('deprecated evidence_required used', not PackageValidator(d).validate()[0]))

        # Test 16: duplicate resource_id
        d = minimal_with('dup_res')
        write_json(d, 'resources.json', {'resources': [
            {'resource_id': 'R1', 'title': 'T', 'resource_type': 'guide', 'description': 'D', 'learning_objective': 'L', 'when_to_recommend': []},
            {'resource_id': 'R1', 'title': 'T2', 'resource_type': 'guide', 'description': 'D2', 'learning_objective': 'L', 'when_to_recommend': []},
        ]})
        results.append(('duplicate resource_id', not PackageValidator(d).validate()[0]))

        # Test 17: missing coaching guidance
        d = base / 'missing_guidance'
        d.mkdir()
        write_text(d, 'methodology.md', 'Valid methodology content.')
        write_text(d, 'guardrails.md', 'Valid guardrail content.')
        with open(d / 'pathway.yaml', 'w', encoding='utf-8') as f:
            f.write(good_manifest)
        write_yaml(d, 'capabilities.yaml', {'capabilities': [cap_c1]})
        write_yaml(d, 'stages.yaml', {'stages': [make_good_stage('S1')]})
        write_json(d, 'activities.json', {'activities': []})
        write_yaml(d, 'evidence.yaml', {'evidence': []})
        write_yaml(d, 'progression.yaml', {'progression': []})
        write_json(d, 'resources.json', {'resources': []})
        write_yaml(d, 'completion.yaml', {'completion': []})
        results.append(('missing coaching guidance', not PackageValidator(d).validate()[0]))

        # Test 18: missing guardrails
        d = base / 'missing_guardrails'
        d.mkdir()
        write_text(d, 'methodology.md', 'Valid methodology content.')
        write_text(d, 'coaching_guidance.md', 'Valid coaching guidance content.')
        with open(d / 'pathway.yaml', 'w', encoding='utf-8') as f:
            f.write(good_manifest)
        write_yaml(d, 'capabilities.yaml', {'capabilities': [cap_c1]})
        write_yaml(d, 'stages.yaml', {'stages': [make_good_stage('S1')]})
        write_json(d, 'activities.json', {'activities': []})
        write_yaml(d, 'evidence.yaml', {'evidence': []})
        write_yaml(d, 'progression.yaml', {'progression': []})
        write_json(d, 'resources.json', {'resources': []})
        write_yaml(d, 'completion.yaml', {'completion': []})
        results.append(('missing guardrails', not PackageValidator(d).validate()[0]))

    print()
    print("=" * 60)
    print("INVALID-PACKAGE SELF-TEST RESULTS")
    print("=" * 60)
    all_passed = True
    for name, invalid_detected in results:
        status = "PASS" if invalid_detected else "FAIL"
        if not invalid_detected:
            all_passed = False
        print(f"{name:52} {status}")
    print("=" * 60)
    if all_passed:
        print("ALL SELF-TESTS PASSED")
    else:
        print("SOME SELF-TESTS FAILED")
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Validate a Pathway Package v1")
    parser.add_argument('package_path', nargs='?', help="Path to package directory")
    parser.add_argument('--self-test', action='store_true', help='Run invalid-package self-tests')
    args = parser.parse_args()

    if args.self_test:
        ok = self_test()
        sys.exit(0 if ok else 1)

    if not args.package_path:
        parser.print_help()
        sys.exit(1)

    is_valid = run_validation(args.package_path)
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
