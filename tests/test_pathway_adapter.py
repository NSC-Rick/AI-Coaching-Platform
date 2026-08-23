"""
Unit and parity tests for coaching.pathway_adapter.

Phase C1: PATHWAY-001 normalization only.  CM-002 remains not runtime
integrated.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coaching.engine import load_pathway
from coaching.pathway_adapter import PathwayAdapter, PathwayAdapterError


class TestPathwayAdapterParity(unittest.TestCase):
    """Verify that adapter output preserves existing PATHWAY-001 information."""

    def test_pathway_identity_preserved(self):
        legacy = load_pathway('PATHWAY-001')
        runtime = PathwayAdapter.for_pathway('PATHWAY-001')

        manifest = legacy['manifest']
        pathway = runtime['pathway']

        self.assertEqual(pathway['id'], manifest['pathway_id'])
        self.assertEqual(pathway['slug'], manifest['slug'])
        self.assertEqual(pathway['name'], manifest['name'])
        self.assertEqual(pathway['version'], manifest['version'])
        self.assertEqual(pathway['status'], manifest['status'])
        self.assertEqual(pathway['default_duration_days'], manifest['default_duration_days'])
        self.assertEqual(pathway['purpose'], manifest['purpose'])

    def test_legacy_missing_v1_fields_are_none_or_empty(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-001')

        pathway = runtime['pathway']
        self.assertIsNone(pathway['domain'])
        self.assertIsNone(pathway['target_user'])
        self.assertIsNone(pathway['entry_context'])
        self.assertIsNone(pathway['expected_outcome'])

    def test_stage_rs01_resolved(self):
        legacy = load_pathway('PATHWAY-001')
        runtime = PathwayAdapter.for_pathway('PATHWAY-001', current_stage_id='RS-01')

        legacy_stage = next(s for s in legacy['manifest']['stages'] if s['stage_id'] == 'RS-01')
        stage = runtime['current_stage']

        self.assertEqual(stage['id'], 'RS-01')
        self.assertEqual(stage['name'], legacy_stage['name'])
        self.assertEqual(stage['purpose'], legacy_stage['purpose'])
        self.assertEqual(stage['description'], legacy_stage['purpose'])
        self.assertEqual(stage['objectives'], legacy_stage['objectives'])
        self.assertEqual(stage['typical_days'], legacy_stage['typical_days'])
        self.assertEqual(stage['exit_conditions'], [])

    def test_stage_rs02_resolved(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-001', current_stage_id='RS-02')
        self.assertEqual(runtime['current_stage']['id'], 'RS-02')
        self.assertEqual(runtime['current_stage']['name'], 'Revenue Activation & Structural Tightening')

    def test_stage_rs03_resolved(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-001', current_stage_id='RS-03')
        self.assertEqual(runtime['current_stage']['id'], 'RS-03')
        self.assertEqual(runtime['current_stage']['name'], 'Governance & Accountability')

    def test_current_day_optional(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-001', current_stage_id='RS-01', current_day=18)
        self.assertEqual(runtime['current_stage']['current_day'], 18)

    def test_no_stage_id_returns_none_stage(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-001')
        self.assertIsNone(runtime['current_stage'])

    def test_unknown_stage_raises(self):
        with self.assertRaises(PathwayAdapterError):
            PathwayAdapter.for_pathway('PATHWAY-001', current_stage_id='RS-99')

    def test_unknown_pathway_raises(self):
        with self.assertRaises(PathwayAdapterError):
            PathwayAdapter.for_pathway('INVALID-PATHWAY')

    def test_coaching_content_preserved(self):
        legacy = load_pathway('PATHWAY-001')
        runtime = PathwayAdapter.for_pathway('PATHWAY-001', current_stage_id='RS-01')

        self.assertEqual(runtime['coaching']['methodology'], legacy['methodology'])
        self.assertEqual(runtime['coaching']['guidance'], legacy['coaching_guidance'])
        self.assertEqual(runtime['coaching']['guardrails'], legacy['guardrails'])

    def test_stage_guidance_extracted(self):
        legacy = load_pathway('PATHWAY-001')
        runtime = PathwayAdapter.for_pathway('PATHWAY-001', current_stage_id='RS-01')

        stage_guidance = runtime['coaching']['stage_guidance']
        # The extracted section should be a non-empty subset of the full guidance
        # and contain the distinctive RS-01 guidance about stabilization visibility.
        self.assertTrue(stage_guidance)
        self.assertIn('visibility', stage_guidance)
        self.assertLess(len(stage_guidance), len(legacy['coaching_guidance']))

    def test_resources_preserved(self):
        legacy = load_pathway('PATHWAY-001')
        runtime = PathwayAdapter.for_pathway('PATHWAY-001')

        legacy_resources = legacy['resources']['resources']
        normalized = runtime['resources']['available_resources']

        self.assertEqual(len(normalized), len(legacy_resources))
        for lr, nr in zip(legacy_resources, normalized):
            self.assertEqual(nr['resource_id'], lr.get('resource_id'))
            self.assertEqual(nr['title'], lr.get('title'))
            self.assertEqual(nr['description'], lr.get('description'))
            self.assertEqual(nr['resource_type'], lr.get('resource_type'))
            self.assertEqual(nr['location'], lr.get('location'))

    def test_unsupported_v1_sections_empty(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-001', current_stage_id='RS-01')

        self.assertEqual(runtime['development']['primary_capabilities'], [])
        self.assertEqual(runtime['development']['reinforcing_capabilities'], [])
        self.assertEqual(runtime['development']['target_behaviors'], [])
        self.assertEqual(runtime['practice']['relevant_activities'], [])
        self.assertEqual(runtime['evidence']['relevant_evidence'], [])
        self.assertEqual(runtime['completion']['criteria'], [])

    def test_progression_time_based_with_next_stage(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-001', current_stage_id='RS-01')

        progression = runtime['progression']
        self.assertEqual(progression['progression_type'], 'time_based')
        self.assertEqual(progression['from_stage'], 'RS-01')
        self.assertEqual(progression['to_stage'], 'RS-02')
        self.assertEqual(progression['evidence_considered'], [])

    def test_progression_last_stage_no_next(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-001', current_stage_id='RS-03')

        self.assertEqual(runtime['progression']['to_stage'], None)

    def test_parity_mapping(self):
        """
        Mapping table between legacy load_pathway output and normalized
        PathwayRuntimeContext.
        """
        legacy = load_pathway('PATHWAY-001')
        runtime = PathwayAdapter.for_pathway('PATHWAY-001', current_stage_id='RS-01')

        self.assertEqual(legacy['manifest']['pathway_id'], runtime['pathway']['id'])
        self.assertEqual(legacy['manifest']['name'], runtime['pathway']['name'])
        self.assertEqual(legacy['manifest']['purpose'], runtime['pathway']['purpose'])
        self.assertEqual(legacy['methodology'], runtime['coaching']['methodology'])
        self.assertEqual(legacy['coaching_guidance'], runtime['coaching']['guidance'])
        self.assertEqual(legacy['guardrails'], runtime['coaching']['guardrails'])

        legacy_stage = next(s for s in legacy['manifest']['stages'] if s['stage_id'] == 'RS-01')
        self.assertEqual(legacy_stage['stage_id'], runtime['current_stage']['id'])
        self.assertEqual(legacy_stage['name'], runtime['current_stage']['name'])
        self.assertEqual(legacy_stage['purpose'], runtime['current_stage']['purpose'])
        self.assertEqual(legacy_stage['objectives'], runtime['current_stage']['objectives'])
        self.assertEqual(legacy_stage['typical_days'], runtime['current_stage']['typical_days'])


if __name__ == '__main__':
    unittest.main()
