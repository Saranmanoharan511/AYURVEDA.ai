"""
AI Assistant API Endpoints

FastAPI endpoints for the AI assistant chat interface.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.rbac import require_doctor
from app.schemas.ai import ChatRequest, ChatResponse
from app.services.ai_orchestrator import AIOrchestrator

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_doctor)
):
    """
    AI Chat endpoint for doctors.

    This endpoint receives a doctor's question, orchestrates the AI tools,
    and returns a grounded response with source references.

    Args:
        request: ChatRequest with message and context
        db: Database session
        current_user: Authenticated doctor user

    Returns:
        ChatResponse with AI response and metadata
    """
    logger.info(f"[AI API] === CHAT REQUEST START ===")
    logger.info(f"[AI API] User Query: {request.message}")
    logger.info(f"[AI API] Patient ID: {request.patient_id}")
    logger.info(f"[AI API] Consultation ID: {request.consultation_id}")
    logger.info(f"[AI API] Context: {request.context}")
    logger.info(f"[AI API] Current User ID: {current_user.id}")

    try:
        # Initialize AI Orchestrator
        orchestrator = AIOrchestrator(db)

        # Add doctor_id to context
        context = request.context.copy()
        context['doctor_id'] = str(current_user.id)

        # Create updated request
        updated_request = ChatRequest(
            message=request.message,
            patient_id=request.patient_id,
            consultation_id=request.consultation_id,
            context=context
        )

        # Execute orchestration
        response = orchestrator.chat(updated_request)

        logger.info(f"[AI API] AI Response: {response.response}")
        logger.info(f"[AI API] === CHAT REQUEST COMPLETE ===")

        return response

    except Exception as e:
        logger.error(f"[AI API] CHAT REQUEST FAILED: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI chat failed: {str(e)}"
        )


@router.get("/health")
async def health():
    """
    Health check endpoint for AI service.
    
    Returns:
        Status of AI service components
    """
    from app.services.bedrock_service import BedrockService
    from app.services.guardrails_service import GuardrailsService
    
    bedrock_service = BedrockService()
    guardrails_service = GuardrailsService()
    
    return {
        "status": "healthy",
        "bedrock_available": bedrock_service.is_available(),
        "guardrails_available": guardrails_service.is_available()
    }
