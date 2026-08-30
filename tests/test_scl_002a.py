"""
SCL-002A tests — generalized pathway coaching context.

Verify that build_coaching_system_prompt consumes pathway-wide coaching
guidance and guardrails for any runtime-ready pathway, while preserving
stage guidance and cross-pathway isolation.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coaching.engine import load_pathway
from coaching.prompts import build_coaching_system_prompt, extract_guardrail_summary


def make_context(stage_id, stage_name, day, client='Rick', business="Rick's Practice"):
    pathway_name = (
        'Senior Change Leadership' if 'SCL' in stage_id
        else 'Recovery & Stabilization'
    )
    return {
        'client': {'first_name': client},
        'business': {'name': business},
        'pathway': {'name': pathway_name},
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


class TestSCL002APathwayCoachingContext(unittest.TestCase):
    """Verify SCL prompt receives intended coaching identity."""

    @classmethod
    def setUpClass(cls):
        cls.pathway_data = load_pathway('PATHWAY-002')
        cls.context = make_context('SCL-01', 'Establish My Practice', 3)
        cls.prompt = build_coaching_system_prompt(cls.context, cls.pathway_data)

    def test_prompt_contains_pathway_identity(self):
        self.assertIn('Senior Change Leadership', self.prompt)
        self.assertIn('Organizational Change Management', self.prompt)
        self.assertIn('Establish My Practice', self.prompt)

    def test_prompt_contains_development_dimensions(self):
        for dimension in [
            'Strategic Change Thinking',
            'Stakeholder Influence & Alignment',
            'Executive Communication',
            'Facilitation & Leadership Presence',
            'Applied Change Judgment',
            'Reflective Practice',
        ]:
            self.assertIn(dimension, self.prompt)

    def test_prompt_contains_coaching_posture_and_behavior(self):
        prompt_lower = self.prompt.lower()
        self.assertIn('thinking partner', prompt_lower)
        self.assertIn('develop the practitioner', prompt_lower)
        self.assertIn('diagnose before prescribing', prompt_lower)
        self.assertIn('avoid manufactured criticism', prompt_lower)
        self.assertIn('validate patterns collaboratively', prompt_lower)
        self.assertIn('encourage deliberate practice', prompt_lower)
        self.assertIn('respect professional experience', prompt_lower)

    def test_prompt_contains_privacy_guidance(self):
        prompt_lower = self.prompt.lower()
        self.assertIn('privacy', prompt_lower)
        self.assertIn('anonymized', prompt_lower)

    def test_prompt_contains_pathway_wide_coaching_guidance(self):
        self.assertIn('PATHWAY-WIDE COACHING GUIDANCE', self.prompt)
        self.assertIn('PATHWAY-SPECIFIC COACHING GUIDANCE', self.prompt)

    def test_prompt_contains_scl_guardrails(self):
        self.assertIn('PATHWAY GUARDRAILS', self.prompt)
        self.assertIn('SCL-G001', self.prompt)
        self.assertIn('Professional Development, Not Task Management', self.prompt)

    def test_prompt_contains_stage_guidance(self):
        self.assertIn('SCL-01', self.prompt)
        self.assertIn('conversational baseline', self.prompt.lower())

    def test_prompt_does_not_contain_recovery_content(self):
        self.assertNotIn('RS-G001', self.prompt)
        self.assertNotIn('Stabilization Before Expansion', self.prompt)
        self.assertNotIn('Immediate Stabilization', self.prompt)


class TestSCL002ARecoveryRegression(unittest.TestCase):
    """Verify Recovery prompt still receives its own identity and guardrails."""

    @classmethod
    def setUpClass(cls):
        cls.pathway_data = load_pathway('PATHWAY-001')
        cls.context = make_context(
            'RS-01', 'Immediate Stabilization', 15,
            client='Sarah', business="Sarah's Bakery"
        )
        cls.prompt = build_coaching_system_prompt(cls.context, cls.pathway_data)

    def test_prompt_contains_recovery_identity(self):
        self.assertIn('Recovery & Stabilization', self.prompt)
        self.assertIn('Immediate Stabilization', self.prompt)

    def test_prompt_contains_recovery_pathway_wide_guidance(self):
        self.assertIn('PATHWAY-WIDE COACHING GUIDANCE', self.prompt)

    def test_prompt_contains_recovery_guardrails(self):
        self.assertIn('PATHWAY GUARDRAILS', self.prompt)
        self.assertIn('RS-G001', self.prompt)
        self.assertIn('Stabilization Before Expansion', self.prompt)

    def test_prompt_does_not_contain_scl_content(self):
        self.assertNotIn('SCL-G001', self.prompt)
        self.assertNotIn('Professional Development, Not Task Management', self.prompt)
        self.assertNotIn('Strategic Change Thinking', self.prompt)


class TestSCL002AGenericGuardrailExtraction(unittest.TestCase):
    """Guardrail extraction must be identifier-agnostic."""

    def test_scl_guardrails_are_extracted(self):
        guardrails = load_pathway('PATHWAY-002').get('guardrails', '')
        summary = extract_guardrail_summary(guardrails)
        self.assertIn('SCL-G001', summary)
        self.assertIn('Professional Development, Not Task Management', summary)
        self.assertGreater(len(summary), 0)

    def test_recovery_guardrails_are_extracted(self):
        guardrails = load_pathway('PATHWAY-001').get('guardrails', '')
        summary = extract_guardrail_summary(guardrails)
        self.assertIn('RS-G001', summary)
        self.assertIn('Stabilization Before Expansion', summary)
        self.assertGreater(len(summary), 0)


if __name__ == '__main__':
    unittest.main()
