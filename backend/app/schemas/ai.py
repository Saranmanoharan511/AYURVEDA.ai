"""
AI Assistant Schemas

Pydantic schemas for AI chat, tools, and orchestration.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# Chat Schemas
# ============================================================================

class ChatRequest(BaseModel):
    """Request schema for AI chat endpoint."""
    
    message: str = Field(..., description="Doctor's question or request")
    patient_id: Optional[str] = Field(None, description="Patient ID for patient-specific queries")
    consultation_id: Optional[str] = Field(None, description="Consultation ID for consultation-specific queries")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class ChatMessage(BaseModel):
    """Single message in chat history."""
    
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")


class ToolExecution(BaseModel):
    """Record of a tool execution."""
    
    tool_name: str = Field(..., description="Name of the tool executed")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for the tool")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Output data from the tool")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    success: bool = Field(..., description="Whether the tool execution succeeded")
    error_message: Optional[str] = Field(None, description="Error message if execution failed")


class ChatResponse(BaseModel):
    """Response schema for AI chat endpoint."""
    
    response: str = Field(..., description="AI assistant's response")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source references for RAG")
    tool_executions: List[ToolExecution] = Field(default_factory=list, description="Tools executed")
    confidence: Optional[float] = Field(None, description="Confidence score of the response")
    requires_clarification: bool = Field(False, description="Whether the AI needs clarification")
    suggested_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")


# ============================================================================
# Tool Schemas
# ============================================================================

class SQLToolRequest(BaseModel):
    """Request schema for SQL Tool."""
    
    query_type: Literal["patient_count", "consultation_status", "appointment_status", 
                        "today_consultations", "monthly_stats", "patient_search"] = Field(
        ..., description="Type of SQL query to execute")
    patient_id: Optional[str] = Field(None, description="Patient ID for patient-specific queries")
    doctor_id: Optional[str] = Field(None, description="Doctor ID for doctor-specific queries")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range for queries (start_date, end_date)")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional filters")


class SQLToolResponse(BaseModel):
    """Response schema for SQL Tool."""
    
    query_type: str = Field(..., description="Type of query executed")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Query results")
    row_count: int = Field(..., description="Number of rows returned")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")


class PatientContextRequest(BaseModel):
    """Request schema for Patient Context Tool."""
    
    patient_id: str = Field(..., description="Patient ID")
    include_consultations: bool = Field(True, description="Include consultation history")
    include_documents: bool = Field(True, description="Include document information")
    include_appointments: bool = Field(True, description="Include appointment information")


class PatientContextResponse(BaseModel):
    """Response schema for Patient Context Tool."""
    
    patient_id: str = Field(..., description="Patient ID")
    client_id: str = Field(..., description="Public client ID")
    profile: Dict[str, Any] = Field(default_factory=dict, description="Patient profile information")
    consultations: List[Dict[str, Any]] = Field(default_factory=list, description="Consultation history")
    documents: List[Dict[str, Any]] = Field(default_factory=list, description="Document information")
    appointments: List[Dict[str, Any]] = Field(default_factory=list, description="Appointment information")
    total_consultations: int = Field(0, description="Total number of consultations")
    total_documents: int = Field(0, description="Total number of documents")


class RAGToolRequest(BaseModel):
    """Request schema for RAG Tool."""
    
    query: str = Field(..., description="Query for semantic search")
    patient_id: str = Field(..., description="Patient ID for authorization")
    consultation_id: Optional[str] = Field(None, description="Consultation ID for filtering")
    document_type: Optional[str] = Field(None, description="Document type for filtering")
    top_k: int = Field(5, description="Number of top results to retrieve")
    min_similarity: float = Field(0.7, description="Minimum similarity threshold")


class RAGToolResponse(BaseModel):
    """Response schema for RAG Tool."""
    
    query: str = Field(..., description="Original query")
    chunks: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved chunks")
    chunk_count: int = Field(..., description="Number of chunks retrieved")
    retrieval_time_ms: float = Field(..., description="Retrieval time in milliseconds")


class AnalyticsToolRequest(BaseModel):
    """Request schema for Analytics Tool."""
    
    metric_type: Literal["monthly_consultations", "common_conditions", "treatment_trends",
                          "returning_patients", "city_distribution", "follow_up_counts"] = Field(
        ..., description="Type of analytics metric")
    doctor_id: Optional[str] = Field(None, description="Doctor ID for doctor-specific analytics")
    date_range: Optional[Dict[str, str]] = Field(None, description="Date range for analytics")
    limit: int = Field(10, description="Maximum number of results")


class AnalyticsToolResponse(BaseModel):
    """Response schema for Analytics Tool."""
    
    metric_type: str = Field(..., description="Type of metric calculated")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Analytics results")
    summary: Optional[Dict[str, Any]] = Field(None, description="Summary statistics")
    calculation_time_ms: float = Field(..., description="Calculation time in milliseconds")


# ============================================================================
# Intent Router Schemas
# ============================================================================

class IntentClassification(BaseModel):
    """Intent classification result."""
    
    primary_intent: Literal["sql_query", "rag_search", "analytics", "patient_context", 
                            "general_question", "multi_tool"] = Field(
        ..., description="Primary intent of the user query")
    confidence: float = Field(..., description="Confidence score for the classification")
    secondary_intents: List[str] = Field(default_factory=list, description="Secondary intents")
    suggested_tools: List[Dict[str, Any]] = Field(default_factory=list, description="Suggested tools to use (execution plan)")


class IntentRouterRequest(BaseModel):
    """Request schema for Intent Router."""
    
    query: str = Field(..., description="User's query")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class IntentRouterResponse(BaseModel):
    """Response schema for Intent Router."""
    
    classification: IntentClassification = Field(..., description="Intent classification")
    execution_plan: List[Dict[str, Any]] = Field(default_factory=list, description="Planned tool executions")
    requires_patient_context: bool = Field(False, description="Whether patient context is needed")


# ============================================================================
# Bedrock Schemas
# ============================================================================

class BedrockRequest(BaseModel):
    """Request schema for Bedrock LLM."""
    
    prompt: str = Field(..., description="Prompt for the LLM")
    model_id: str = Field(..., description="Bedrock model ID")
    max_tokens: int = Field(1000, description="Maximum tokens to generate")
    temperature: float = Field(0.7, description="Temperature for generation")
    system_prompt: Optional[str] = Field(None, description="System prompt for the LLM")


class BedrockResponse(BaseModel):
    """Response schema for Bedrock LLM."""
    
    text: str = Field(..., description="Generated text")
    model_id: str = Field(..., description="Model ID used")
    tokens_used: int = Field(..., description="Number of tokens used")
    finish_reason: Optional[str] = Field(None, description="Reason for completion")
    guardrails_applied: bool = Field(False, description="Whether guardrails were applied")


class GuardrailsConfig(BaseModel):
    """Configuration for Bedrock Guardrails."""
    
    guardrail_id: Optional[str] = Field(None, description="Guardrail ID")
    guardrail_version: Optional[str] = Field(None, description="Guardrail version")
    content_filters: List[str] = Field(default_factory=list, description="Content filters to apply")
    blocked_categories: List[str] = Field(default_factory=list, description="Categories to block")
    medical_diagnosis_blocked: bool = Field(True, description="Block medical diagnosis attempts")


# ============================================================================
# Orchestrator Schemas
# ============================================================================

class OrchestratorState(BaseModel):
    """State for AI Orchestrator graph."""
    
    user_query: str = Field(..., description="Original user query")
    patient_id: Optional[str] = Field(None, description="Patient ID from context")
    consultation_id: Optional[str] = Field(None, description="Consultation ID from context")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    intent_classification: Optional[IntentClassification] = Field(None, description="Intent classification")
    tool_results: Dict[str, Any] = Field(default_factory=dict, description="Results from tool executions")
    aggregated_evidence: str = Field("", description="Aggregated evidence from tools")
    final_response: str = Field("", description="Final response to user")
    execution_history: List[ToolExecution] = Field(default_factory=list, description="Execution history")
    current_step: str = Field("start", description="Current step in orchestration")


class OrchestrationRequest(BaseModel):
    """Request schema for AI Orchestrator."""
    
    query: str = Field(..., description="User's query")
    patient_id: Optional[str] = Field(None, description="Patient ID for context")
    consultation_id: Optional[str] = Field(None, description="Consultation ID for context")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class OrchestrationResponse(BaseModel):
    """Response schema for AI Orchestrator."""
    
    final_response: str = Field(..., description="Final response to user")
    tool_executions: List[ToolExecution] = Field(default_factory=list, description="Tool execution history")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source references")
    confidence: Optional[float] = Field(None, description="Confidence score")
    orchestration_time_ms: float = Field(..., description="Total orchestration time")
