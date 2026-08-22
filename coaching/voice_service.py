"""
Voice Service - ElevenLabs Integration

This module provides a clean abstraction for ElevenLabs Conversational AI integration.
It handles signed URL generation for secure agent authentication and conversation management.

Build 003 - Voice Integration
"""

import os
import requests
from typing import Optional, Dict, Any


class VoiceService:
    """
    Abstraction layer for ElevenLabs Conversational AI.
    
    This service handles:
    - Signed URL generation for secure agent access
    - Session configuration with client context
    - Conversation metadata management
    
    The actual voice interaction happens client-side using the ElevenLabs SDK.
    This service provides the server-side support for secure authentication and context.
    """
    
    def __init__(self):
        """Initialize the voice service with ElevenLabs configuration."""
        self.api_key = os.environ.get('ELEVENLABS_API_KEY')
        self.agent_id = os.environ.get('ELEVENLABS_AGENT_ID')
        self.api_base = 'https://api.elevenlabs.io/v1'
        
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is required")
        if not self.agent_id:
            raise ValueError("ELEVENLABS_AGENT_ID environment variable is required")
    
    def generate_signed_url(self, session_id: Optional[str] = None, engagement_id: Optional[int] = None) -> Dict[str, str]:
        """
        Generate a signed URL for secure ElevenLabs agent access.
        
        This is required for private agents. The signed URL provides temporary
        authenticated access to the conversational agent.
        
        Voice Spike 001D-1: Identity Round-Trip
        Application identity metadata (session_id, engagement_id) is passed to
        build_session_config() and included in the conversation configuration,
        not in the signed URL request itself.
        
        Args:
            session_id: Optional application session ID (stored for config, not used in URL request)
            engagement_id: Optional engagement ID (stored for config, not used in URL request)
        
        Returns:
            dict: Contains 'signed_url' for client-side connection
            
        Raises:
            Exception: If the API request fails
        """
        try:
            url = f"{self.api_base}/convai/conversation/get-signed-url"
            params = {'agent_id': self.agent_id}
            headers = {'xi-api-key': self.api_key}
            
            # ElevenLabs API requires GET method for signed URL generation
            # Identity metadata is passed via conversation config, not here
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Store identity metadata for later use in session config
            result = {'signed_url': data.get('signed_url')}
            if session_id or engagement_id:
                result['metadata'] = {
                    'app_session_id': str(session_id) if session_id else None,
                    'app_engagement_id': str(engagement_id) if engagement_id else None,
                    'app_platform': 'ai_coaching_platform'
                }
            
            return result
            
        except requests.exceptions.RequestException as e:
            # Enhanced error logging for diagnosis (without exposing secrets)
            import logging
            logging.error("=" * 60)
            logging.error("ELEVENLABS SIGNED URL REQUEST FAILED")
            logging.error("=" * 60)
            logging.error(f"Request URL: {url}")
            logging.error(f"Request method: GET")
            logging.error(f"Agent ID: {self.agent_id}")
            logging.error(f"API key configured: {'Yes' if self.api_key else 'No'}")
            logging.error(f"API key length: {len(self.api_key) if self.api_key else 0} characters")
            logging.error(f"Header name used: xi-api-key")
            
            if hasattr(e, 'response') and e.response is not None:
                logging.error(f"HTTP status code: {e.response.status_code}")
                logging.error(f"Response headers: {dict(e.response.headers)}")
                
                # Log response body if available (sanitized)
                try:
                    response_body = e.response.text
                    # Don't log if it contains tokens or keys
                    if response_body and len(response_body) < 1000:
                        logging.error(f"Response body: {response_body}")
                    else:
                        logging.error(f"Response body length: {len(response_body)} characters")
                except:
                    logging.error("Could not read response body")
            else:
                logging.error(f"No response object available")
            
            logging.error(f"Exception type: {type(e).__name__}")
            logging.error(f"Exception message: {str(e)}")
            logging.error("=" * 60)
            
            raise Exception(f"Failed to generate ElevenLabs signed URL: {str(e)}")
    
    def build_session_config(
        self,
        client_name: str,
        business_name: str,
        pathway_name: str,
        current_stage: str,
        current_day: int,
        coaching_context: str,
        session_id: str,
        user_id: str,
        engagement_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build session configuration with client context for the voice agent.
        
        This configuration will be used to initialize the ElevenLabs conversation
        with relevant client context, ensuring the voice coach has the same
        information as the text-based coach.
        
        Voice Spike 001D-1: Identity metadata is included in the conversation
        configuration to enable round-trip through the post-call webhook.
        
        Args:
            client_name: Client's preferred name
            business_name: Business name
            pathway_name: Current pathway name
            current_stage: Current pathway stage
            current_day: Day in pathway
            coaching_context: Full coaching context from context builder
            session_id: Session ID for tracking
            user_id: User ID for tracking
            engagement_id: Optional engagement ID for identity round-trip
            
        Returns:
            dict: Configuration object for client-side initialization
        """
        config = {
            'agent_id': self.agent_id,
            'user_id': user_id,
            'session_metadata': {
                'session_id': session_id,
                'client_name': client_name,
                'business_name': business_name,
                'pathway': pathway_name,
                'stage': current_stage,
                'day': current_day
            },
            'conversation_config_override': {
                'agent': {
                    'prompt': {
                        'prompt': self._build_agent_prompt(
                            client_name,
                            business_name,
                            pathway_name,
                            current_stage,
                            current_day,
                            coaching_context
                        )
                    }
                }
            }
        }
        
        # Voice Spike 001D-1: Add identity metadata for webhook round-trip
        # This metadata will be returned in the post-call webhook
        if session_id or engagement_id:
            config['conversation_config_override']['agent']['custom_llm_extra_body'] = {
                'app_session_id': str(session_id) if session_id else None,
                'app_engagement_id': str(engagement_id) if engagement_id else None,
                'app_platform': 'ai_coaching_platform'
            }
        
        return config
    
    def _build_agent_prompt(
        self,
        client_name: str,
        business_name: str,
        pathway_name: str,
        current_stage: str,
        current_day: int,
        coaching_context: str
    ) -> str:
        """
        Build the agent prompt with client context.
        
        This prompt provides the ElevenLabs agent with the same context
        that the Build 002 text coach receives, ensuring consistent
        coaching behavior across interaction channels.
        
        Args:
            client_name: Client's preferred name
            business_name: Business name
            pathway_name: Current pathway name
            current_stage: Current pathway stage
            current_day: Day in pathway
            coaching_context: Full coaching context from context builder
            
        Returns:
            str: Complete agent prompt with context
        """
        prompt = f"""You are an AI Recovery Coach supporting {client_name} who owns {business_name}.

You are working within the {pathway_name} pathway, currently in {current_stage} (Day {current_day}).

COACHING STYLE:
- Be calm, practical, and supportive
- Ask useful questions
- Work from known facts
- Recognize progress
- Follow up on commitments
- Help turn intentions into actions
- Respect advisor guidance
- Apply pathway guardrails
- Escalate appropriately when needed

IMPORTANT BEHAVIORAL RULES:
- Sound natural and conversational
- Do NOT sound like a questionnaire
- Do NOT lecture unnecessarily
- Do NOT pretend to be the human advisor
- Do NOT fabricate facts or invent resources
- Do NOT reveal internal implementation details

CURRENT CLIENT CONTEXT:
{coaching_context}

Your role is to help {client_name} make progress through the pathway using appropriate coaching behavior.
Remember what has been discussed and build on previous conversations naturally."""

        return prompt
    
    def validate_conversation_data(self, conversation_data: Dict[str, Any]) -> bool:
        """
        Validate conversation data structure.
        
        Args:
            conversation_data: Conversation data from client
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['session_id']
        return all(field in conversation_data for field in required_fields)
    
    def normalize_conversation_to_messages(
        self,
        conversation_data: Dict[str, Any]
    ) -> list:
        """
        Normalize ElevenLabs conversation data into SessionMessage format.
        
        This converts the ElevenLabs conversation format into the standard
        SessionMessage format used by the Build 002 extraction pipeline.
        
        Args:
            conversation_data: Raw conversation data from ElevenLabs
            
        Returns:
            list: List of message dictionaries in SessionMessage format
        """
        messages = []
        
        # ElevenLabs may provide conversation history in various formats
        # This is a placeholder for the actual normalization logic
        # The exact format will depend on what ElevenLabs returns
        
        if 'messages' in conversation_data:
            for msg in conversation_data['messages']:
                messages.append({
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', ''),
                    'timestamp': msg.get('timestamp')
                })
        
        # If ElevenLabs provides a transcript instead
        elif 'transcript' in conversation_data:
            transcript = conversation_data['transcript']
            if isinstance(transcript, list):
                for entry in transcript:
                    messages.append({
                        'role': entry.get('speaker', 'user'),
                        'content': entry.get('text', ''),
                        'timestamp': entry.get('timestamp')
                    })
        
        return messages
    
    def get_conversation_metadata(
        self,
        conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract metadata from conversation data.
        
        Args:
            conversation_data: Conversation data from client
            
        Returns:
            dict: Metadata including duration, status, etc.
        """
        return {
            'duration': conversation_data.get('duration'),
            'status': conversation_data.get('status', 'completed'),
            'elevenlabs_conversation_id': conversation_data.get('conversation_id'),
            'error': conversation_data.get('error')
        }


# Singleton instance
_voice_service = None


def get_voice_service() -> VoiceService:
    """
    Get or create the VoiceService singleton instance.
    
    Returns:
        VoiceService: The voice service instance
    """
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
