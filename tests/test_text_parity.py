"""
Text coaching parity tests for Phase C2.

Verify that build_coaching_system_prompt produces materially equivalent
Recovery coaching context after it is routed through PathwayAdapter.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coaching.engine import load_pathway
from coaching.prompts import build_coaching_system_prompt


def make_context(stage_id, stage_name, day):
    return {
        'client': {'first_name': 'Sarah'},
        'business': {'name': "Sarah's Bakery"},
        'pathway': {'name': 'Recovery & Stabilization'},
        'current_state': {
            'stage_id': stage_id,
            'stage_name': stage_name,
            'current_day': day,
            'current_focus': '',
            'current_priorities': ''
        },
        'open_commitments': [],
        'current_risks': [],
        'recent_events': [],
        'recent_learning': [],
        'coaching_observations': [],
        'advisor_guidance': None,
        'recent_session': None
    }


class TestTextCoachingParity(unittest.TestCase):
    """Verify text prompt preserves Recovery content for each stage."""

    def _assert_recovery_prompt_content(self, prompt, stage_id, stage_name, day, objectives):
        self.assertIn('Recovery & Stabilization', prompt)
        self.assertIn(stage_name, prompt)
        self.assertIn(f'Day: {day}', prompt)
        for obj in objectives:
            self.assertIn(obj, prompt)
        self.assertIn('PATHWAY-SPECIFIC COACHING GUIDANCE', prompt)
        self.assertIn('PATHWAY GUARDRAILS', prompt)
        self.assertIn('APPROVED LEARNING RESOURCES', prompt)

    def test_rs01_prompt_content(self):
        pathway_data = load_pathway('PATHWAY-001')
        context = make_context('RS-01', 'Immediate Stabilization', 18)
        prompt = build_coaching_system_prompt(context, pathway_data)

        self._assert_recovery_prompt_content(
            prompt,
            'RS-01',
            'Immediate Stabilization',
            18,
            [
                'Establish rolling cash visibility',
                'Apply agreed spending controls',
                'Align payroll and owner compensation',
                'Prepare for lender discussion'
            ]
        )

    def test_rs02_prompt_content(self):
        pathway_data = load_pathway('PATHWAY-001')
        context = make_context('RS-02', 'Revenue Activation & Structural Tightening', 45)
        prompt = build_coaching_system_prompt(context, pathway_data)

        self._assert_recovery_prompt_content(
            prompt,
            'RS-02',
            'Revenue Activation & Structural Tightening',
            45,
            [
                'Review historical customer data',
                'Conduct targeted customer outreach',
                'Reduce slow-moving inventory',
                'Eliminate underutilized subscriptions'
            ]
        )

    def test_rs03_prompt_content(self):
        pathway_data = load_pathway('PATHWAY-001')
        context = make_context('RS-03', 'Governance & Accountability', 75)
        prompt = build_coaching_system_prompt(context, pathway_data)

        self._assert_recovery_prompt_content(
            prompt,
            'RS-03',
            'Governance & Accountability',
            75,
            [
                'Maintain weekly financial review',
                'Track revenue, expenses, and net income',
                'Monitor cash position versus plan'
            ]
        )

    def test_prompt_does_not_bypass_adapter(self):
        """The prompt should fail cleanly when the adapter cannot resolve a stage."""
        pathway_data = load_pathway('PATHWAY-001')
        context = make_context('RS-99', 'Unknown', 1)

        with self.assertRaises(Exception):
            build_coaching_system_prompt(context, pathway_data)


if __name__ == '__main__':
    unittest.main()
