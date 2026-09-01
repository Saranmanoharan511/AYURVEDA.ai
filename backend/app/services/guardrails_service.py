"""
Guardrails Service

Amazon Bedrock Guardrails configuration and validation.
This service provides AI safety controls to prevent medical diagnosing and ensure safe outputs.
"""

import os
import json
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError

from app.schemas.ai import GuardrailsConfig


class GuardrailsService:
    """
    Bedrock Guardrails service for AI safety.
    
    This service provides methods to configure and apply guardrails
    to ensure AI responses are safe and appropriate for medical contexts.
    
    Note: AWS Code-Only Mode - This service requires actual AWS
    credentials and Bedrock access configured after Sprint 8.
    """
    
    def __init__(self):
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.guardrail_id = os.getenv("BEDROCK_GUARDRAIL_ID")
        self.guardrail_version = os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT")
        
        # Initialize Bedrock client
        try:
            self.client = boto3.client("bedrock", region_name=self.region)
        except Exception as e:
            self.client = None
            print(f"Warning: Could not initialize Bedrock client: {e}")
    
    def get_default_config(self) -> GuardrailsConfig:
        """
        Get the default guardrails configuration.
        
        Returns:
            GuardrailsConfig with default safety settings
        """
        return GuardrailsConfig(
            guardrail_id=self.guardrail_id,
            guardrail_version=self.guardrail_version,
            content_filters=[
                "HATE_SPEECH",
                "INSULTS",
                "SEXUAL",
                "VIOLENCE",
                "MISCONDUCT"
            ],
            blocked_categories=[
                "MEDICAL_ADVICE",
                "MEDICAL_DIAGNOSIS",
                "PRESCRIPTION_RECOMMENDATION"
            ],
            medical_diagnosis_blocked=True
        )
    
    def validate_output(self, text: str, config: GuardrailsConfig) -> tuple:
        """
        Validate AI output against guardrails rules.
        
        Args:
            text: AI-generated text to validate
            config: GuardrailsConfig with validation rules
            
        Returns:
            Tuple of (is_valid, blocked_reasons, filtered_text)
        """
        blocked_reasons = []
        
        # Check for medical diagnosis attempts
        if config.medical_diagnosis_blocked:
            diagnosis_keywords = [
                "diagnose",
                "diagnosis",
                "you have",
                "patient has",
                "suffering from",
                "condition is"
            ]
            
            for keyword in diagnosis_keywords:
                if keyword.lower() in text.lower():
                    blocked_reasons.append(f"Medical diagnosis keyword detected: {keyword}")
        
        # Check for prescription recommendations
        prescription_keywords = [
            "prescribe",
            "prescription",
            "take this medicine",
            "you should take",
            "recommended dosage"
        ]
        
        for keyword in prescription_keywords:
            if keyword.lower() in text.lower():
                blocked_reasons.append(f"Prescription recommendation detected: {keyword}")
        
        # Check for definitive medical advice
        definitive_phrases = [
            "this is definitely",
            "you certainly have",
            "the diagnosis is",
            "i am certain"
        ]
        
        for phrase in definitive_phrases:
            if phrase.lower() in text.lower():
                blocked_reasons.append(f"Definitive medical advice detected: {phrase}")
        
        is_valid = len(blocked_reasons) == 0
        
        # If invalid, filter the text
        filtered_text = text
        if not is_valid:
            filtered_text = self._filter_text(text, blocked_reasons)
        
        return is_valid, blocked_reasons, filtered_text
    
    def _filter_text(self, text: str, blocked_reasons: List[str]) -> str:
        """
        Filter text to remove problematic content.
        
        Args:
            text: Text to filter
            blocked_reasons: List of reasons why text was blocked
            
        Returns:
            Filtered text with warning message
        """
        warning = (
            "\n\n[AI SAFETY NOTICE: This response contains content that may not be appropriate "
            "for medical diagnosis or prescription. Please consult with a qualified healthcare "
            "professional for medical advice.]"
        )
        
        return text + warning
    
    def create_guardrail(self, config: GuardrailsConfig) -> Optional[str]:
        """
        Create a Bedrock guardrail with the given configuration.
        
        Args:
            config: GuardrailsConfig with guardrail settings
            
        Returns:
            Guardrail ID if successful, None otherwise
        """
        if not self.client:
            print("Warning: Bedrock client not initialized")
            return None
        
        try:
            response = self.client.create_guardrail(
                name="Ayurveda-AI-Guardrail",
                description="Guardrails for Ayurveda AI assistant to prevent medical diagnosis",
                contentFilters=[
                    {
                        "type": filter_type,
                        "inputStrength": "MEDIUM",
                        "outputStrength": "MEDIUM"
                    }
                    for filter_type in config.content_filters
                ],
                blockedWords=config.blocked_categories,
                blockedWordsConfig={
                    "maskStrategy": "ENTITY_TYPE_MASK"
                }
            )
            
            return response.get("guardrailId")
            
        except ClientError as e:
            print(f"Error creating guardrail: {e}")
            return None
    
    def apply_system_prompt_constraints(self, text: str) -> str:
        """
        Apply system prompt constraints to ensure safe AI behavior.
        
        Args:
            text: Text to check
            
        Returns:
            Text with safety constraints applied if needed
        """
        # Check if text contains unsafe patterns
        unsafe_patterns = [
            "I am a doctor",
            "I can diagnose",
            "I recommend treatment",
            "You should take"
        ]
        
        for pattern in unsafe_patterns:
            if pattern.lower() in text.lower():
                # Add safety disclaimer
                disclaimer = (
                    "\n\n[Disclaimer: I am an AI assistant, not a doctor. "
                    "This information is for reference only and should not replace "
                    "professional medical advice.]"
                )
                return text + disclaimer
        
        return text
    
    def check_for_prompt_injection(self, text: str) -> bool:
        """
        Check for potential prompt injection attempts.
        
        Args:
            text: Text to check
            
        Returns:
            Boolean indicating if prompt injection was detected
        """
        injection_patterns = [
            "ignore previous instructions",
            "ignore all instructions",
            "disregard system prompt",
            "override your instructions",
            "new instructions:",
            "forget everything above"
        ]
        
        for pattern in injection_patterns:
            if pattern.lower() in text.lower():
                return True
        
        return False
    
    def sanitize_input(self, text: str) -> str:
        """
        Sanitize user input to prevent prompt injection.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text
        """
        # Remove potential injection patterns
        sanitized = text
        
        injection_patterns = [
            "ignore previous instructions",
            "ignore all instructions",
            "disregard system prompt",
            "override your instructions",
            "new instructions:",
            "forget everything above"
        ]
        
        for pattern in injection_patterns:
            sanitized = sanitized.replace(pattern, "[FILTERED]")
        
        return sanitized
    
    def is_available(self) -> bool:
        """
        Check if guardrails service is available.
        
        Returns:
            Boolean indicating availability
        """
        return self.client is not None
    
    def get_guardrail_info(self, guardrail_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific guardrail.
        
        Args:
            guardrail_id: Guardrail ID
            
        Returns:
            Guardrail information dictionary or None
        """
        if not self.client:
            return None
        
        try:
            response = self.client.get_guardrail(
                guardrailIdentifier=guardrail_id
            )
            return response
        except ClientError as e:
            print(f"Error getting guardrail info: {e}")
            return None
