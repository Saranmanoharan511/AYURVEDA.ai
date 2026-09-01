# Ayurveda AI — Claude Code Project Instructions

> **This file defines how Claude Code must work on this project.**
>
> The project requirements and implementation roadmap are defined in:
>
> - `Projectplan_Neon.md`
> - `Sprintplan_Neon.md`
>
> These documents define **what to build**.
>
> This file defines **how Claude Code should build it**.

---

# 1. Project Overview

This repository contains the **Ayurveda AI Platform**, an AI-powered web application for an Ayurveda doctor.

The platform combines three major systems:

1. **Clinical / Business System**
2. **Document Intelligence System**
3. **AI Assistant System**

The platform is designed as a production-oriented modular application with asynchronous background processing and managed cloud services.

The complete project architecture, requirements, workflows, technology decisions, database design, API design, AI architecture, security model, deployment model, testing strategy, and sprint roadmap are defined in:

```text
Projectplan_Neon.md
Sprintplan_Neon.md
```

These files are the primary source of truth for implementation.

---

# 2. Source-of-Truth Hierarchy

When implementing anything in this project, follow this hierarchy:

```text
Projectplan_Neon.md
        ↓
Architecture / Requirements
        ↓
Sprintplan_Neon.md
        ↓
Current Sprint Tasks
        ↓
Existing Repository Implementation
        ↓
Implementation
        ↓
Testing
        ↓
Verification
```

Before implementing a feature:

1. Read the relevant section of `Projectplan_Neon.md`.
2. Read the corresponding section of `Sprintplan_Neon.md`.
3. Inspect the existing repository.
4. Understand existing implementation before changing it.
5. Follow the approved architecture.
6. Implement incrementally.
7. Test the implementation.
8. Verify against the sprint requirements.

Do not silently replace requirements with personal assumptions.

If the project documents do not define an important architectural decision, explain the ambiguity before making a major decision.

---

# 3. Core Architecture

The project consists of three logical systems.

```text
┌─────────────────────────────────────────────────────────────┐
│                    AYURVEDA AI PLATFORM                     │
│                                                             │
│  ┌────────────────────────┐                                 │
│  │ 1. CLINICAL /          │                                 │
│  │    BUSINESS SYSTEM     │                                 │
│  │                        │                                 │
│  │ Patients               │                                 │
│  │ Consultations          │                                 │
│  │ Appointments           │                                 │
│  │ Reports               │                                 │
│  │ Doctor Notes           │                                 │
│  │ Admin                  │                                 │
│  └────────────┬───────────┘                                 │
│               │                                             │
│               ▼                                             │
│        Neon PostgreSQL                                      │
│                                                             │
│  ┌────────────────────────┐                                 │
│  │ 2. DOCUMENT            │                                 │
│  │    INTELLIGENCE        │                                 │
│  │                        │                                 │
│  │ S3                     │                                 │
│  │  ↓                     │                                 │
│  │ SQS                    │                                 │
│  │  ↓                     │                                 │
│  │ Worker                 │                                 │
│  │  ↓                     │                                 │
│  │ Textract               │                                 │
│  │  ↓                     │                                 │
│  │ Chunking               │                                 │
│  │  ↓                     │                                 │
│  │ Embeddings             │                                 │
│  │  ↓                     │                                 │
│  │ Neon PostgreSQL        │                                 │
│  │ + pgvector             │                                 │
│  └────────────────────────┘                                 │
│                                                             │
│  ┌────────────────────────┐                                 │
│  │ 3. AI ASSISTANT        │                                 │
│  │                        │                                 │
│  │ Intent Router          │                                 │
│  │ SQL Tool               │                                 │
│  │ RAG Tool               │                                 │
│  │ Analytics Tool         │                                 │
│  │ Patient Context Tool   │                                 │
│  │          ↓             │                                 │
│  │ Amazon Bedrock         │                                 │
│  │          ↓             │                                 │
│  │ Bedrock Guardrails     │                                 │
│  └────────────────────────┘                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

These are **logical boundaries**, not separate microservices.

Do not turn every system or domain into a separate microservice unless the project plan explicitly requires it.

The initial implementation should remain a **modular application**.

---

# 4. Approved Technology Stack

The approved technology stack is:

## Frontend

```text
React
Vite
Tailwind CSS
```

Do not replace React with Next.js.

---

## Backend

```text
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
```

---

## Database

```text
Neon PostgreSQL
pgvector
```

Neon PostgreSQL is the managed PostgreSQL platform for this project.

PostgreSQL is the source of truth for structured application data.

pgvector is used for vector search and RAG.

---

## Object Storage

```text
Amazon S3
```

S3 stores original uploaded documents.

Examples include:

```text
Medical reports
Prescriptions
Uploaded PDFs
Images
Other patient documents
```

Do not store original large documents directly in PostgreSQL unless explicitly required by the project plan.

---

## Authentication

```text
Amazon Cognito
```

Authentication and identity management use Cognito.

---

## Messaging

```text
Amazon SQS
```

SQS is used for asynchronous workloads.

Examples:

```text
Document processing
Email processing
Background jobs
```

---

## OCR / Document Extraction

```text
Amazon Textract
```

---

## AI

```text
Amazon Bedrock
Amazon Bedrock Guardrails
```

Bedrock is the production AI runtime.

---

## Email

```text
Amazon SES
```

---

## Monitoring

```text
Amazon CloudWatch
```

---

## Deployment

Initial deployment:

```text
AWS Amplify
+
AWS Lightsail
```

Future scaling path:

```text
AWS ECS / Fargate
```

Do not introduce ECS/Fargate prematurely.

---

## Containerization

```text
Docker
```

---

# 5. Neon PostgreSQL Rules

Neon PostgreSQL is the approved managed PostgreSQL platform.

The application architecture is:

```text
React
  ↓
FastAPI
  ↓
Neon PostgreSQL
```

The frontend must **never connect directly to Neon PostgreSQL**.

Incorrect:

```text
React
  ↓
Neon PostgreSQL
```

Correct:

```text
React
  ↓
FastAPI
  ↓
Neon PostgreSQL
```

PostgreSQL remains the source of truth for structured data.

---

# 6. pgvector Rules

pgvector is part of the Neon PostgreSQL architecture.

Use pgvector for:

- Document embeddings
- Semantic search
- RAG retrieval

Do not introduce a separate vector database unless explicitly approved.

Expected document intelligence flow:

```text
Document
   ↓
Amazon S3
   ↓
Amazon SQS
   ↓
Worker
   ↓
Amazon Textract / extraction
   ↓
Chunking
   ↓
Embeddings
   ↓
Neon PostgreSQL + pgvector
```

---

# 7. Document Storage Rules

Original documents belong in Amazon S3.

Neon PostgreSQL stores:

```text
Document metadata
Patient relationship
Consultation relationship
Processing status
Extracted metadata
Vector representation
```

Conceptually:

```text
S3
 └── Original Document

Neon PostgreSQL
 ├── Document metadata
 ├── Patient relationship
 ├── Consultation relationship
 ├── Processing status
 ├── Extracted metadata
 └── Vector representation
```

Medical documents must remain private.

Do not create public S3 buckets for patient documents.

---

# 8. AI Architecture

The AI assistant must not have unrestricted direct access to the entire database.

Expected architecture:

```text
Doctor
   ↓
AI Chat
   ↓
Intent Router
   ↓
Tool Selection
   ├── SQL Tool
   ├── RAG Tool
   ├── Analytics Tool
   └── Patient Context Tool
   ↓
Amazon Bedrock
   ↓
Bedrock Guardrails
   ↓
Doctor Assistant Response
```

---

# 9. SQL Tool Rules

The SQL Tool is responsible for structured data access.

Examples:

```text
Patient information
Consultation history
Appointment information
Structured clinical information
Business information
Analytics queries
```

The AI SQL path must be controlled and primarily read-only.

Never provide unrestricted database access to the LLM.

The AI must not execute destructive operations such as:

```sql
DROP
DELETE
TRUNCATE
ALTER
UPDATE
INSERT
```

through the AI query path unless explicitly designed as a controlled application operation outside the normal AI SQL tool.

---

# 10. RAG Tool Rules

RAG retrieval must respect patient authorization.

Expected flow:

```text
Doctor Question
      ↓
RAG Tool
      ↓
Query Embedding
      ↓
Neon pgvector
      ↓
Authorization / Patient Filtering
      ↓
Relevant Chunks
      ↓
AI Context
```

Never retrieve documents from another patient simply because they are semantically similar.

Patient filtering and authorization must occur on the backend.

---

# 11. Patient Data Isolation

Patient data isolation is a critical security requirement.

The system must enforce:

```text
Patient
    ↓
Own records only

Doctor
    ↓
Authorized patient records only

Admin
    ↓
Administrative permissions
```

Authorization must be enforced by the backend.

Frontend checks alone are never sufficient.

Do not rely on:

```text
React route protection
```

as the only authorization mechanism.

FastAPI must verify authorization for protected resources.

---

# 12. API Architecture

APIs should use:

```text
/api/v1/
```

Expected domains include:

```text
/api/v1/auth
/api/v1/patients
/api/v1/consultations
/api/v1/appointments
/api/v1/documents
/api/v1/reports
/api/v1/doctor
/api/v1/admin
/api/v1/analytics
/api/v1/ai
```

Follow consistent:

- HTTP methods
- Status codes
- Request schemas
- Response schemas
- Validation
- Error responses

Do not randomly create APIs outside the established structure.

---

# 13. Backend Architecture

Prefer a modular FastAPI architecture.

Conceptually:

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── v1/
│   │
│   ├── core/
│   │
│   ├── models/
│   │
│   ├── schemas/
│   │
│   ├── services/
│   │
│   ├── repositories/
│   │
│   ├── ai/
│   │
│   ├── documents/
│   │
│   └── workers/
│
├── migrations/
├── tests/
├── Dockerfile
└── requirements.txt
```

This is a conceptual structure.

Before creating directories, inspect the existing repository and follow existing patterns.

Do not reorganize the entire project unnecessarily.

---

# 14. Frontend Architecture

Use:

```text
React
+
Vite
+
Tailwind CSS
```

The frontend communicates with FastAPI.

Frontend responsibilities include:

```text
Authentication UI
Patient dashboard
Doctor dashboard
Consultation UI
Appointment UI
Document UI
AI chat UI
Analytics UI
Admin UI
Responsive layouts
```

Business authorization must not exist exclusively in the frontend.

---

# 15. Background Processing

Long-running operations should not block normal API requests.

Use:

```text
FastAPI
   ↓
Amazon SQS
   ↓
Worker
```

Examples:

```text
Document processing
OCR processing
Embedding generation
Email processing
Background jobs
```

Where required:

- Implement retries.
- Handle failed messages.
- Use dead-letter queues.
- Make background operations observable.

---

# 16. Secrets Management

Never hardcode secrets.

Never commit:

```text
.env
credentials
AWS access keys
AWS secret keys
API keys
database passwords
JWT secrets
Cognito secrets
third-party credentials
```

Use environment variables and appropriate deployment secret mechanisms.

---

# 17. Environment Strategy

Maintain separate environments:

```text
development
staging
production
```

Never accidentally connect local development to production.

Database connection configuration must be environment-specific.

AWS configuration must also be environment-specific.

---

# 18. Database Migration Rules

Use Alembic or the migration mechanism defined in the project plan.

Every schema change should include:

```text
Migration
+
Application model update
+
Tests
+
Verification
```

Never manually modify production schema without a migration.

Do not delete or rewrite existing migrations unnecessarily.

---

# 19. Coding Standards

Write production-quality code.

Prefer:

- Clear names
- Small functions
- Single responsibility
- Type hints
- Pydantic validation
- Explicit error handling
- Reusable services
- Testable components
- Dependency injection where appropriate

Avoid:

- Giant functions
- Duplicate logic
- Hardcoded secrets
- Magic values
- Unnecessary abstractions
- Premature microservices
- Unnecessary dependencies

Before adding a dependency, check whether the existing stack already provides the required functionality.

---

# 20. Error Handling

Do not silently swallow errors.

Avoid:

```python
try:
    ...
except:
    pass
```

Use explicit exception handling.

API errors should return appropriate HTTP status codes and structured responses.

Never expose:

- Stack traces
- Secrets
- Internal credentials
- Sensitive implementation details

to end users.

---

# 21. Logging

Logs should help diagnose:

```text
API failures
Authentication failures
Document processing failures
SQS failures
AI invocation failures
Database failures
External service failures
```

Never log:

```text
Passwords
Tokens
API keys
Database credentials
Sensitive medical content unnecessarily
```

---

# 22. Testing Rules

Every meaningful feature must have appropriate tests.

Testing should include:

## Unit Tests

Test:

- Services
- Utilities
- Validation
- Business rules
- AI tools where practical

## Integration Tests

Test important interactions such as:

```text
FastAPI
   ↓
Neon PostgreSQL
```

and relevant AWS integration boundaries.

## API Tests

Test:

- Authentication
- Authorization
- Validation
- Success cases
- Failure cases
- Edge cases

## Security Tests

Test:

- Patient isolation
- Unauthorized access
- Role boundaries
- Document access
- AI tool authorization
- Prompt injection defenses

## RAG Tests

Test:

- Retrieval quality
- Patient filtering
- Metadata filtering
- Missing evidence
- Cross-patient leakage

## AI Tests

Test:

- Tool selection
- SQL safety
- RAG behavior
- Guardrails
- Hallucination behavior
- Missing evidence handling

---

# 23. Definition of Done

A feature is not complete merely because the code exists.

A feature is complete when:

```text
Requirements implemented
        +
Correct architecture followed
        +
Validation implemented
        +
Authorization verified
        +
Tests written
        +
Tests passing
        +
Errors handled
        +
Logging appropriate
        +
Documentation updated
        +
No secrets committed
```

For infrastructure-related code:

```text
Integration code implemented
        +
Configuration placeholders created
        +
Tests/mocks created
        +
Required AWS resources documented
        +
Security requirements documented
        +
Manual AWS setup instructions documented
```

Claude Code does not need to create the actual AWS resources.

---

# 24. Sprint Discipline

The project contains eight sprints.

Follow them sequentially unless explicitly instructed otherwise.

The intended progression is:

```text
Sprint 1
Foundation and Cloud Setup
        ↓
Sprint 2
Authentication and Roles
        ↓
Sprint 3
Clinical / Business System
        ↓
Sprint 4
Documents and Notifications
        ↓
Sprint 5
Document Intelligence and RAG
        ↓
Sprint 6
AI Assistant and Tool Orchestration
        ↓
Sprint 7
Admin, Analytics, Reliability and Security
        ↓
Sprint 8
Testing, Deployment and Production Hardening
```

Do not automatically begin the next sprint.

---

# 25. Sprint Workflow

For every sprint:

## Step 1 — Read

Read the relevant sprint from:

```text
Sprintplan_Neon.md
```

Read the relevant architecture sections from:

```text
Projectplan_Neon.md
```

## Step 2 — Inspect

Before modifying code:

- Inspect repository structure.
- Inspect existing implementation.
- Inspect configuration.
- Inspect tests.
- Identify existing patterns.
- Identify dependencies.

Do not assume the repository is empty.

## Step 3 — Plan

Explain:

```text
What will change
Files to create
Files to modify
Database changes
Dependencies
Tests required
Potential risks
```

## Step 4 — Implement

Implement incrementally.

Do not generate hundreds of unrelated files at once.

## Step 5 — Test

Run relevant tests after meaningful changes.

## Step 6 — Fix

Fix failures before continuing.

Do not ignore failing tests.

## Step 7 — Verify

Compare implementation against the sprint requirements.

## Step 8 — Report

Provide:

```text
Completed
Partially completed
Not completed
Tests executed
Test results
Known issues
Next recommended step
```

Do not automatically move to the next sprint.

---

# 26. Do Not Guess Major Requirements

For minor implementation details, use reasonable engineering judgment.

For major decisions involving:

```text
Database architecture
Authentication
Authorization
Cloud infrastructure
AI architecture
Security
Data model
Deployment
New external services
```

do not silently invent a solution.

Explain the issue and ask for direction when necessary.

---

# 27. Do Not Replace Approved Technologies

Do not replace approved technologies without explicit approval.

Do not change:

```text
React
FastAPI
Neon PostgreSQL
pgvector
Amazon S3
Amazon SQS
Amazon Textract
Amazon Bedrock
Amazon Cognito
Amazon SES
Amazon CloudWatch
AWS Amplify
AWS Lightsail
Docker
```

with alternatives such as:

```text
Next.js
Django
RDS
DynamoDB
Pinecone
MongoDB
Kafka
OpenAI
Kubernetes
```

unless explicitly instructed.

---

# 28. Cost-Conscious Architecture

The initial system should remain cost-conscious.

Do not introduce expensive infrastructure without justification.

Avoid prematurely introducing:

```text
Kubernetes
ECS/Fargate
Aurora
Dedicated vector databases
Kafka
Multiple production AI providers
Microservices for every domain
```

Initial architecture should remain:

```text
React/Vite
    ↓
AWS Amplify

FastAPI
    ↓
AWS Lightsail

Neon PostgreSQL
    +
pgvector

S3
SQS
Textract
Bedrock
Cognito
SES
CloudWatch
```

Scale only when justified by requirements or actual workload.

---

# 29. Security Is a First-Class Requirement

This application handles sensitive clinical information.

Always prioritize:

```text
Authentication
Authorization
Patient isolation
Document privacy
Least privilege
Secure secrets
Auditability
Input validation
AI safety
```

Never weaken security merely to make implementation easier.

Never implement:

```text
Public medical documents
Hardcoded credentials
Unrestricted SQL
Cross-patient retrieval
Disabled authorization
```

for production-oriented code.

---

# 30. AI Safety Rules

The AI assistant is an assistant, not an unrestricted autonomous database administrator.

AI must not:

- Bypass authorization.
- Retrieve unauthorized patient data.
- Execute destructive SQL.
- Invent patient information.
- Present unsupported information as verified fact.
- Ignore missing evidence.
- Circumvent application security.

When evidence is unavailable, the AI should clearly indicate that sufficient evidence is unavailable.

---

# 31. Git Rules

Use Git throughout development.

Create focused commits.

Examples:

```text
feat: initialize backend foundation
feat: add neon database configuration
feat: add patient management
feat: add document upload workflow
feat: add rag retrieval
feat: add ai orchestration
test: add authorization coverage
fix: enforce patient document isolation
```

Avoid meaningless commit messages such as:

```text
changes
update
stuff
final
final-final
```

Never commit:

```text
.env
credentials
API keys
database passwords
private certificates
large generated files
```

---

# 32. Existing Code Must Be Respected

Before modifying an existing file:

1. Read it.
2. Understand its purpose.
3. Follow existing patterns.
4. Make the smallest clean change necessary.

Do not rewrite working modules unnecessarily.

Do not replace the architecture simply because another implementation appears easier.

---

# 33. Dependency Management

Before adding a dependency:

1. Check whether an existing dependency already solves the problem.
2. Check compatibility.
3. Consider maintenance.
4. Consider security.
5. Add it only if justified.

Record new dependencies correctly.

---

# 34. AWS DEVELOPMENT AND INFRASTRUCTURE SAFETY

## Critical Rule

The developer is new to AWS.

**Claude Code must operate in AWS CODE-ONLY MODE by default.**

The default behavior is:

> **Write AWS integration code, configuration templates, tests, and documentation — but do not create, modify, delete, deploy, or manage AWS resources.**

Claude Code is a software development agent in this project, **not an autonomous AWS administrator**.

---

# 35. AWS Code-Only Responsibilities

Claude Code MAY:

```text
Write AWS SDK integration code
Write boto3 integrations
Write S3 integration
Write SQS integration
Write Cognito integration
Write Bedrock integration
Write SES integration
Write CloudWatch integration
Write AWS configuration classes
Write environment variable handling
Write .env.example
Write tests and mocks
Write Docker configuration
Write deployment configuration
Write infrastructure-as-code files
Document AWS setup requirements
Explain required AWS resources
Explain required IAM permissions
```

Claude Code MUST NOT automatically:

```text
Create AWS resources
Modify AWS resources
Delete AWS resources
Deploy to AWS
Upload production files
Configure production AWS
Modify IAM
Create credentials
Modify security groups
Modify networking
Create S3 buckets
Create SQS queues
Create Cognito resources
Create Lightsail resources
Create Amplify resources
Configure CloudWatch resources
Configure production Bedrock resources
Configure SES production resources
```

---

# 36. AWS CLI Rules

AWS CLI commands that modify infrastructure must never be executed automatically.

Examples of prohibited automatic commands include:

```text
aws cloudformation deploy
aws cloudformation create-stack
aws cloudformation update-stack

aws s3 mb
aws s3api create-bucket

aws sqs create-queue
aws sqs delete-queue

aws iam create-user
aws iam create-role
aws iam attach-role-policy
aws iam put-role-policy

aws cognito-idp create-user-pool

aws lightsail create-container-service

aws amplify create-app
aws amplify start-job
```

Do not execute Terraform, CloudFormation, CDK, Pulumi, or similar infrastructure provisioning commands against the AWS account unless explicitly authorized.

---

# 37. AWS Read-Only Inspection

AWS CLI inspection may be used only when genuinely necessary.

Examples include:

```text
aws sts get-caller-identity
aws s3 ls
aws sqs list-queues
aws cognito-idp list-user-pools
aws lightsail get-container-services
aws logs describe-log-groups
```

Even read-only commands should not be executed unnecessarily.

Never assume AWS access is required just because the application uses AWS.

---

# 38. AWS Deployment Is Manual

Claude Code must never automatically:

```text
Deploy application
Push Docker images to AWS
Upload production files to S3
Create database resources
Create queues
Configure Cognito
Configure IAM
Configure CloudWatch
Configure Amplify
Configure Lightsail
Modify networking
Modify security groups
Modify production configuration
```

Deployment remains developer-controlled.

---

# 39. AWS Integration Code Is Allowed

Claude Code should write the application code necessary to communicate with AWS.

Example:

```python
import os
import boto3

s3_client = boto3.client(
    "s3",
    region_name=os.getenv("AWS_REGION")
)

bucket_name = os.getenv("S3_BUCKET_NAME")
```

This is allowed.

However, Claude Code must not create the bucket.

The code should assume that the AWS resource will be configured separately.

---

# 40. Never Hardcode AWS Credentials

Never write:

```python
boto3.client(
    "s3",
    aws_access_key_id="...",
    aws_secret_access_key="..."
)
```

Never hardcode:

```text
AWS access keys
AWS secret keys
Session tokens
IAM credentials
Cognito secrets
Bedrock credentials
SES credentials
Database passwords
API keys
```

---

# 41. AWS Environment Variables

AWS integration must use environment variables.

Create a safe `.env.example` such as:

```env
AWS_REGION=

S3_BUCKET_NAME=

SQS_DOCUMENT_QUEUE_URL=
SQS_EMAIL_QUEUE_URL=

COGNITO_USER_POOL_ID=
COGNITO_CLIENT_ID=

BEDROCK_MODEL_ID=

SES_FROM_EMAIL=
```

The values remain empty placeholders.

The developer will fill the actual values manually after inspecting and configuring AWS.

---

# 42. .env Rules

Claude Code MAY create:

```text
.env.example
```

Claude Code MUST NOT populate:

```text
.env
```

with real AWS credentials.

If `.env` already exists:

- Do not expose its contents.
- Do not print secrets.
- Do not modify credentials without explicit instruction.
- Do not commit it.

Ensure `.env` is included in `.gitignore`.

---

# 43. Never Invent AWS Resource Values

Do not invent real environment-specific values.

Incorrect:

```python
S3_BUCKET_NAME = "ayurveda-ai-production-bucket"
```

unless the developer explicitly provides that value.

Correct:

```python
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
```

and:

```env
S3_BUCKET_NAME=
```

Use placeholders such as:

```text
<your-s3-bucket-name>
<your-document-queue-url>
<your-user-pool-id>
```

in documentation when necessary.

---

# 44. Separate AWS Application Code From AWS Infrastructure

Application integration:

```text
FastAPI
   │
   ├── S3 client
   ├── SQS client
   ├── Cognito integration
   ├── Bedrock integration
   └── SES integration
```

Infrastructure:

```text
AWS Console / Infrastructure-as-Code
        │
        ├── S3
        ├── SQS
        ├── Cognito
        ├── IAM
        ├── CloudWatch
        ├── Lightsail
        └── Amplify
```

Claude Code should implement the application integration.

The developer controls the infrastructure.

---

# 45. Infrastructure-as-Code

Claude Code MAY write infrastructure-as-code files if required.

Examples:

```text
Terraform
CloudFormation
AWS CDK
Pulumi
```

However, Claude Code MUST NOT automatically execute:

```text
terraform apply
terraform destroy
```

or equivalent deployment commands.

Claude Code may write:

```text
infrastructure/
├── main.tf
├── variables.tf
└── outputs.tf
```

The developer must inspect the infrastructure definitions before applying them.

---

# 46. AWS Modification Requires Explicit Approval

If an AWS operation would modify infrastructure, Claude Code must stop and ask for explicit permission.

Example:

> This operation will create an S3 bucket. Do you want me to execute it?

Do not execute until the developer explicitly approves the specific operation.

---

# 47. Production AWS Environment Is Protected

Never automatically modify production.

Never:

```text
Delete production resources
Modify production IAM
Modify production databases
Modify production S3
Modify production SQS
Modify production networking
Deploy production containers
Change production configuration
```

without explicit developer approval.

---

# 48. AWS Credentials Are Developer-Owned

Claude Code must not request AWS credentials simply to write integration code.

The developer will configure AWS credentials independently when required.

If credentials are required for a future operation, explain:

```text
What credential is required
Why it is required
Where it should be configured
What permissions it should have
```

Never request the secret value itself through the chat.

---

# 49. Least-Privilege IAM

When documenting AWS permissions, use least privilege.

Do not recommend:

```text
AdministratorAccess
```

for the application simply because it is convenient.

Instead identify the minimum permissions required.

For example:

```text
S3:
    s3:GetObject
    s3:PutObject

SQS:
    sqs:SendMessage
    sqs:ReceiveMessage
    sqs:DeleteMessage
```

The final IAM policy must be inspected by the developer before deployment.

---

# 50. AWS Integration Development Workflow

For every AWS integration:

```text
Requirement
    ↓
Implement application code
    ↓
Create configuration interface
    ↓
Create .env.example placeholders
    ↓
Write tests / mocks
    ↓
Document required AWS resource
    ↓
Document required IAM permissions
    ↓
STOP
    ↓
Developer manually configures AWS
    ↓
Developer provides configuration
    ↓
Developer manually tests
    ↓
Developer manually deploys
```

Do not skip the manual inspection step.

---

# 51. Local Development and AWS

Where practical, local development should not require immediate access to production AWS resources.

Use appropriate:

```text
Mocks
Test doubles
Fixtures
Dependency injection
Test environments
```

Example:

```text
LOCAL

FastAPI
   │
   ├── Mock S3
   ├── Mock SQS
   ├── Mock Cognito
   └── Controlled AI integration


PRODUCTION

FastAPI
   │
   ├── Amazon S3
   ├── Amazon SQS
   ├── Amazon Cognito
   └── Amazon Bedrock
```

Do not introduce unnecessary local infrastructure solely to imitate AWS.

---

# 52. AWS Documentation Requirements

Whenever Claude Code implements an AWS integration, document:

1. AWS service required.
2. Why it is required.
3. Required environment variables.
4. Required IAM permissions.
5. Expected resource configuration.
6. Whether local development requires it.
7. Whether production requires it.
8. Whether the resource must be created manually.

Example:

```text
AWS S3

Purpose:
Store uploaded medical documents.

Environment variables:
S3_BUCKET_NAME
AWS_REGION

Required permissions:
s3:GetObject
s3:PutObject

Resource creation:
Manual — developer controlled.

Application integration:
Implemented by Claude Code.
```

---

# 53. AWS Safety Summary

The default behavior is:

```text
┌────────────────────────────────────────────────────┐
│                 CLAUDE CODE                        │
│                                                    │
│ Write AWS integration code              ✅         │
│ Write configuration                     ✅         │
│ Write .env.example                      ✅         │
│ Write tests / mocks                     ✅         │
│ Write documentation                     ✅         │
│ Explain AWS resources                   ✅         │
│ Explain IAM requirements                ✅         │
│                                                    │
│ Create AWS resources                    ❌         │
│ Modify AWS resources                    ❌         │
│ Delete AWS resources                    ❌         │
│ Deploy to AWS                           ❌         │
│ Execute Terraform apply                 ❌         │
│ Execute CloudFormation deploy           ❌         │
│ Modify IAM                              ❌         │
│ Create AWS credentials                  ❌         │
│ Upload production S3 files              ❌         │
│ Modify production infrastructure       ❌         │
└────────────────────────────────────────────────────┘
```

**Only perform an AWS infrastructure operation when the developer explicitly authorizes that specific operation.**

---

# 54. Infrastructure Changes

Infrastructure-related application code may be implemented normally.

However, actual infrastructure creation and modification remains developer-controlled.

When infrastructure is required:

1. Explain the resource.
2. Explain why it is required.
3. Explain the expected configuration.
4. Explain cost implications where known.
5. Explain security implications.
6. Create the required code/configuration.
7. Create `.env.example` placeholders.
8. Stop before modifying AWS.

---

# 55. Database Safety

Never perform destructive database operations against production without explicit confirmation.

Be especially careful with:

```text
DROP DATABASE
DROP TABLE
TRUNCATE
DELETE
ALTER TABLE
```

When testing migrations:

Prefer development or staging environments.

Never assume a database is disposable.

---

# 56. Backup and Recovery

The system must have recovery strategies for:

```text
Neon PostgreSQL
S3
Application code
Configuration
```

The project should be designed so that:

```text
Application can be recreated
        +
Database can be recovered
        +
Documents can be recovered
        +
Patient relationships remain intact
```

Backup and recovery configuration must be documented and validated.

Do not claim recovery works merely because a configuration exists.

Where possible, recovery procedures should be tested in a non-production environment.

---

# 57. Observability

CloudWatch should be used for application and infrastructure observability according to the project plan.

Monitor important failures such as:

```text
API errors
Worker failures
SQS dead-letter messages
Document processing failures
Bedrock invocation errors
SES failures
Database connectivity issues
High resource usage
```

Logs must not expose sensitive patient information unnecessarily.

---

# 58. Documentation Rules

When architecture or implementation changes, update relevant documentation.

Documentation must remain consistent with the actual implementation.

For example, if the project uses:

```text
Neon PostgreSQL
```

do not introduce documentation referring to another PostgreSQL hosting platform.

Do not document functionality that does not exist.

---

# 59. Working With Project Plans

When asked to implement a sprint:

Use:

```text
Projectplan_Neon.md
        ↓
Architecture / Requirements
        ↓
Sprintplan_Neon.md
        ↓
Current Sprint
        ↓
Existing Repository
        ↓
Implementation
        ↓
Tests
        ↓
Verification
```

If there is an apparent conflict:

1. Identify it.
2. Explain it.
3. Do not silently choose a new architecture.
4. Ask for direction when the conflict materially affects the system.

---

# 60. When Claude Code Should Ask

Ask before making a major decision when:

- Requirements conflict.
- A new external service is required.
- A major architecture change is proposed.
- A security boundary must be weakened.
- A destructive database operation is required.
- Production infrastructure may be affected.
- A significant technology replacement is needed.
- An AWS resource would be created, modified, or deleted.
- A requirement is genuinely ambiguous and cannot safely be resolved.

Do not ask unnecessary questions for routine implementation details.

---

# 61. When Claude Code Should NOT Ask

Do not interrupt for trivial decisions such as:

- Variable names
- Function names
- Minor file organization
- Standard error handling
- Normal test structure
- Formatting
- Standard FastAPI patterns
- Standard React patterns
- Routine migration naming

Use reasonable engineering judgment for small decisions.

---

# 62. Before Finishing Any Task

Before saying a task is complete, verify:

```text
[ ] Requirement implemented
[ ] Existing code inspected
[ ] Correct architecture followed
[ ] Security considered
[ ] Authorization considered
[ ] Database changes migrated
[ ] Tests added
[ ] Tests passing
[ ] Errors handled
[ ] Logging appropriate
[ ] No secrets committed
[ ] Documentation updated if necessary
[ ] No unrelated files changed
[ ] AWS infrastructure was NOT modified automatically
```

---

# 63. Final Development Philosophy

Do not optimize for generating the largest amount of code.

Optimize for:

```text
Correctness
    +
Security
    +
Maintainability
    +
Testability
    +
Architecture consistency
    +
Incremental progress
    +
Developer control
```

The project documents define **what to build**.

This file defines **how Claude Code should build it**.

Build the system **sprint by sprint**.

Do not skip ahead.

Do not silently change architectural decisions.

Do not claim a feature is complete without verification.

**Claude Code writes the software.**

**The developer remains in control of AWS infrastructure, credentials, deployment, and production changes.**