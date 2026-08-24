"""
Voice coaching parity tests for Phase C3.

Verify that VoiceService.build_session_config produces materially
equivalent Recovery voice configuration after it is routed through
PathwayAdapter.
"""

import os
import unittest
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coaching.engine import load_pathway
from coaching.voice_service import VoiceService
from coaching.pathway_adapter import PathwayAdapterError


class TestVoiceCoachingParity(unittest.TestCase):
    """Verify voice config preserves Recovery identity and stage for each stage."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('ELEVENLABS_API_KEY', 'test-api-key')
        os.environ.setdefault('ELEVENLABS_AGENT_ID', 'test-agent-id')

    @classmethod
    def tearDownClass(cls):
        if os.environ.get('ELEVENLABS_API_KEY') == 'test-api-key':
            os.environ.pop('ELEVENLABS_API_KEY', None)
        if os.environ.get('ELEVENLABS_AGENT_ID') == 'test-agent-id':
            os.environ.pop('ELEVENLABS_AGENT_ID', None)

    def setUp(self):
        self.voice_service = VoiceService()
        self.coaching_context = "Client: Sarah, Business: Bakery, Open commitments: call lender."

    def _build_config(self, stage, day):
        return self.voice_service.build_session_config(
            client_name='Sarah',
            business_name="Sarah's Bakery",
            pathway_data=load_pathway('PATHWAY-001'),
            current_stage=stage,
            current_day=day,
            coaching_context=self.coaching_context,
            session_id='session-1',
            user_id='user-1',
            engagement_id=1
        )

    def _assert_recovery_voice_config(self, config, stage, day, stage_name, sample_objective):
        self.assertEqual(config['agent_id'], 'test-agent-id')
        self.assertEqual(config['user_id'], 'user-1')

        metadata = config['session_metadata']
        self.assertEqual(metadata['session_id'], 'session-1')
        self.assertEqual(metadata['client_name'], 'Sarah')
        self.assertEqual(metadata['business_name'], "Sarah's Bakery")
        self.assertEqual(metadata['pathway'], 'Recovery & Stabilization')
        self.assertEqual(metadata['stage'], stage)
        self.assertEqual(metadata['day'], day)

        self.assertIn('custom_llm_extra_body', config['conversation_config_override']['agent'])
        extra = config['conversation_config_override']['agent']['custom_llm_extra_body']
        self.assertEqual(extra['app_session_id'], 'session-1')
        self.assertEqual(extra['app_engagement_id'], '1')
        self.assertEqual(extra['app_platform'], 'ai_coaching_platform')

        prompt = config['conversation_config_override']['agent']['prompt']['prompt']
        self.assertIn('AI Recovery Coach', prompt)
        self.assertIn('Sarah', prompt)
        self.assertIn("Sarah's Bakery", prompt)
        self.assertIn('Recovery & Stabilization', prompt)
        self.assertIn(stage, prompt)
        self.assertIn(f'Day {day}', prompt)
        self.assertIn(self.coaching_context, prompt)

        # C3.1: pathway coaching context must be present in the voice prompt
        self.assertIn('PATHWAY CONTEXT FOR THIS SESSION', prompt)
        self.assertIn(f'Stage: {stage_name}', prompt)
        self.assertIn('Purpose:', prompt)
        self.assertIn('Current Stage Objectives:', prompt)
        self.assertIn(sample_objective, prompt)
        self.assertIn('Coaching Guidance:', prompt)
        self.assertIn('Guardrails:', prompt)
        self.assertIn('CURRENT CLIENT CONTEXT', prompt)

    def test_rs01_voice_config(self):
        config = self._build_config('RS-01', 18)
        self._assert_recovery_voice_config(
            config, 'RS-01', 18,
            stage_name='Immediate Stabilization',
            sample_objective='Establish rolling cash visibility'
        )

    def test_rs02_voice_config(self):
        config = self._build_config('RS-02', 45)
        self._assert_recovery_voice_config(
            config, 'RS-02', 45,
            stage_name='Revenue Activation & Structural Tightening',
            sample_objective='Review historical customer data'
        )

    def test_rs03_voice_config(self):
        config = self._build_config('RS-03', 75)
        self._assert_recovery_voice_config(
            config, 'RS-03', 75,
            stage_name='Governance & Accountability',
            sample_objective='Maintain weekly financial review'
        )

    def test_voice_runtime_uses_adapter(self):
        """The resulting pathway name must come from the normalized runtime context."""
        config = self._build_config('RS-01', 18)
        # If the adapter were bypassed and the legacy pathway_data were used
        # directly, the keys would still be present. This test focuses on
        # proving the runtime goes through PathwayAdapter by checking that
        # the display values match the normalized package.
        self.assertEqual(config['session_metadata']['pathway'], 'Recovery & Stabilization')
        self.assertEqual(config['session_metadata']['stage'], 'RS-01')

    def test_unknown_stage_raises(self):
        with self.assertRaises(PathwayAdapterError):
            self._build_config('RS-99', 1)


if __name__ == '__main__':
    unittest.main()
