import os
import json
from openai import OpenAI
from typing import Dict, List, Any, Optional

class AIServiceError(Exception):
    pass

class AIService:
    """
    AI Service abstraction layer for coaching interactions.
    Provides a clean interface to AI capabilities while keeping provider implementation replaceable.
    """
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-4-turbo-preview')
        
        if not self.api_key:
            raise AIServiceError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def generate_coaching_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        max_completion_tokens: int = 1000
    ) -> str:
        """
        Generate a coaching response based on conversation history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: System instructions for the AI coach
            max_completion_tokens: Maximum response length
            
        Returns:
            str: The AI coach's response
            
        Raises:
            AIServiceError: If the API call fails
        """
        try:
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                max_completion_tokens=max_completion_tokens
            )
            
            # DIAGNOSTIC CHECKPOINT 1: Raw OpenAI Response
            print(f"[DIAGNOSTIC] OpenAI Response ID: {response.id}")
            print(f"[DIAGNOSTIC] Model: {response.model}")
            print(f"[DIAGNOSTIC] Finish Reason: {response.choices[0].finish_reason}")
            print(f"[DIAGNOSTIC] Choices Count: {len(response.choices)}")
            print(f"[DIAGNOSTIC] Message Role: {response.choices[0].message.role}")
            print(f"[DIAGNOSTIC] Message Content Type: {type(response.choices[0].message.content)}")
            print(f"[DIAGNOSTIC] Message Content Length: {len(response.choices[0].message.content) if response.choices[0].message.content else 0}")
            print(f"[DIAGNOSTIC] Message Content Preview: {repr(response.choices[0].message.content[:100] if response.choices[0].message.content else None)}")
            
            result = response.choices[0].message.content
            
            # DIAGNOSTIC CHECKPOINT 2: AIService Return Value
            print(f"[DIAGNOSTIC] AIService Return Type: {type(result)}")
            print(f"[DIAGNOSTIC] AIService Return Value: {repr(result[:100] if result else result)}")
            
            return result
            
        except Exception as e:
            raise AIServiceError(f"Failed to generate coaching response: {str(e)}")
    
    def extract_session_outcomes(
        self,
        messages: List[Dict[str, str]],
        context: Dict[str, Any],
        extraction_prompt: str
    ) -> Dict[str, Any]:
        """
        Extract structured outcomes from a coaching session.
        
        Args:
            messages: List of session messages
            context: Current coaching context
            extraction_prompt: Instructions for extraction
            
        Returns:
            Dict containing structured extraction results
            
        Raises:
            AIServiceError: If extraction fails or returns invalid JSON
        """
        try:
            system_prompt = extraction_prompt
            
            conversation_text = "\n\n".join([
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in messages
            ])
            
            user_prompt = f"""COACHING SESSION TRANSCRIPT:

{conversation_text}

CURRENT COACHING RECORD CONTEXT:
{json.dumps(context, indent=2)}

Based on this session and the current context, extract structured updates following the exact JSON schema provided in your instructions."""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            return result
            
        except json.JSONDecodeError as e:
            raise AIServiceError(f"Failed to parse extraction JSON: {str(e)}")
        except Exception as e:
            raise AIServiceError(f"Failed to extract session outcomes: {str(e)}")
    
    def test_connection(self) -> bool:
        """
        Test the AI service connection.
        
        Returns:
            bool: True if connection is working
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_completion_tokens=5
            )
            return True
        except Exception:
            return False
