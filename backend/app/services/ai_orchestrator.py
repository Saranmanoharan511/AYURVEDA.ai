"""
AI Orchestrator Service

LangGraph-style orchestration for multi-step AI tool execution.
This service coordinates the AI tools and Bedrock to answer doctor questions.
"""

import time
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.schemas.ai import (
    OrchestrationRequest, OrchestrationResponse, OrchestratorState,
    ChatRequest, ChatResponse, ToolExecution
)
from app.services.intent_router import IntentRouter
from app.services.sql_tool import SQLTool
from app.services.patient_context_tool import PatientContextTool
from app.services.rag_tool import RAGTool
from app.services.analytics_tool import AnalyticsTool
from app.services.bedrock_service import BedrockService
from app.services.guardrails_service import GuardrailsService


class AIOrchestrator:
    """
    AI Orchestrator for multi-step tool execution and LLM coordination.
    
    This orchestrator implements a graph-based workflow:
    1. Analyze user query with Intent Router
    2. Execute appropriate tools (SQL, RAG, Analytics, Patient Context)
    3. Aggregate evidence from tools
    4. Synthesize response with Bedrock
    5. Apply guardrails for safety
    6. Return grounded response to user
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Initialize tools
        self.intent_router = IntentRouter()
        self.sql_tool = SQLTool(db)
        self.patient_context_tool = PatientContextTool(db)
        self.rag_tool = RAGTool(db)
        self.analytics_tool = AnalyticsTool(db)
        self.bedrock_service = BedrockService()
        self.guardrails_service = GuardrailsService()
    
    def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResponse:
        """
        Orchestrate the complete AI workflow.
        
        Args:
            request: OrchestrationRequest with user query and context
            
        Returns:
            OrchestrationResponse with final answer and execution history
        """
        start_time = time.time()
        
        # Initialize orchestrator state
        state = OrchestratorState(
            user_query=request.query,
            patient_id=request.patient_id,
            consultation_id=request.consultation_id,
            context=request.context
        )
        
        try:
            # Step 1: Route intent
            state = self._route_intent(state)
            
            # Step 2: Execute tools based on intent
            state = self._execute_tools(state)
            
            # Step 3: Aggregate evidence
            state = self._aggregate_evidence(state)
            
            # Step 4: Synthesize response with Bedrock
            state = self._synthesize_response(state)
            
            # Step 5: Apply guardrails
            state = self._apply_guardrails(state)
            
            orchestration_time = (time.time() - start_time) * 1000
            
            # Extract sources from tool results
            sources = self._extract_sources(state)
            
            return OrchestrationResponse(
                final_response=state.final_response,
                tool_executions=state.execution_history,
                sources=sources,
                confidence=self._calculate_confidence(state),
                orchestration_time_ms=orchestration_time
            )
            
        except Exception as e:
            orchestration_time = (time.time() - start_time) * 1000
            raise Exception(f"AI Orchestration failed: {str(e)}")
    
    def _route_intent(self, state: OrchestratorState) -> OrchestratorState:
        """
        Route the user query to determine intent.
        
        Args:
            state: Current orchestrator state
            
        Returns:
            Updated state with intent classification
        """
        from app.schemas.ai import IntentRouterRequest
        
        router_request = IntentRouterRequest(
            query=state.user_query,
            context=state.context
        )
        
        router_response = self.intent_router.route(router_request)
        state.intent_classification = router_response.classification
        state.current_step = "intent_routed"
        
        return state
    
    def _execute_tools(self, state: OrchestratorState) -> OrchestratorState:
        """
        Execute tools based on intent classification.
        
        Args:
            state: Current orchestrator state
            
        Returns:
            Updated state with tool results
        """
        tool_executions = []
        
        # Extract patient reference if needed
        patient_reference = self.intent_router.extract_patient_reference(state.user_query)
        if patient_reference and not state.patient_id:
            # Convert client_id to patient_id
            patient_info = self.sql_tool.get_patient_by_client_id(patient_reference)
            if patient_info:
                state.patient_id = patient_info['patient_id']
        
        # Execute tools based on execution plan
        for step in state.intent_classification.suggested_tools:
            tool_name = step.get('tool')
            action = step.get('action')
            
            try:
                tool_start = time.time()
                
                if tool_name == "multi_tool":
                    # Execute multi-tool orchestration
                    result = self._execute_multi_tool(state, step.get('sub_steps', []))
                    state.tool_results['multi_tool'] = result
                elif tool_name == "sql_tool":
                    result = self._execute_sql_tool(state)
                    state.tool_results['sql'] = result
                elif tool_name == "rag_tool":
                    result = self._execute_rag_tool(state)
                    state.tool_results['rag'] = result
                elif tool_name == "analytics_tool":
                    result = self._execute_analytics_tool(state)
                    state.tool_results['analytics'] = result
                elif tool_name == "patient_context_tool":
                    result = self._execute_patient_context_tool(state)
                    state.tool_results['patient_context'] = result
                else:
                    # Unknown tool, skip
                    result = {"error": f"Unknown tool: {tool_name}"}
                    state.tool_results[tool_name] = result
                
                tool_time = (time.time() - tool_start) * 1000
                
                tool_executions.append(ToolExecution(
                    tool_name=tool_name,
                    input_data=step,
                    output_data=result if isinstance(result, dict) else {"result": str(result)},
                    execution_time_ms=tool_time,
                    success=True
                ))
                
            except Exception as e:
                tool_executions.append(ToolExecution(
                    tool_name=tool_name,
                    input_data=step,
                    output_data=None,
                    execution_time_ms=0,
                    success=False,
                    error_message=str(e)
                ))
        
        state.execution_history = tool_executions
        state.current_step = "tools_executed"
        
        return state
    
    def _execute_sql_tool(self, state: OrchestratorState) -> Dict[str, Any]:
        """Execute SQL tool based on query type."""
        from app.schemas.ai import SQLToolRequest
        
        query_type = self.intent_router.suggest_query_type(state.user_query)
        
        request = SQLToolRequest(
            query_type=query_type,
            patient_id=state.patient_id,
            doctor_id=state.context.get('doctor_id')
        )
        
        response = self.sql_tool.execute_query(request)
        return {
            "query_type": response.query_type,
            "results": response.results,
            "row_count": response.row_count
        }
    
    def _execute_rag_tool(self, state: OrchestratorState) -> Dict[str, Any]:
        """Execute RAG tool for document retrieval."""
        from app.schemas.ai import RAGToolRequest
        
        request = RAGToolRequest(
            query=state.user_query,
            patient_id=state.patient_id,
            consultation_id=state.consultation_id,
            top_k=5
        )
        
        response = self.rag_tool.retrieve(request)
        return {
            "chunks": response.chunks,
            "chunk_count": response.chunk_count
        }
    
    def _execute_analytics_tool(self, state: OrchestratorState) -> Dict[str, Any]:
        """Execute Analytics tool for metrics."""
        from app.schemas.ai import AnalyticsToolRequest
        
        metric_type = self.intent_router.suggest_analytics_type(state.user_query)
        
        request = AnalyticsToolRequest(
            metric_type=metric_type,
            doctor_id=state.context.get('doctor_id')
        )
        
        response = self.analytics_tool.calculate_metrics(request)
        return {
            "metric_type": response.metric_type,
            "results": response.results,
            "summary": response.summary
        }
    
    def _execute_patient_context_tool(self, state: OrchestratorState) -> Dict[str, Any]:
        """Execute Patient Context tool."""
        from app.schemas.ai import PatientContextRequest
        
        if not state.patient_id:
            return {"error": "Patient ID required for patient context"}
        
        request = PatientContextRequest(
            patient_id=state.patient_id,
            include_consultations=True,
            include_documents=True,
            include_appointments=True
        )
        
        response = self.patient_context_tool.get_patient_context(request)
        return {
            "patient_id": response.patient_id,
            "client_id": response.client_id,
            "profile": response.profile,
            "consultations": response.consultations,
            "documents": response.documents,
            "appointments": response.appointments
        }
    
    def _execute_multi_tool(self, state: OrchestratorState, sub_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute multiple tools in sequence for multi-tool orchestration.
        
        Args:
            state: Current orchestrator state
            sub_steps: List of tool execution steps
            
        Returns:
            Dict with combined results from all sub-tools
        """
        results = {}
        
        for sub_step in sub_steps:
            tool_name = sub_step.get('tool')
            action = sub_step.get('action')
            
            try:
                if tool_name == "sql_tool":
                    result = self._execute_sql_tool(state)
                    results['sql'] = result
                elif tool_name == "rag_tool":
                    result = self._execute_rag_tool(state)
                    results['rag'] = result
                elif tool_name == "analytics_tool":
                    result = self._execute_analytics_tool(state)
                    results['analytics'] = result
                elif tool_name == "patient_context_tool":
                    result = self._execute_patient_context_tool(state)
                    results['patient_context'] = result
            except Exception as e:
                results[f'{tool_name}_error'] = str(e)
        
        return results
    
    def _aggregate_evidence(self, state: OrchestratorState) -> OrchestratorState:
        """
        Aggregate evidence from tool results.
        
        Args:
            state: Current orchestrator state
            
        Returns:
            Updated state with aggregated evidence
        """
        evidence_parts = []
        
        # Merge multi_tool results into main tool_results for aggregation
        if 'multi_tool' in state.tool_results and isinstance(state.tool_results['multi_tool'], dict):
            multi_tool_results = state.tool_results['multi_tool']
            for tool_name, tool_result in multi_tool_results.items():
                # Only merge if not already present in main results
                if tool_name not in state.tool_results:
                    state.tool_results[tool_name] = tool_result
        
        # Format SQL results
        if 'sql' in state.tool_results:
            sql_result = state.tool_results['sql']
            evidence_parts.append(f"SQL Query Results:\n{sql_result}")
        
        # Format RAG results
        if 'rag' in state.tool_results:
            rag_result = state.tool_results['rag']
            evidence_parts.append(f"Document Retrieval Results:\n{rag_result}")
        
        # Format Analytics results
        if 'analytics' in state.tool_results:
            analytics_result = state.tool_results['analytics']
            evidence_parts.append(f"Analytics Results:\n{analytics_result}")
        
        # Format Patient Context
        if 'patient_context' in state.tool_results:
            patient_context = state.tool_results['patient_context']
            formatted_context = self.patient_context_tool.format_context_for_ai(
                type('obj', (object,), patient_context)
            )
            evidence_parts.append(f"Patient Context:\n{formatted_context}")
        
        state.aggregated_evidence = "\n\n".join(evidence_parts)
        state.current_step = "evidence_aggregated"
        
        return state
    
    def _synthesize_response(self, state: OrchestratorState) -> OrchestratorState:
        """
        Synthesize response using Bedrock.
        
        Args:
            state: Current orchestrator state
            
        Returns:
            Updated state with final response
        """
        if not self.bedrock_service.is_available():
            # Fallback to simple response if Bedrock not available
            state.final_response = self._generate_fallback_response(state)
            state.current_step = "response_synthesized"
            return state
        
        from app.schemas.ai import BedrockRequest
        
        # Generate system prompt
        system_prompt = self.bedrock_service.generate_system_prompt(state.context)
        
        # Format prompt with context
        patient_context = None
        if 'patient_context' in state.tool_results:
            patient_context = self.patient_context_tool.format_context_for_ai(
                type('obj', (object,), state.tool_results['patient_context'])
            )
        
        prompt = self.bedrock_service.format_prompt_with_context(
            state.user_query,
            state.tool_results,
            patient_context
        )
        
        # Invoke Bedrock
        bedrock_request = BedrockRequest(
            prompt=prompt,
            model_id=self.bedrock_service.model_id,
            max_tokens=1000,
            temperature=0.7,
            system_prompt=system_prompt
        )
        
        # Check if guardrails configuration is available
        guardrails_config = self.guardrails_service.get_default_config()
        if guardrails_config.guardrail_id and guardrails_config.guardrail_version:
            # Use Bedrock Guardrails for actual AWS guardrail enforcement
            bedrock_response = self.bedrock_service.invoke_with_guardrails(
                bedrock_request,
                guardrails_config
            )
        else:
            # Fall back to regular invocation without guardrails
            bedrock_response = self.bedrock_service.invoke_model(bedrock_request)
        
        state.final_response = bedrock_response.text
        state.current_step = "response_synthesized"
        
        return state
    
    def _generate_fallback_response(self, state: OrchestratorState) -> str:
        """Generate a fallback response when Bedrock is not available."""
        response_parts = [f"Based on the available data, here's what I found:\n\n"]
        
        if 'sql' in state.tool_results:
            response_parts.append(f"Database Query Results:\n{state.tool_results['sql']}\n")
        
        if 'rag' in state.tool_results:
            response_parts.append(f"Document Search Results:\n{state.tool_results['rag']}\n")
        
        if 'analytics' in state.tool_results:
            response_parts.append(f"Analytics:\n{state.tool_results['analytics']}\n")
        
        if 'patient_context' in state.tool_results:
            response_parts.append(f"Patient Information:\n{state.tool_results['patient_context']}\n")
        
        response_parts.append(
            "\nNote: Full AI synthesis requires Bedrock configuration. "
            "This is a summary of the raw tool results."
        )
        
        return "".join(response_parts)
    
    def _apply_guardrails(self, state: OrchestratorState) -> OrchestratorState:
        """
        Apply guardrails to ensure safe output.
        
        Args:
            state: Current orchestrator state
            
        Returns:
            Updated state with guarded response
        """
        guardrails_config = self.guardrails_service.get_default_config()
        
        # Validate output
        is_valid, blocked_reasons, filtered_text = self.guardrails_service.validate_output(
            state.final_response,
            guardrails_config
        )
        
        # Apply system prompt constraints
        state.final_response = self.guardrails_service.apply_system_prompt_constraints(
            filtered_text
        )
        
        state.current_step = "guardrails_applied"
        
        return state
    
    def _extract_sources(self, state: OrchestratorState) -> List[Dict[str, Any]]:
        """Extract source references from tool results."""
        sources = []
        
        if 'rag' in state.tool_results:
            for chunk in state.tool_results['rag'].get('chunks', []):
                sources.append({
                    "type": "document",
                    "source": chunk.get('source_filename', ''),
                    "document_type": chunk.get('document_type', ''),
                    "similarity": chunk.get('similarity', 0.0)
                })
        
        if 'sql' in state.tool_results:
            sources.append({
                "type": "database",
                "query_type": state.tool_results['sql'].get('query_type', ''),
                "row_count": state.tool_results['sql'].get('row_count', 0)
            })
        
        return sources
    
    def _calculate_confidence(self, state: OrchestratorState) -> Optional[float]:
        """Calculate confidence score based on tool execution success."""
        if not state.execution_history:
            return None
        
        successful_tools = sum(1 for t in state.execution_history if t.success)
        total_tools = len(state.execution_history)
        
        if total_tools == 0:
            return None
        
        return successful_tools / total_tools
    
    def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Handle a chat request from the frontend.
        
        Args:
            request: ChatRequest with message and context
            
        Returns:
            ChatResponse with AI response
        """
        # Convert to orchestration request
        orchestration_request = OrchestrationRequest(
            query=request.message,
            patient_id=request.patient_id,
            consultation_id=request.consultation_id,
            context=request.context
        )
        
        # Orchestrate
        orchestration_response = self.orchestrate(orchestration_request)
        
        # Convert to chat response
        return ChatResponse(
            response=orchestration_response.final_response,
            sources=orchestration_response.sources,
            tool_executions=orchestration_response.tool_executions,
            confidence=orchestration_response.confidence,
            requires_clarification=False,
            suggested_questions=[]
        )
