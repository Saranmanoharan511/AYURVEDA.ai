"""
Intent Router Service

Analyzes doctor's questions and selects appropriate tools.
This is the routing logic for the AI orchestrator.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from app.schemas.ai import IntentRouterRequest, IntentRouterResponse, IntentClassification
from app.services.bedrock_service import BedrockService

# Configure logging
logger = logging.getLogger(__name__)


class IntentRouter:
    """
    Intent Router for analyzing user queries and selecting tools.

    This router uses LLM-based intent classification (Bedrock) to determine
    the intent of a user query and suggest appropriate tools to use.
    Falls back to pattern-based classification if LLM is unavailable.
    """

    def __init__(self):
        self.bedrock_service = BedrockService()
    
    def route(self, request: IntentRouterRequest) -> IntentRouterResponse:
        """
        Analyze the user query and determine the intent.

        Args:
            request: IntentRouterRequest with user query and context

        Returns:
            IntentRouterResponse with classification and execution plan
        """
        logger.info(f"[INTENT ROUTER] === ROUTE START ===")
        logger.info(f"[INTENT ROUTER] User Query: {request.query}")
        logger.info(f"[INTENT ROUTER] Context: {request.context}")

        query = request.query.lower()

        # Determine primary intent
        primary_intent, confidence, secondary_intents = self._classify_intent(query)

        logger.info(f"[INTENT ROUTER] Primary Intent: {primary_intent}")
        logger.info(f"[INTENT ROUTER] Confidence: {confidence}")
        logger.info(f"[INTENT ROUTER] Secondary Intents: {secondary_intents}")

        # Build execution plan
        execution_plan = self._build_execution_plan(
            primary_intent,
            secondary_intents,
            request.context
        )

        logger.info(f"[INTENT ROUTER] Execution Plan: {execution_plan}")

        # Determine if patient context is needed
        requires_patient_context = self._needs_patient_context(query, request.context)
        logger.info(f"[INTENT ROUTER] Requires Patient Context: {requires_patient_context}")

        classification = IntentClassification(
            primary_intent=primary_intent,
            confidence=confidence,
            secondary_intents=secondary_intents,
            suggested_tools=execution_plan
        )

        logger.info(f"[INTENT ROUTER] === ROUTE COMPLETE ===")

        return IntentRouterResponse(
            classification=classification,
            execution_plan=execution_plan,
            requires_patient_context=requires_patient_context
        )
    
    def _classify_intent(self, query: str) -> tuple:
        """
        Classify the intent of the query using LLM.

        Args:
            query: Lowercase user query

        Returns:
            Tuple of (primary_intent, confidence, secondary_intents)
        """
        logger.info(f"[INTENT ROUTER] === LLM INTENT CLASSIFICATION START ===")

        # Try LLM-based classification first
        if self.bedrock_service.is_available():
            try:
                primary_intent = self._classify_intent_with_llm(query)
                logger.info(f"[INTENT ROUTER] LLM classified intent as: {primary_intent}")
                logger.info(f"[INTENT ROUTER] === LLM INTENT CLASSIFICATION COMPLETE ===")
                return primary_intent, 0.9, []  # High confidence for LLM classification
            except Exception as e:
                logger.warning(f"[INTENT ROUTER] LLM classification failed: {str(e)}, falling back to pattern matching")
        else:
            logger.warning(f"[INTENT ROUTER] Bedrock not available, falling back to pattern matching")

        # Fallback to pattern-based classification
        return self._classify_intent_with_patterns(query)

    def _classify_intent_with_llm(self, query: str) -> str:
        """
        Classify intent using LLM (Bedrock).

        Args:
            query: User query

        Returns:
            Intent classification string
        """
        from app.schemas.ai import BedrockRequest

        logger.info(f"[INTENT ROUTER] Invoking Bedrock for intent classification")
        logger.info(f"[INTENT ROUTER] Query for classification: {query}")

        prompt = f"""
You are an intent classifier for an AI medical assistant. Classify the doctor's question into one of these intents:

- sql_query: Questions about database data (patients, consultations, prescriptions, appointments, counts, lists, details, status, history in database)
- rag_search: Questions about documents, reports, medical history in uploaded files, document content
- analytics: Questions about statistics, trends, metrics, performance data
- patient_context: Questions requesting comprehensive patient overview, summary, profile
- general_question: General medical knowledge, explanations, definitions, how-to questions

Question: "{query}"

Return ONLY the intent name (one of: sql_query, rag_search, analytics, patient_context, general_question). Do not include any explanation.
"""

        bedrock_request = BedrockRequest(
            prompt=prompt,
            model_id=self.bedrock_service.model_id,
            max_tokens=50,
            temperature=0.1,
            system_prompt="You are an intent classifier. Return only the intent name."
        )

        try:
            response = self.bedrock_service.invoke_model(bedrock_request)
            intent = response.text.strip().lower()

            logger.info(f"[INTENT ROUTER] Bedrock raw response: {response.text}")
            logger.info(f"[INTENT ROUTER] Classified intent: {intent}")

            # Validate the returned intent
            valid_intents = ["sql_query", "rag_search", "analytics", "patient_context", "general_question"]
            if intent in valid_intents:
                return intent
            else:
                logger.warning(f"[INTENT ROUTER] LLM returned invalid intent: {intent}, defaulting to general_question")
                return "general_question"

        except Exception as e:
            logger.error(f"[INTENT ROUTER] LLM intent classification error: {str(e)}")
            raise

    def _classify_intent_with_patterns(self, query: str) -> tuple:
        """
        Fallback pattern-based intent classification.

        Args:
            query: Lowercase user query

        Returns:
            Tuple of (primary_intent, confidence, secondary_intents)
        """
        logger.info(f"[INTENT ROUTER] Using fallback pattern-based classification")

        # Simplified fallback patterns
        fallback_patterns = {
            "sql_query": [
                r"how many", r"count", r"number of", r"total", r"list", r"show",
                r"patient", r"consultation", r"prescription", r"appointment", r"doctor", r"medicine"
            ],
            "rag_search": [
                r"document", r"report", r"file", r"upload", r"search.*document"
            ],
            "analytics": [
                r"analytics", r"statistics", r"metrics", r"trends", r"performance"
            ],
            "patient_context": [
                r"tell me about", r"summary", r"overview", r"profile", r"context"
            ]
        }

        scores = {}

        for intent, patterns in fallback_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query):
                    score += 1
            scores[intent] = score

        # Find the highest scoring intent
        if not scores or max(scores.values()) == 0:
            logger.info(f"[INTENT ROUTER] Pattern matching found no matches, defaulting to general_question")
            return "general_question", 0.5, []

        primary_intent = max(scores, key=scores.get)
        max_score = scores[primary_intent]

        # Calculate confidence
        total_patterns = sum(len(p) for p in fallback_patterns.values())
        confidence = min(max_score / max(total_patterns * 0.3, 1), 1.0)

        logger.info(f"[INTENT ROUTER] Pattern-based classification result: {primary_intent} (confidence: {confidence})")

        return primary_intent, confidence, []
    
    def _build_execution_plan(self, primary_intent: str, secondary_intents: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build an execution plan based on the intent classification.
        
        Args:
            primary_intent: Primary intent classification
            secondary_intents: Secondary intent classifications
            context: Additional context
            
        Returns:
            List of tool execution steps
        """
        plan = []
        
        if primary_intent == "sql_query":
            plan.append({
                "tool": "sql_tool",
                "action": "execute_query",
                "priority": 1
            })
        elif primary_intent == "rag_search":
            plan.append({
                "tool": "rag_tool",
                "action": "retrieve",
                "priority": 1
            })
        elif primary_intent == "analytics":
            plan.append({
                "tool": "analytics_tool",
                "action": "calculate_metrics",
                "priority": 1
            })
        elif primary_intent == "patient_context":
            plan.append({
                "tool": "patient_context_tool",
                "action": "get_patient_context",
                "priority": 1
            })
        
        # Add secondary intents if they complement the primary
        if "rag_search" in secondary_intents and primary_intent != "rag_search":
            plan.append({
                "tool": "rag_tool",
                "action": "retrieve",
                "priority": 2
            })
        
        if "sql_query" in secondary_intents and primary_intent != "sql_query":
            plan.append({
                "tool": "sql_tool",
                "action": "execute_query",
                "priority": 2
            })
        
        # If multiple tools are needed, mark as multi-tool
        if len(plan) > 1:
            plan = [
                {
                    "tool": "multi_tool",
                    "action": "orchestrate",
                    "sub_steps": plan,
                    "priority": 1
                }
            ]
        
        return plan
    
    def _needs_patient_context(self, query: str, context: Dict[str, Any]) -> bool:
        """
        Determine if patient context is needed for the query.
        
        Args:
            query: User query
            context: Additional context
            
        Returns:
            Boolean indicating if patient context is needed
        """
        # Check if context already has patient information
        if context.get('patient_id') or context.get('client_id'):
            return False
        
        # Check if query mentions a specific patient
        patient_keywords = [
            r"patient\s+\w+",
            r"client\s+\w+",
            r"ayu-\d+",
            r"for\s+\w+\s+patient"
        ]
        
        for pattern in patient_keywords:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        # Check if query is patient-specific
        patient_specific_patterns = [
            r"their",
            r"his",
            r"her",
            r"this patient",
            r"the patient"
        ]
        
        for pattern in patient_specific_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
    
    def extract_patient_reference(self, query: str) -> Optional[str]:
        """
        Extract patient reference from query (client_id or name).
        
        Args:
            query: User query
            
        Returns:
            Patient reference string or None
        """
        # Try to extract client ID (AYU-XXXXXX format)
        client_id_match = re.search(r"AYU-\d+", query, re.IGNORECASE)
        if client_id_match:
            return client_id_match.group(0).upper()
        
        # Try to extract patient name (simple heuristic)
        name_match = re.search(r"patient\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", query)
        if name_match:
            return name_match.group(1)
        
        return None
    
    def suggest_query_type(self, query: str) -> str:
        """
        Suggest the most appropriate query type for the SQL tool.
        
        Now always uses LLM-generated SQL for maximum flexibility.
        
        Args:
            query: User query
            
        Returns:
            Always returns "llm_generated" for LLM-based SQL generation
        """
        # Always use LLM-generated SQL for all queries
        return "llm_generated"
    
    def suggest_analytics_type(self, query: str) -> str:
        """
        Suggest the most appropriate analytics metric type.
        
        Args:
            query: User query
            
        Returns:
            Suggested metric type string
        """
        query_lower = query.lower()
        
        if "monthly" in query_lower or "consultation" in query_lower:
            return "monthly_consultations"
        
        if "common" in query_lower or "condition" in query_lower:
            return "common_conditions"
        
        if "trend" in query_lower or "treatment" in query_lower:
            return "treatment_trends"
        
        if "returning" in query_lower:
            return "returning_patients"
        
        if "city" in query_lower or "location" in query_lower:
            return "city_distribution"
        
        if "follow up" in query_lower:
            return "follow_up_counts"
        
        return "monthly_consultations"  # Default
