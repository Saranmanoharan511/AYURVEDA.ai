from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Ayurveda AI Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Database - Neon PostgreSQL
    DATABASE_URL: str
    
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    
    # S3 Configuration
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    
    # SQS Configuration
    SQS_DOCUMENT_QUEUE_URL: str = os.getenv("SQS_DOCUMENT_QUEUE_URL", "")
    SQS_EMAIL_QUEUE_URL: str = os.getenv("SQS_EMAIL_QUEUE_URL", "")
    
    # DLQ Configuration
    DLQ_DOCUMENT_QUEUE_URL: str = os.getenv("DLQ_DOCUMENT_QUEUE_URL", "")
    DLQ_EMAIL_QUEUE_URL: str = os.getenv("DLQ_EMAIL_QUEUE_URL", "")
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY_SECONDS: int = int(os.getenv("RETRY_DELAY_SECONDS", "60"))
    
    # Cognito Configuration
    COGNITO_USER_POOL_ID: str = os.getenv("COGNITO_USER_POOL_ID", "")
    COGNITO_CLIENT_ID: str = os.getenv("COGNITO_CLIENT_ID", "")
    COGNITO_REGION: str = os.getenv("COGNITO_REGION", "us-east-1")
    
    # Bedrock Configuration
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-micro-v1:0")
    BEDROCK_GUARDRAIL_ID: str = os.getenv("BEDROCK_GUARDRAIL_ID", "")
    BEDROCK_GUARDRAIL_VERSION: str = os.getenv("BEDROCK_GUARDRAIL_VERSION", "DRAFT")
    
    # SES Configuration
    SES_FROM_EMAIL: str = os.getenv("SES_FROM_EMAIL", "")
    SES_REGION: str = os.getenv("SES_REGION", "us-east-1")
    
    # Embedding Configuration (Sprint 5)
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "bedrock")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # CloudWatch Configuration
    CLOUDWATCH_LOG_GROUP: str = os.getenv("CLOUDWATCH_LOG_GROUP", "/ayurveda-ai/backend")
    
    # Security
    SECRET_KEY: str
    
    # Rate Limiting Configuration
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
    REDIS_URL: str = os.getenv("REDIS_URL", "memory://")
    
    # CloudWatch Alarms
    CLOUDWATCH_ERROR_THRESHOLD: int = int(os.getenv("CLOUDWATCH_ERROR_THRESHOLD", "5"))
    CLOUDWATCH_LATENCY_THRESHOLD_P95: int = int(os.getenv("CLOUDWATCH_LATENCY_THRESHOLD_P95", "2000"))
    CLOUDWATCH_LATENCY_THRESHOLD_P99: int = int(os.getenv("CLOUDWATCH_LATENCY_THRESHOLD_P99", "5000"))
    
    # Admin Configuration
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    DEFAULT_DOCTOR_STATUS: str = os.getenv("DEFAULT_DOCTOR_STATUS", "active")
    DEFAULT_PATIENT_STATUS: str = os.getenv("DEFAULT_PATIENT_STATUS", "active")
    
    # System Configuration
    ENABLE_AUDIT_LOGGING: bool = os.getenv("ENABLE_AUDIT_LOGGING", "True").lower() == "true"
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "True").lower() == "true"
    SYSTEM_TIMEZONE: str = os.getenv("SYSTEM_TIMEZONE", "Asia/Kolkata")
    
    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
        case_sensitive = True


settings = Settings()
