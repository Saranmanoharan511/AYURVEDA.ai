# **Ayurveda AI Platform — Final Production Architecture & Project Blueprint** 

## **1. Project Vision** 

Build a production-ready, AI-assisted Ayurveda consultation platform for an Ayurveda doctor and her patients. 

The platform combines three intentionally separated systems: 

1. **Clinical / Business System** — manages people, authentication, patients, consultations, appointments, reports, administration, notifications, and analytics data. 

2. **Document Intelligence System** — securely stores, extracts, processes, embeds, indexes, and retrieves patient documents for doctor-facing RAG workflows. 

3. **AI Assistant System** — provides a controlled, tool-driven assistant that can query business data, retrieve patient-specific documents, generate analytics, summarize records, and assist the doctor without bypassing authorization boundaries. 

The architecture is designed for: 

- Mobile and desktop browser access. 

- A single-doctor or small-clinic initial deployment. 

- Strong separation of application data and medical documents. 

- 

- AWS + Neon production infrastructure. 

- 

- Cost-conscious initial deployment. 

- 

- Clear migration path from Lightsail to ECS/Fargate when scale requires it. 

- AI assistance that supports the doctor rather than acting as an autonomous medical diagnostician. 

# **2. Final Technology Stack** 

|Layer|Final Decision|Purpose|
|---|---|---|
|Frontend|React + Vite|Patient, Doctor, Admin interfaces|
|Frontend Hosting|AWS Amplify Hosting|Git-based deployment and web hosting|
|Backend|FastAPI|REST API and business logic|
|Backend Packaging|Docker|Reproducible deployment|
|Initial Backend<br>Hosting|AWS Lightsail|Simple, cost-conscious production<br>compute|



1 

|Layer|Final Decision|Purpose|
|---|---|---|
|Future Backend<br>Hosting|ECS + Fargate|Scalable managed container<br>deployment|
|Authentication|Amazon Cognito|User authentication and identity|
|Authorization|Application RBAC + resource-level<br>authorization|Patient / Doctor / Admin permissions|
|Primary Database|PostgreSQL|Transactional business data|
|Production DB<br>Hosting|Neon PostgreSQL|Managed database, backups, recovery|
|Vector Search|pgvector|Embeddings and semantic retrieval|
|Object Storage|Amazon S3|Medical documents, reports,<br>prescriptions, images|
|Upload Pattern|S3 pre-signed URLs|Secure direct browser-to-S3 uploads/<br>downloads|
|Async Messaging|Amazon SQS|Decouple long-running/background<br>workfows|
|OCR / Document<br>Extraction|Amazon Textract|Extract text and structured data from<br>supported documents|
|Embeddings|Confgurable embedding provider|Convert document chunks into vectors|
|LLM|Amazon Bedrock|Production foundation model access|
|AI Safety|Amazon Bedrock Guardrails|AI input/output safety controls|
|AI Orchestration|FastAPI service + LangGraph-style<br>graph orchestration|Route requests through controlled<br>tools and workfows|
|Email|Amazon SES|Transactional notifcations|
|Monitoring|Amazon CloudWatch|Logs, metrics, alarms, operational<br>visibility|
|Local AI<br>Development|LM Studio|Cost-free local model development and<br>testing|
|Video Consultation|Zoom|Doctor-patient online consultation|
|CI/CD|GitHub + Amplify + Docker<br>deployment workfow|Source control and automated delivery|



2 

## **2A. Database Hosting Decision — Neon PostgreSQL**

The project uses **Neon PostgreSQL** as the managed PostgreSQL platform.

The database responsibility remains unchanged:

- PostgreSQL remains the source of truth for structured clinical and business data.
- pgvector remains in PostgreSQL for document embeddings and semantic retrieval.
- FastAPI remains the application layer responsible for database access.
- Amazon S3 remains the source of the actual medical document files.
- The AI layer continues to access structured and vector data only through controlled, authorization-aware tools.
- Development, staging, and production database connection settings remain environment-specific.

This is a database-hosting change, not a change to the three-system logical architecture.

# **3. Final Architecture at a Glance** 

|<br> <br> <br>|`INTERNET`<br>`|`<br>`v`<br>`+---------------------------+`|
|---|---|
||`|     AWS Amplify Hosting    |`|
|<br> <br> <br> <br> <br> <br>|`|       React + Vite         |`<br>`+-------------+-------------+`<br>`|`<br>`HTTPS API Requests`<br>`|`<br>`v`<br>`+---------------------------+`|
||`|       FastAPI Backend      |`|
||`|       Docker Container     |`|
||`|     AWS Lightsail (v1)     |`|
|<br> <br> <br> <br>|<br>`+-------------+-------------+`<br>`|`<br>`+--------------------------+--------------------------+`<br>|
||`|                          |                          |`|
||`v                          v                          v`|
||`+------------------+       +------------------+`|
|`+-----`|`-------------+`|
||`| Amazon Cognito   |       | Neon PostgreSQL       |       | Amazon S3`|
|`|`||
||`| Authentication   |       | PostgreSQL       |       | Secure Documents`|
|`|`||
||`| Patient/Doctor/  |       | + pgvector       |       | Reports/Images`|
|`|`||
||`| Admin identities |       | Business Data   |       | Prescriptions`|
|`|`||
||`+------------------+       +------------------+       +--------`|
|`+-----`|`----+`|
||`|`|
||`|`|
|`Object`<br>|`Events`<br>`v`|
|`+-----`|`----------+`|
||`| Amazon`|
|<br>`SQS`|<br>`|`|
||`| Async`|
|`Queue`|`|`|
|<br>`+-----`|`+-------`<br>`--+`|



3 

```
                                                                          |
                                                                          v
+---------------+
                                                                  | Worker
Layer   |
                                                                  | Document
Jobs  |
                                                                  | Email
Jobs     |
                                                                  | AI
Jobs        |
                                                                  +-------
+-------+
                                                                          |
                                           +------------------------------
+------------------+
```

```
|                                                 |
v                                                 v
                                   +---------------
+                                 +---------------+
                                   | Amazon
|                                 | Embedding      |
                                   | Textract
|                                 | Service       |
                                   | OCR/Extract
|                                 |               |
                                   +-------+-------
+                                 +-------+-------+
|                                                 |
                                           +-------------------
+-----------------------------+
                                                               |
                                                               v
                                                        +--------------+
                                                        | pgvector      |
                                                        | Chunk Vectors |
                                                        | Metadata      |
                                                        +------+-------+
                                                               |
                                                               v
                                                      +------------------+
                                                      | AI Orchestrator  |
                                                      | Intent Router    |
                                                      | Tool Router      |
```

4 



<!-- Start of picture text -->
                                                      +---+---+---+---+<br>                                                          |   |   |<br>                                      +-------------------+   |<br>+-------------------+<br>                                      |<br>|                       |<br>                                      v<br>v                       v<br>                               +-------------+        +-------------+<br>+-------------+<br>                               | SQL Tool    |        | RAG Tool    |        |<br>Analytics   |<br>                               | PostgreSQL  |        | pgvector +  |        |<br>Tool        |<br>                               | Read/Query  |        | S3 Metadata |        |<br>PostgreSQL  |<br>                               +------+------+        +------+------+<br>+------+------+<br>                                      |<br>|                      |<br>                                      +----------------------<br>+----------------------+<br>                                                             |<br>                                                             v<br>                                                     +---------------+<br>                                                     | Bedrock       |<br>                                                     | LLM           |<br>                                                     | Guardrails    |<br>                                                     +-------+-------+<br>                                                             |<br>                                                             v<br>                                                     Doctor AI Answer<br>+-------------------------------------------------------+<br>                          |                  Amazon<br>SES                             |<br>                          | Booking | Meeting | Report | Notification<br>Emails       |<br>                          +-----------------------<br>^-------------------------------+<br>                                                  |<br>                                                  |<br>                                           SQS Email Jobs<br>+-------------------------------------------------------+<br>                          |                Amazon<br><!-- End of picture text -->

5 

```
CloudWatch                       |
                          | Logs | Metrics | Alarms | Errors | Service
Monitoring  |
+-------------------------------------------------------+
```

# **4. Three-System Architecture Model** 

## **System 1 — Clinical / Business System** 

### **Responsibility** 

This system is the source of truth for all operational and transactional data. 

It answers questions such as: 

- Who is the patient? 

- Who is the doctor? 

- Which consultation belongs to which patient? 

- What is the current appointment status? 

- Has a meeting been scheduled? 

- Has the doctor uploaded a report? 

- Which users can access which records? 

- What analytics can be computed from structured data? 

### **Core Components** 

```
React Frontend
      |
      v
FastAPI API
      |
```

```
      +--> Cognito Authentication
      |
      +--> RBAC / Authorization
      |
      +--> PostgreSQL
      |
      +--> S3 File Metadata
      |
      +--> SQS Background Jobs
      |
```

- `+--> SES Notifications` 

6 

```
      |
```

```
      +--> Zoom Meeting Metadata
```

### **Main Modules** 

#### **Patient Module** 

- Registration and login. 

- Stable Client ID. 

- Profile management. 

- Personal details. 

- Contact details. 

- Consultation history. 

- Appointment status. 

- Report access. 

- Document access. 

#### **Doctor Module** 

- Doctor authentication. 

- Dashboard. 

- Waiting for scheduling. 

- Meeting scheduled. 

- Completed consultation / report pending. 

- Completed consultation / report sent. 

- All clients. 

- Client search. 

- Patient detail page. 

- Doctor notes. 

- Report creation. 

- AI assistant. 

- Analytics. 

#### **Admin Module** 

- Admin authentication. 

- User management. 

- Doctor management. 

- Blocking / unblocking users. 

- Booking ON/OFF. 

- Holiday configuration. 

- Email templates. • AI configuration. 

- Storage administration. 

- Backup visibility. 

- Permission management. 

- System analytics. 

7 

#### **Appointment Module** 

Recommended state machine: 

```
NO_ACTIVE_CONSULTATION
        |
        v
APPOINTMENT_BOOKED
        |
        v
WAITING_FOR_MEETING_SCHEDULE
        |
        v
MEETING_SCHEDULED
        |
        v
WAITING_FOR_CONSULTATION
        |
        v
CONSULTATION_COMPLETED
        |
        v
WAITING_FOR_DOCTOR_REPORT
        |
        v
REPORT_UPLOADED
        |
        v
REPORT_SENT
        |
        v
CONSULTATION_CLOSED
```

The state transition should happen through explicit backend actions rather than arbitrary frontend status updates. 

Example: 

```
Doctor clicks "Send Meeting Details"
        |
        v
Validate meeting date/time/link
        |
        v
Save appointment details
```

8 

```
        |
        v
Change status -> MEETING_SCHEDULED
        |
        v
Create email job in SQS
        |
        v
Email worker sends SES email
```

#### **Client ID Design** 

Use two identifiers: 

```
Internal ID
UUID
Private database identity
Public Client ID
AYU-000001
Permanent human-readable identity
```

Do not use the public Client ID as the only database primary key. 

All relevant records should reference the stable internal patient UUID while exposing the Client ID to authorized users. 

# **5. Clinical / Business Data Model** 

Recommended core tables: 

- `users - id - cognito_sub - role - status - created_at - updated_at` 

```
patients
- id (UUID)
```

- `client_id (unique)` 

- `cognito_sub` 

9 

```
- full_name
- date_of_birth / age policy
- gender
- phone
- email
- city
- state
- created_at
- updated_at
```

```
doctors
```

```
- id
```

```
- cognito_sub
- name
- qualifications
- specialization
- status
```

```
consultations
```

```
- id
- patient_id
- doctor_id
- reason
- description
- consultation_status
- started_at
- completed_at
- created_at
```

```
appointments
- id
- consultation_id
- scheduled_date
- scheduled_time
- timezone
- zoom_meeting_url
- status
```

```
consultation_notes
- id
- consultation_id
- doctor_id
- diagnosis
- ayurvedic_assessment
- medicines
- lifestyle_advice
- diet_plan
- follow_up_instructions
```

10 

```
- created_at
```

```
reports
```

- `id` 

- `consultation_id` 

- `patient_id` 

- `report_type` 

- `s3_object_key` 

- `uploaded_by - uploaded_at` 

```
patient_documents
```

- `id` 

- `patient_id` 

- `consultation_id` 

- `s3_object_key` 

- `document_type` 

- `original_filename` 

- `content_type` 

- `upload_status` 

- `processing_status` 

- `created_at` 

```
notifications
```

- `id` 

- `user_id` 

- `event_type` 

- `channel` 

- `delivery_status` 

- `provider_message_id` 

- `created_at` 

```
system_settings
```

- `id` 

- `key` 

- `value` 

- `updated_by` 

- `updated_at` 

```
audit_logs
```

- `id` 

- `actor_user_id` 

- `action` 

- `resource_type - resource_id` 

- `metadata` 

- `timestamp` 

11 

The exact schema can evolve, but the architectural rule is: 

PostgreSQL owns structured clinical/business truth. S3 owns files. pgvector owns searchable document representations. No single storage layer should be treated as the source of truth for everything. 

# **6. System 2 — Document Intelligence System** 

## **Responsibility** 

This system manages all patient-related documents that require secure storage, extraction, indexing, semantic search, and AI retrieval. 

It handles: 

- Previous medical reports. 

- Blood test reports. 

- Scan reports. 

- Prescription images. 

- Prescription PDFs. 

- Condition-related photographs. 

- Doctor-generated reports. 

- Supporting documents. 

The system is asynchronous by design. 

# **7. Document Upload Architecture** 

Recommended flow: 

```
Patient / Doctor Browser
        |
        | 1. Request upload permission
        v
FastAPI
        |
        | 2. Authorize user + patient/consultation ownership
        v
Generate pre-signed S3 upload URL
        |
        v
Browser uploads directly to S3
```

12 

```
        |
        v
S3 stores private object
        |
        v
Create document metadata in PostgreSQL
        |
        v
Create processing job
        |
        v
SQS
        |
        v
Document Worker
```

This avoids sending large files through FastAPI unnecessarily. 

# **8. Document Intelligence Processing Pipeline** 

```
                S3 Upload
                    |
                    v
             Document Metadata
              PostgreSQL Record
                    |
                    v
                  SQS
                    |
                    v
            Document Processing Worker
                    |
        +-----------+-----------+
        |                       |
        v                       v
 Text-based PDF             Scanned Document
        |                       |
        |                       v
        |                  Amazon Textract
        |                       |
        +-----------+-----------+
                    |
                    v
             Extracted Text
```

13 

```
                    |
                    v
          Document Normalization
                    |
                    v
              Chunking
                    |
                    v
       Attach Security Metadata
                    |
                    v
        Embedding Generation
                    |
                    v
       PostgreSQL + pgvector
                    |
                    v
          Document Ready for RAG
```

# **9. Document Metadata Strategy** 

Every indexed chunk should carry enough metadata to enforce patient and consultation boundaries. 

Example metadata: 

```
chunk_id
patient_id
client_id
consultation_id
document_id
document_type
source_filename
uploaded_by
created_at
content_hash
```

Retrieval should conceptually enforce: 

```
WHERE patient_id = authorized_patient_id
```

or for doctor-wide access: 

14 

```
WHERE doctor_id = authorized_doctor_id
```

The AI should never perform unrestricted vector retrieval across all patients. 

# **10. RAG Architecture** 

The RAG system should be patient-aware and permission-aware. 

```
Doctor Question
      |
      v
Identify Patient Context
      |
      v
Validate Doctor Authorization
      |
      v
Create Retrieval Filter
      |
      +--> patient_id
      +--> consultation_id (optional)
      +--> document_type (optional)
      +--> date range (optional)
      |
      v
Vector Search in pgvector
      |
      v
Retrieve Top-K Chunks
      |
      v
Optional Reranking / Relevance Filtering
      |
      v
Build Grounded Context
      |
      v
Bedrock + Guardrails
      |
      v
AI Answer with Source References
```

Example: 

15 

```
Question:
"What was Client AYU-000001's previous diagnosis?"
Retrieval context:
patient_id = internal UUID for AYU-000001
Retrieve:
- Previous consultation notes
- Relevant reports
- Relevant prescriptions
Do NOT retrieve:
- AYU-000002 documents
- Unrelated clinic documents
```

# **11. Document Lifecycle** 

```
UPLOADED
   |
   v
STORED_IN_S3
   |
   v
PROCESSING_QUEUED
   |
   v
EXTRACTING
   |
   v
CHUNKING
   |
   v
EMBEDDING
   |
   v
INDEXED
   |
   v
AVAILABLE_FOR_RAG
```

Failure path: 

16 

```
PROCESSING_FAILED
       |
       +--> error log
       +--> retry count
       +--> dead-letter queue after repeated failure
       +--> admin visibility
```

The system should never mark a document as RAG-ready before its processing pipeline is successfully completed. 

# **12. System 3 — AI Assistant System** 

## **Responsibility** 

The AI Assistant is a controlled intelligence layer over the clinical/business system and document intelligence system. 

It should not directly access the entire database without controls. 

Instead, it uses explicit tools. 

```
Doctor
   |
   v
AI Chat Interface
   |
   v
FastAPI AI Endpoint
   |
   v
AI Orchestrator
   |
   v
Intent Router
   |
   +------ SQL Tool
   |
   +------ RAG Tool
   |
   +------ Analytics Tool
   |
   +------ Patient Context Tool
   |
```

17 

```
   +------ Appointment Tool
   |
   +------ Optional Web Tool
   |
   v
Bedrock
   |
   v
Guardrails
   |
   v
Final Response
```

# **13. AI Orchestration Design** 

The AI layer should work as an orchestration graph rather than one large prompt. 

Conceptual flow: 

```
START
  |
  v
Authenticate User
  |
  v
Load Role + Permissions
  |
  v
Determine Context
  |
  v
Intent Router
  |
  +---------------------------+
  |                           |
  v                           v
Structured Data           Document Question
  |                           |
  v                           v
SQL / Analytics            RAG Retrieval
  |                           |
  +-------------+-------------+
                |
                v
```

18 

```
         Combine Evidence
                |
                v
          Bedrock LLM
                |
                v
        Guardrails Check
                |
                v
     Response Validation
                |
                v
              END
```

The graph should support multi-step execution. 

Example: 

```
Question:
"Summarize today's skin allergy patients and mention any previous treatment
patterns."
Router
  |
  +--> SQL Tool: find today's skin allergy consultations
  |
  +--> For each relevant patient, create authorized retrieval scope
  |
  +--> RAG Tool: retrieve previous diagnoses/treatments
  |
  +--> Analytics Tool: identify repeated patterns
  |
  +--> Bedrock: synthesize grounded summary
  |
  +--> Guardrails: validate final response
  |
  v
Doctor Summary
```

This is significantly stronger than a single LLM prompt with unrestricted database access. 

19 

# **14. AI Tool Definitions** 

## **SQL Tool** 

Purpose: 

- Query structured business data. 

- Appointment status. 

- Patient counts. 

- Pending reports. 

- Today's consultations. 

- Monthly consultation statistics. 

- Patient search. 

Examples: 

```
Show patients waiting for meeting scheduling.
Show today's consultations.
How many consultations happened this month?
Which city has the highest number of patients?
```

The SQL tool should: 

- Use a restricted database user. 

- Prefer allow-listed query patterns or validated SQL generation. 

- Never allow destructive SQL. 

- Never return unauthorized patient records. 

- Apply doctor/admin authorization before execution. 

## **RAG Tool** 

Purpose: 

- Search patient-specific documents. 

- Search consultation history. 

- Search prescriptions. 

- Search reports. 

- Summarize medical documents. 

Examples: 

20 

```
What was the previous diagnosis for Client AYU-000001?
What medicines were prescribed in the last consultation?
What was the patient's previous blood sugar value?
```

The RAG tool must enforce: 

```
User authorization
        +
Patient scope
        +
Consultation scope
        +
Document scope
```

before retrieval. 

## **Analytics Tool** 

Purpose: 

- Monthly consultation metrics. 

- Most common conditions. 

- Treatment trends. 

- Returning patient rate. 

- City distribution. 

- Follow-up counts. 

The Analytics Tool should primarily calculate from structured PostgreSQL data rather than asking an LLM to estimate statistics. 

```
PostgreSQL
    |
    v
SQL / Aggregation
    |
    v
Exact Metrics
    |
    v
Bedrock
    |
```

21 

```
    v
Human-friendly explanation
```

## **Patient Context Tool** 

Purpose: 

Build the canonical context for a particular Client ID. 

Example: 

```
Client AYU-000001
        |
        +--> Patient profile
        +--> Active consultation
        +--> Previous consultations
        +--> Appointments
        +--> Reports
        +--> Documents
        +--> Relevant RAG chunks
```

This tool should be used when the AI needs a holistic patient view. 

# **15. AI Guardrails and Safety Model** 

The system is designed as a doctor-assistance platform, not an autonomous medical diagnosis engine. 

The AI should: 

- Summarize available information. 

- Retrieve documented history. 

- Surface patterns in existing data. 

- Help the doctor prepare for consultations. 

- Draft non-final summaries. 

- Organize information. 

The AI should not: 

- Present itself as a doctor. 

- Independently diagnose patients. 

- Override the doctor's judgment. 

- Invent missing medical history. 

22 

- Generate unsupported claims from incomplete documents. 

- Expose another patient's information. 

Guardrails should cover: 

```
Prompt Safety
Content Safety
Sensitive Information Handling
Medical Advice Boundaries
Prompt Injection Resistance
Document Instruction Isolation
Output Validation
```

A retrieved document is treated as data, not as an instruction source. 

For example, text inside a patient-uploaded document saying "ignore previous instructions" must never override system or developer policies. 

# **16. Authentication and Authorization Architecture** 

Use Amazon Cognito for identity, with application-level role and resource authorization. 

```
Cognito User Pool
       |
       +--> Patient
       |
       +--> Doctor
       |
       +--> Admin
```

The frontend may expose separate routes: 

```
/patient/login
/doctor/login
/admin/login
```

But the backend should validate the authenticated identity and role on every protected request. 

Authorization levels: 

23 

### **Patient** 

Can access: 

- Own profile. 

- Own Client ID. 

- Own consultations. 

- Own appointments. 

- Own reports. 

- Own documents. 

### **Doctor** 

Can access: 

- Authorized clinic patients. 

- Consultations. 

- Reports. 

- Appointments. 

- AI tools for permitted clinical records. 

- Analytics within the doctor's scope. 

### **Admin** 

Can access: 

- Operational administration. 

- User management. 

- System configuration. 

- Permission management. 

- System-wide analytics. 

The backend, not the React frontend, is the final authority for authorization. 

# **17. Secure Document Access** 

S3 bucket should be private. 

Recommended pattern: 

```
User requests document
        |
        v
FastAPI authenticates user
        |
```

24 

```
        v
Authorization check
        |
        v
Verify patient/doctor/admin scope
        |
        v
Generate short-lived access URL
        |
        v
User downloads from S3
```

Do not expose permanent public URLs for patient documents. 

# **18. Notification Architecture** 

Notifications should be asynchronous. 

```
Business Event
      |
      v
FastAPI
      |
      v
Create SQS Message
      |
      v
Email Worker
      |
      v
Amazon SES
      |
      v
Delivery Result
      |
      v
Notification Record
      |
      v
CloudWatch Logs / Metrics
```

Events: 

25 

```
CONSULTATION_BOOKED
MEETING_SCHEDULED
REPORT_UPLOADED
REPORT_SENT
FOLLOW_UP_REMINDER
ADMIN_NOTIFICATION
```

Email content should never be the only place where critical information exists. The application database remains the source of truth. 

# **19. Main End-to-End Workflows** 

## **Workflow A — Patient Books Consultation** 

```
Patient
  |
  v
Login / Register
  |
  v
Cognito authentication
  |
  v
Patient Dashboard
  |
  v
Book Consultation
  |
  +--> Personal details
  +--> Health reason
  +--> Description
  +--> Document uploads
  |
  v
FastAPI
  |
  +--> Validate request
  +--> Create consultation
  +--> Create appointment request
  +--> Create Client/Consultation linkage
  +--> Store document metadata
  +--> Generate S3 upload URLs
  |
```

26 

```
  v
Database Commit
  |
  v
SQS Events
  |
  +--> Email patient
  +--> Email doctor
  +--> Process documents
  |
  v
Patient sees confirmation
```

## **Workflow B — Doctor Schedules Meeting** 

```
Doctor Dashboard
      |
      v
Waiting for Meeting Schedule
      |
      v
Select Patient
      |
      v
Enter Zoom Link + Date + Time
      |
      v
FastAPI Authorization
      |
      v
Save Appointment
      |
      v
Status -> MEETING_SCHEDULED
      |
      v
SQS Email Job
      |
      v
SES
      |
      v
Patient receives meeting details
```

27 

## **Workflow C — Doctor Uploads Consultation Report** 

```
Doctor
   |
   v
Open Patient Detail
   |
   v
Complete Consultation
   |
   v
Enter diagnosis / assessment / medicines / advice
   |
   v
Upload Prescription PDF
   |
   v
S3
   |
   v
Save Report Metadata in PostgreSQL
   |
   v
SQS
   |
   +--> Email patient
   +--> Process document
   +--> Create embedding/index
   |
   v
Status -> REPORT_SENT / CONSULTATION_CLOSED
```

## **Workflow D — Doctor Asks AI About a Patient** 

```
Doctor
  |
  v
AI Chat
  |
  v
"What medicines were prescribed previously for AYU-000001?"
  |
  v
```

28 

```
Authenticate Doctor
  |
  v
Authorization Check
  |
  v
Intent Router
  |
  v
Patient Context Resolver
  |
  v
RAG Tool
  |
  v
Filter by Patient ID
  |
  v
pgvector retrieval
  |
  v
Relevant prescription chunks
  |
  v
Bedrock
  |
  v
Guardrails
  |
  v
Answer with grounded context
```

# **20. AI Query Routing Examples** 

|User Query|Primary Tool|Data Source|
|---|---|---|
|Show patients waiting for scheduling|SQL Tool|PostgreSQL|
|Show today's consultations|SQL Tool|PostgreSQL|
|How many skin allergy patients visited this<br>month?|Analytics Tool|PostgreSQL|
|Tell me about Client AYU-000001|Patient Context + SQL + RAG|PostgreSQL +<br>pgvector|



29 

|User Query|Primary Tool|Data Source|
|---|---|---|
|What was the previous diagnosis?|RAG Tool|pgvector|
|What medicines were prescribed last time?|RAG Tool|pgvector|
|What was the blood sugar value?|RAG Tool|pgvector / extracted<br>data|
|Summarize today's workload|SQL + Analytics + Bedrock|PostgreSQL|
|Summarize this patient's complete history|Patient Context + RAG|PostgreSQL +<br>pgvector|
|Which patients need follow-up?|SQL + Analytics|PostgreSQL|
|What should I prepare before today's<br>consultations?|SQL + Patient Context + RAG +<br>Bedrock|Multiple|



The router should support multi-tool workflows when a question requires both structured and unstructured information. 

# **21. Infrastructure and Deployment Environments** 

Use three environments conceptually: 

```
Development
    |
    +--> Local React
    +--> Local FastAPI
    +--> Local PostgreSQL or development Neon database
    +--> Local S3-compatible test storage or AWS dev S3
    +--> LM Studio
    +--> Local test workers
Staging
    |
    +--> Amplify staging branch
    +--> FastAPI staging container
    +--> Staging Neon PostgreSQL
    +--> Staging S3
    +--> Bedrock
    +--> SES sandbox / controlled sending
Production
    |
    +--> Amplify production
```

30 

```
    +--> Lightsail FastAPI container
    +--> Neon PostgreSQL
    +--> S3 private bucket
    +--> SQS
    +--> Worker process
    +--> Textract
    +--> Bedrock
    +--> Guardrails
    +--> SES
    +--> CloudWatch
```

The initial production deployment can be simpler, but application configuration should always separate environments. 

# **22. Recommended Backend Deployment Evolution** 

## **Phase 1 — Initial Production** 

```
Amplify
   |
Lightsail Docker
   |
FastAPI
   |
Neon PostgreSQL
```

## **Phase 2 — More Background Processing** 

```
Lightsail FastAPI
      |
      v
SQS
      |
      v
Dedicated worker container
```

## **Phase 3 — Growth** 

```
Amplify
   |
Load Balancer / API Layer
```

31 

```
   |
ECS + Fargate
   |
+--> FastAPI Service
+--> Worker Service
+--> Scheduled Jobs
```

The application should be designed from Day 1 so Phase 3 does not require a major rewrite. 

# **23. Recommended FastAPI Service Boundaries** 

Organize the backend by business capability rather than putting everything in one giant file. 

```
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── auth.py
│   │   ├── patients.py
│   │   ├── consultations.py
│   │   ├── appointments.py
│   │   ├── reports.py
│   │   ├── documents.py
│   │   ├── doctor.py
│   │   ├── admin.py
│   │   ├── ai.py
│   │   └── analytics.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── permissions.py
│   │   └── logging.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── patient.py
│   │   ├── consultation.py
│   │   ├── appointment.py
│   │   ├── document.py
│   │   └── report.py
```

32 

```
│   │
```

```
│   ├── services/
```

```
│   │   ├── patient_service.py
```

```
│   │   ├── consultation_service.py
```

```
│   │   ├── appointment_service.py
```

```
│   │   ├── document_service.py
```

```
│   │   ├── report_service.py
```

```
│   │   ├── notification_service.py
```

```
│   │   └── analytics_service.py
```

```
│   │
│   ├── ai/
│   │   ├── orchestrator.py
```

```
│   │   ├── router.py
│   │   ├── tools/
│   │   │   ├── sql_tool.py
│   │   │   ├── rag_tool.py
│   │   │   ├── analytics_tool.py
│   │   │   └── patient_context_tool.py
│   │   ├── retrieval/
│   │   │   ├── retriever.py
│   │   │   ├── filters.py
│   │   │   └── reranker.py
│   │   └── prompts/
│   │       ├── system.py
│   │       ├── sql.py
│   │       └── rag.py
│   │
│   ├── workers/
│   │   ├── document_worker.py
│   │   ├── email_worker.py
│   │   └── ai_worker.py
│   │
│   └── db/
│       ├── session.py
│       ├── migrations/
│       └── repositories/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   ├── ai/
│   └── e2e/
│
├── Dockerfile
├── docker-compose.yml
```

33 

```
├── requirements.txt
└── .env.example
```

# **24. Frontend Structure** 

```
frontend/
│
├── src/
│   ├── app/
│   │   ├── router.tsx
│   │   └── providers/
│   │
│   ├── pages/
│   │   ├── public/
│   │   │   ├── Portfolio.tsx
│   │   │   └── AyurvedaInfo.tsx
│   │   ├── patient/
│   │   │   ├── Dashboard.tsx
```

```
│   │   │   ├── BookConsultation.tsx
│   │   │   ├── History.tsx
│   │   │   └── Reports.tsx
│   │   ├── doctor/
```

```
│   │   │   ├── Dashboard.tsx
```

```
│   │   │   ├── PatientDetail.tsx
```

```
│   │   │   ├── ScheduleMeeting.tsx
│   │   │   ├── Reports.tsx
```

```
│   │   │   ├── AIChat.tsx
```

```
│   │   │   └── Analytics.tsx
```

```
│   │   └── admin/
```

```
│   │       ├── Dashboard.tsx
```

```
│   │       ├── Users.tsx
```

```
│   │       ├── Settings.tsx
│   │       └── Analytics.tsx
```

```
│   │
```

```
│   ├── components/
```

```
│   ├── features/
│   │   ├── auth/
│   │   ├── patients/
│   │   ├── consultations/
│   │   ├── documents/
│   │   ├── reports/
│   │   ├── ai/
```

```
│   │   └── analytics/
```

34 

```
│   │
│   ├── services/
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── uploads.ts
│   │
│   └── types/
│
└── package.json
```

# **25. Security Architecture** 

Security is a cross-cutting layer across all three systems. 

```
                    SECURITY BOUNDARY
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
 Authentication     Authorization       Data Protection
        |                  |                  |
     Cognito          RBAC + ABAC        Encryption
        |                  |                  |
        v                  v                  v
 Identity Tokens    Resource Scoping     S3 Private
                                          Database Security
                           |
                           v
                     Audit Logging
                           |
                           v
                     CloudWatch
```

Minimum controls: 

- Cognito-based authentication. 

- Backend token validation. 

- Role-based access control. 

- 

- Resource-level patient authorization. 

- Private S3 buckets. 

- Short-lived document access URLs. 

- Database encryption. 

35 

- HTTPS everywhere. 

- Secrets outside source code. 

- Separate development/staging/production credentials. 

- Audit logs for sensitive actions. 

- AI retrieval authorization filtering. 

- No unrestricted SQL from the LLM. 

- No unrestricted vector retrieval from the LLM. 

- No public medical files. 

# **26. AI-Specific Security Controls** 

The AI system needs additional controls beyond standard web security. 

### **SQL Safety** 

```
LLM generates intent
      |
      v
Validated SQL plan
      |
      v
Read-only database permissions
      |
      v
Execute
      |
      v
Structured result
```

Never allow the AI to execute arbitrary INSERT, UPDATE, DELETE, DROP, ALTER, or schema-management statements through the normal doctor assistant. 

### **RAG Safety** 

```
User identity
      |
      v
Doctor authorization
      |
      v
Patient scope
      |
      v
```

36 

```
Document scope
      |
      v
Vector search
```

### **Prompt Injection Protection** 

Documents are untrusted content. 

The system must separate: 

```
System Instructions
Developer Instructions
Tool Instructions
User Question
Retrieved Document Content
```

Retrieved content should be treated as evidence, not executable instructions. 

# **27. Observability Architecture** 

CloudWatch should monitor all three systems. 

```
Clinical System
  |
  +--> API latency
  +--> 4xx / 5xx
  +--> Appointment events
  +--> Email failures
```

```
Document System
  |
  +--> Upload failures
  +--> S3 errors
  +--> OCR failures
  +--> Queue depth
  +--> Processing duration
  +--> Embedding errors
```

```
AI System
  |
  +--> AI request count
```

```
  +--> Tool execution failures
```

37 

```
  +--> Retrieval failures
  +--> Bedrock errors
  +--> Guardrail interventions
  +--> Response latency
```

Recommended alarms: 

- FastAPI 5xx rate. 

- High latency. 

- SQS queue depth above threshold. 

- Dead-letter queue messages. 

- Failed document processing. 

- High database CPU. 

- High database connections. 

- S3/SES failures. 

- Bedrock invocation errors. 

# **28. Backup and Recovery** 

Critical recovery layers: 

```
PostgreSQL
  |
  +--> Automated backups
  +--> Snapshots
  +--> Point-in-time recovery strategy
S3
  |
  +--> Versioning
  +--> Lifecycle policies
  +--> Backup/replication strategy as required
Configuration
  |
  +--> Infrastructure as code
  +--> Environment configuration backup
Application
  |
  +--> Git repository
  +--> Tagged releases
```

The disaster-recovery goal is: 

38 

```
Application can be recreated
Data can be restored
Documents can be recovered
Patient relationships remain intact
```

# **29. API Domains** 

Recommended API grouping: 

```
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

Examples: 

```
POST   /api/v1/consultations
GET    /api/v1/patients/{client_id}
POST   /api/v1/appointments/{id}/schedule
POST   /api/v1/documents/upload-url
POST   /api/v1/reports
GET    /api/v1/patients/{client_id}/timeline
POST   /api/v1/ai/chat
GET    /api/v1/analytics/consultations
```

Keep API contracts stable and versioned. 

39 

# **30. Eight-Sprint Production Build Plan** 

## **Sprint 1 — Foundation and Cloud Setup** 

### **Goal** 

Create the project foundation and AWS environment. 

### **Build** 

• React + Vite project. • FastAPI project. • Docker setup. • PostgreSQL schema foundation. • AWS account structure. • Amplify frontend deployment. • Lightsail backend deployment. • Neon PostgreSQL. • S3 private buckets. • Environment configuration. • CloudWatch logging. 

### **Output** 

A deployed empty application with frontend, backend, database, storage, and monitoring connected. 

## **Sprint 2 — Authentication and Roles** 

### **Goal** 

Implement secure identity and access control. 

### **Build** 

- Cognito User Pool. • Patient sign-up/sign-in. • Doctor login. • Admin login. • Role mapping. • Backend JWT validation. • RBAC middleware. 

- Resource-level authorization helpers. • Protected frontend routes. 

40 

### **Output** 

Patients, doctors, and admins can securely access their own application areas. 

## **Sprint 3 — Clinical / Business System** 

### **Goal** 

Build the core consultation platform. 

### **Build** 

- Patient profile. • Permanent Client ID. • Consultation creation. • Appointment records. • Consultation statuses. • Patient dashboard. • Doctor dashboard. • Patient detail page. • Search/filter. • Consultation history. 

### **Output** 

The end-to-end consultation lifecycle exists without AI. 

## **Sprint 4 — Documents and Notifications** 

### **Goal** 

Build secure document storage and operational notifications. 

### **Build** 

- S3 upload URLs. 

- Private document storage. 

- Document metadata. 

- Report uploads. 

- Prescription uploads. 

- SES integration. 

- SQS email jobs. 

- Booking confirmation. 

- Meeting scheduling emails. 

- Report notification emails. 

41 

### **Output** 

The platform can securely store documents and reliably notify patients/doctors. 

## **Sprint 5 — Document Intelligence and RAG** 

### **Goal** 

Build the document processing pipeline. 

### **Build** 

- SQS document queue. • Worker service. • PDF extraction. • Textract integration. • OCR workflow. • Chunking. • Embedding generation. • pgvector storage. • Metadata filtering. • Patient-scoped retrieval. • Document processing status. • Retry and failure handling. 

### **Output** 

Patient documents become searchable through secure semantic retrieval. 

## **Sprint 6 — AI Assistant and Tool Orchestration** 

### **Goal** 

Build the doctor AI assistant. 

### **Build** 

- AI chat interface. 

- Intent router. • SQL tool. • RAG tool. • Analytics tool. • Patient context tool. • Bedrock integration. • Guardrails. 

42 

- Multi-step orchestration. 

- Authorization-aware tool execution. 

### **Output** 

Doctor can ask natural-language questions across structured and unstructured patient data. 

## **Sprint 7 — Admin, Analytics, Reliability and Security** 

### **Goal** 

Make the platform production-oriented. 

### **Build** 

• Admin panel. • User management. • Booking controls. • Holiday settings. • Email template management. • Analytics dashboard. • CloudWatch alarms. • Audit logs. • Security review. • Backup strategy. • Error handling. • Dead-letter queue handling. • Rate limiting strategy. 

### **Output** 

The platform becomes operationally manageable. 

## **Sprint 8 — Testing, Deployment and Production Hardening** 

### **Goal** 

Prepare the system for real users. 

### **Build** 

- Unit tests. • Integration tests. • API tests. 

- Security tests. 

43 

- Authorization tests. 

- RAG evaluation. 

- AI response evaluation. 

- Prompt injection tests. 

- Patient data isolation tests. 

- Document access tests. 

- Load tests. 

- Mobile responsiveness. 

- Production deployment. 

- Monitoring dashboards. 

- Operational runbook. 

- Final documentation. 

### **Output** 

A production-ready, documented, monitored Ayurveda AI platform. 

# **31. Testing Strategy** 

Testing must cover the three systems independently and together. 

## **Clinical System** 

- Patient can only access own records. 

- Doctor can access authorized patient records. 

- Admin can manage system users. 

- Client ID never changes. 

- Appointment state transitions are valid. 

- Reports are linked to the correct consultation. 

## **Document System** 

- Files are private. 

- Upload URL authorization works. 

- Unauthorized users cannot access documents. 

- Document metadata points to correct patient. 

- Failed processing retries. 

- Duplicate document handling works. 

- RAG filters are enforced. 

## **AI System** 

- SQL results are accurate. 

- SQL cannot perform destructive operations. 

- RAG retrieves correct patient data. 

44 

- RAG does not leak cross-patient information. 

- Analytics match direct SQL calculations. 

- Guardrails trigger correctly. 

- Prompt injection attempts are contained. 

- Hallucination is minimized. 

- AI clearly indicates missing evidence. 

# **32. Definition of Production Ready** 

The project should not be considered production-ready merely because it is deployed. 

It is production-ready when: 

```
Authentication        -> Secure
Authorization         -> Enforced server-side
Patient isolation     -> Verified
Documents             -> Private
Database              -> Backed up
Uploads               -> Resilient
Background jobs       -> Retryable
Emails                -> Observable
AI tools              -> Controlled
RAG                   -> Permission-aware
AI outputs            -> Guardrailed
Logs                  -> Centralized
Errors                -> Monitored
Backups               -> Tested
Deployment            -> Repeatable
Frontend              -> Mobile responsive
```

# **33. Cost-Conscious Initial Deployment** 

For the first real deployment, keep the architecture simple but preserve the logical boundaries. 

Recommended initial runtime: 

```
Amplify
+
Lightsail FastAPI
+
Neon PostgreSQL + pgvector
```

45 

```
+
S3
+
SQS
+
Bedrock pay-per-use model
+
SES
+
CloudWatch
```

Avoid starting with: 

- ECS/Fargate before needed. • Aurora before needed. • Dedicated vector database. • Kubernetes. • Kafka. 

- Multiple AI providers in production. • Microservices for every domain. 

The application should be a modular monolith at first, with three logical systems and clear internal boundaries. 

That gives you: 

```
Low operational complexity
            +
Clean architecture
            +
Clear AI separation
            +
Future scaling path
```

# **34. Recommended Initial Architecture Philosophy** 

The application should be: 

```
Modular Monolith
       +
Asynchronous Workers
       +
Managed Cloud Services
```

46 

```
       +
Explicit AI Tool Boundaries
```

Not: 

```
Many Microservices
       +
Complex Kubernetes
       +
Independent DB per service
```

at the beginning. 

The three systems are **logical architectural boundaries** , not necessarily three separate deployable microservices. 

Initial deployment can therefore be: 

```
FastAPI Container
   |
   +--> Clinical/Business Modules
   +--> AI Orchestration Modules
   +--> Document APIs
Worker Container
   |
   +--> Document Processing
   +--> Email Processing
```

Later, if scale requires it: 

```
ECS/Fargate
   |
   +--> API Service
   +--> Document Worker
   +--> Email Worker
   +--> AI Worker
```

# **35. Final Mental Model** 

Think about the platform as three connected layers. 

47 

## **Layer 1 — Clinical Truth** 

```
Patients
Consultations
Appointments
Reports
Doctor Notes
Admin
```

Owned by: 

```
PostgreSQL + S3
```

## **Layer 2 — Document Intelligence** 

```
Documents
OCR
Extraction
Chunking
Embeddings
Vector Search
RAG
```

Owned by: 

```
S3 + SQS + Textract + pgvector
```

## **Layer 3 — AI Intelligence** 

```
Natural Language
Intent Routing
SQL Tool
RAG Tool
Analytics Tool
Bedrock
Guardrails
```

Owned by: 

48 

#### `FastAPI AI Orchestrator + Bedrock` 

The data flow is: 



<!-- Start of picture text -->
                    CLINICAL TRUTH<br>                          |<br>                          | structured data<br>                          v<br>                 PostgreSQL / Neon PostgreSQL<br>                          |<br>                          v<br>                    SQL / Analytics<br>                          |<br>                          |<br>                          +------------------+<br>                                             |<br>                                             v<br>                                      AI ORCHESTRATOR<br>                                             ^<br>                                             |<br>                                             |<br>                    DOCUMENT INTELLIGENCE   |<br>                                             |<br>Documents -> S3 -> SQS -> Textract -> Embeddings -> pgvector<br>                                             |<br>                                             v<br>                                         RAG Tool<br>                                             |<br>                                             +------------------+<br>                                                                |<br>                                                                v<br>                                                            Bedrock<br>                                                                |<br>                                                                v<br>                                                            Guardrails<br>                                                                |<br>                                                                v<br>                                                         Doctor Assistant<br><!-- End of picture text -->

# **36. Final Architecture Decision** 

The final recommended platform is: 

49 

```
FRONTEND
React + Vite
    |
    v
AWS Amplify Hosting
BACKEND
FastAPI + Docker
    |
    v
AWS Lightsail initially
    |
    v
ECS + Fargate later when justified
AUTHENTICATION
Amazon Cognito
    |
    v
Role + Resource Authorization
CLINICAL / BUSINESS DATA
Neon PostgreSQL PostgreSQL
    |
    +--> Business Tables
    +--> Consultation History
    +--> Appointments
    +--> Reports Metadata
    +--> Analytics Data
    +--> pgvector
DOCUMENT INTELLIGENCE
Amazon S3
    |
    v
Amazon SQS
    |
    v
Worker
    |
    +--> Amazon Textract
    +--> Chunking
    +--> Embeddings
    |
    v
PostgreSQL + pgvector
```

50 

```
AI ASSISTANT
Intent Router
    |
    +--> SQL Tool
    +--> RAG Tool
    +--> Analytics Tool
    +--> Patient Context Tool
    |
    v
Amazon Bedrock
    |
    v
Amazon Bedrock Guardrails
    |
    v
Doctor AI Assistant
NOTIFICATIONS
SQS -> Email Worker -> Amazon SES
OBSERVABILITY
Amazon CloudWatch
```

This is the architecture to build toward. 

The central design principle is: 

#### **PostgreSQL is the source of structured clinical truth, S3 is the source of document files, pgvector is the searchable representation of document knowledge, and the AI layer can only reach these systems through controlled, authorization-aware tools.** 

That principle gives the platform a strong foundation for security, RAG accuracy, maintainability, and future growth while keeping the first production deployment practical and cost-conscious. 

51 

