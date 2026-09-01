"""
Intent Router Service

Analyzes doctor's questions and selects appropriate tools.
This is the routing logic for the AI orchestrator.
"""

import re
from typing import List, Dict, Any, Optional
from app.schemas.ai import IntentRouterRequest, IntentRouterResponse, IntentClassification


class IntentRouter:
    """
    Intent Router for analyzing user queries and selecting tools.
    
    This router uses keyword matching and pattern recognition to determine
    the intent of a user query and suggest appropriate tools to use.
    """
    
    # Keyword patterns for different intents
    PATTERNS = {
        "sql_query": [
            r"how many",
            r"count of",
            r"number of",
            r"total",
            r"show me.*patients",
            r"list.*patients",
            r"waiting for",
            r"scheduled",
            r"today",
            r"this month",
            r"this week",
            r"patient count",
            r"consultation status",
            r"appointment status"
        ],
        "rag_search": [
            r"what was",
            r"previous",
            r"history",
            r"diagnosis",
            r"medicines",
            r"prescription",
            r"treatment",
            r"blood test",
            r"report",
            r"document",
            r"notes",
            r"find.*in.*documents",
            r"search.*documents"
        ],
        "analytics": [
            r"analytics",
            r"statistics",
            r"metrics",
            r"trends",
            r"common conditions",
            r"most common",
            r"treatment trends",
            r"returning patients",
            r"city distribution",
            r"follow up",
            r"monthly stats",
            r"performance"
        ],
        "patient_context": [
            r"tell me about",
            r"patient profile",
            r"patient information",
            r"summary of",
            r"overview of",
            r"patient.*context",
            r"holistic view",
            r"complete picture"
        ],
        "general_question": [
            r"what is",
            r"how do",
            r"can you",
            r"help me",
            r"explain",
            r"define"
        ]
    }
    
    def __init__(self):
        pass
    
    def route(self, request: IntentRouterRequest) -> IntentRouterResponse:
        """
        Analyze the user query and determine the intent.
        
        Args:
            request: IntentRouterRequest with user query and context
            
        Returns:
            IntentRouterResponse with classification and execution plan
        """
        query = request.query.lower()
        
        # Determine primary intent
        primary_intent, confidence, secondary_intents = self._classify_intent(query)
        
        # Build execution plan
        execution_plan = self._build_execution_plan(
            primary_intent, 
            secondary_intents, 
            request.context
        )
        
        # Determine if patient context is needed
        requires_patient_context = self._needs_patient_context(query, request.context)
        
        classification = IntentClassification(
            primary_intent=primary_intent,
            confidence=confidence,
            secondary_intents=secondary_intents,
            suggested_tools=execution_plan
        )
        
        return IntentRouterResponse(
            classification=classification,
            execution_plan=execution_plan,
            requires_patient_context=requires_patient_context
        )
    
    def _classify_intent(self, query: str) -> tuple:
        """
        Classify the intent of the query.
        
        Args:
            query: Lowercase user query
            
        Returns:
            Tuple of (primary_intent, confidence, secondary_intents)
        """
        scores = {}
        
        for intent, patterns in self.PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query):
                    score += 1
            scores[intent] = score
        
        # Find the highest scoring intent
        if not scores or max(scores.values()) == 0:
            return "general_question", 0.5, []
        
        primary_intent = max(scores, key=scores.get)
        max_score = scores[primary_intent]
        
        # Calculate confidence (normalized)
        total_patterns = sum(len(p) for p in self.PATTERNS.values())
        confidence = min(max_score / max(total_patterns * 0.3, 1), 1.0)
        
        # Find secondary intents
        secondary_intents = [
            intent for intent, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
            if intent != primary_intent and score > 0
        ][:2]
        
        return primary_intent, confidence, secondary_intents
    
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
        
        Args:
            query: User query
            
        Returns:
            Suggested query type string
        """
        query_lower = query.lower()
        
        if "how many" in query_lower or "count" in query_lower:
            if "patient" in query_lower:
                return "patient_count"
            elif "consultation" in query_lower:
                return "consultation_status"
            elif "appointment" in query_lower:
                return "appointment_status"
        
        if "today" in query_lower:
            return "today_consultations"
        
        if "month" in query_lower or "monthly" in query_lower:
            return "monthly_stats"
        
        if "search" in query_lower or "find" in query_lower:
            return "patient_search"
        
        return "patient_count"  # Default
    
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
