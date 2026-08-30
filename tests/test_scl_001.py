"""
WPP-SCL-001: Senior Change Leadership Pathway Definition tests.

Verifies that the new Change Management / Senior Change Leadership pathway
loads correctly through the existing PB pathway loader and runtime, that the
legacy Recovery & Stabilization pathway remains functional, and that the
developmental dimensions and coaching posture are available to the existing
runtime without special-case hard-coded logic.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coaching.engine import load_pathway, validate_pathway
from coaching.pathway_adapter import PathwayAdapter


class TestSCL001PathwayDefinition(unittest.TestCase):
    """Verify the Senior Change Leadership pathway package."""

    def setUp(self):
        self.pathway_data = load_pathway('PATHWAY-002')
        self.manifest = self.pathway_data['manifest']

    def test_change_management_domain_present(self):
        self.assertEqual(self.manifest['domain'], 'Organizational Change Management')

    def test_senior_change_leadership_pathway_loads(self):
        self.assertIsNotNone(self.pathway_data)
        self.assertIn('manifest', self.pathway_data)
        self.assertEqual(self.manifest['pathway_id'], 'PATHWAY-002')
        self.assertEqual(self.manifest['name'], 'Senior Change Leadership')
        self.assertEqual(self.manifest['version'], '0.1')

    def test_pathway_validation_passes(self):
        self.assertTrue(validate_pathway(self.pathway_data))

    def test_six_stages_present_and_ordered(self):
        stages = self.manifest['stages']
        self.assertEqual(len(stages), 6)

        expected_ids = ['SCL-01', 'SCL-02', 'SCL-03', 'SCL-04', 'SCL-05', 'SCL-06']
        actual_ids = [s['stage_id'] for s in stages]
        self.assertEqual(actual_ids, expected_ids)

    def test_stage_names_match_requirements(self):
        stages = self.manifest['stages']
        expected_names = [
            'Establish My Practice',
            'Observe My Practice',
            'Recognize Patterns',
            'Deliberate Practice',
            'Evaluate Outcomes',
            'Demonstrate Growth'
        ]
        actual_names = [s['name'] for s in stages]
        self.assertEqual(actual_names, expected_names)

    def test_six_developmental_dimensions_defined(self):
        dimensions = self.manifest.get('development_dimensions', [])
        self.assertEqual(len(dimensions), 6)

        dimension_ids = [d['dimension_id'] for d in dimensions]
        expected_ids = [
            'strategic_change_thinking',
            'stakeholder_influence',
            'executive_communication',
            'facilitation_presence',
            'applied_change_judgment',
            'reflective_practice'
        ]
        self.assertEqual(dimension_ids, expected_ids)

    def test_methodology_coaching_and_guardrails_files_loaded(self):
        self.assertIn('methodology', self.pathway_data)
        self.assertIn('coaching_guidance', self.pathway_data)
        self.assertIn('guardrails', self.pathway_data)

    def test_coaching_posture_present(self):
        guidance = self.pathway_data['coaching_guidance']
        self.assertIn('Senior Change Leadership Coach', guidance)
        self.assertIn('Professional Thinking Partner', guidance)

    def test_milestones_present_for_each_stage(self):
        milestones = self.pathway_data['milestones']['milestones']
        for stage in self.manifest['stages']:
            stage_milestones = [m for m in milestones if m['stage_id'] == stage['stage_id']]
            self.assertGreaterEqual(len(stage_milestones), 1, f"No milestones for {stage['stage_id']}")

    def test_resources_present(self):
        resources = self.pathway_data['resources']['resources']
        self.assertGreaterEqual(len(resources), 1)


class TestSCL001RuntimeIntegration(unittest.TestCase):
    """Verify the pathway reaches the existing PB runtime unchanged."""

    def test_pathway_adapter_loads_scl_without_special_case(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-002', current_stage_id='SCL-01')

        self.assertEqual(runtime['pathway']['id'], 'PATHWAY-002')
        self.assertEqual(runtime['pathway']['name'], 'Senior Change Leadership')
        self.assertEqual(runtime['pathway']['domain'], 'Organizational Change Management')
        self.assertEqual(runtime['current_stage']['id'], 'SCL-01')
        self.assertEqual(runtime['current_stage']['name'], 'Establish My Practice')

    def test_stage_guidance_extracted_for_scl_01(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-002', current_stage_id='SCL-01')

        stage_guidance = runtime['coaching']['stage_guidance']
        self.assertTrue(stage_guidance)
        self.assertIn('conversational baseline', stage_guidance.lower())

    def test_guardrails_reach_runtime(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-002', current_stage_id='SCL-01')

        guardrails = runtime['coaching']['guardrails']
        self.assertTrue(guardrails)
        self.assertIn('Professional Development, Not Task Management', guardrails)

    def test_progression_resolves_between_stages(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-002', current_stage_id='SCL-01')

        self.assertEqual(runtime['progression']['from_stage'], 'SCL-01')
        self.assertEqual(runtime['progression']['to_stage'], 'SCL-02')

    def test_all_scl_stages_resolvable(self):
        for stage in load_pathway('PATHWAY-002')['manifest']['stages']:
            runtime = PathwayAdapter.for_pathway('PATHWAY-002', current_stage_id=stage['stage_id'])
            self.assertEqual(runtime['current_stage']['id'], stage['stage_id'])
            self.assertEqual(runtime['current_stage']['name'], stage['name'])


class TestSCL001BackwardCompatibility(unittest.TestCase):
    """Verify existing Recovery & Stabilization pathway remains intact."""

    def test_existing_recovery_stabilization_pathway_still_loads(self):
        pathway_data = load_pathway('PATHWAY-001')

        self.assertEqual(pathway_data['manifest']['pathway_id'], 'PATHWAY-001')
        self.assertEqual(pathway_data['manifest']['name'], 'Recovery & Stabilization')
        self.assertEqual(len(pathway_data['manifest']['stages']), 3)

    def test_pathway_adapter_for_legacy_pathway_still_works(self):
        runtime = PathwayAdapter.for_pathway('PATHWAY-001', current_stage_id='RS-01')

        self.assertEqual(runtime['pathway']['id'], 'PATHWAY-001')
        self.assertEqual(runtime['current_stage']['id'], 'RS-01')
        self.assertEqual(runtime['current_stage']['name'], 'Immediate Stabilization')


if __name__ == '__main__':
    unittest.main()
