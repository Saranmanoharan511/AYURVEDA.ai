# **<u>SPRINT PLANNING AND SUBTASKS FOR EACH SPRINT</u>** 

Here is a detailed sub-task breakdown for each of the eight sprints outlined in the "Ayurveda Ai Platform — Final Production Architecture & Project Blueprint.pdf". 

## **Database Hosting Decision — Neon PostgreSQL**

All sprints use **Neon PostgreSQL** as the managed PostgreSQL platform. PostgreSQL remains the transactional source of truth and pgvector remains the vector-search layer. The AWS services around the database remain unchanged.

## **Sprint 1: Foundation and Cloud Setup** 

**Goal:** Create the project foundation and AWS environment. 

1. Initialize the frontend repository using React and Vite. 

2. Set up the frontend routing structure (e.g., /patient, /doctor, /admin) using react-router. 

3. Initialize the backend repository using FastAPI and Python. 

4. Create the initial FastAPI project structure (e.g., api/, core/, models/, services/) as defined in the service boundaries. 

5. Write a Dockerfile and docker-compose.yml for local FastAPI and PostgreSQL development. 

6. Create the Neon PostgreSQL project/database to serve as the managed production database. 

7. Set up SQLAlchemy (or equivalent ORM) in FastAPI and establish a secure connection to the Neon PostgreSQL database. 

8. Create foundational database migration scripts (e.g., Alembic) for the initial Neon PostgreSQL schema. 

9. Provision a private Amazon S3 bucket for secure document storage. 

10. Configure AWS Amplify Hosting and connect it to the frontend Git repository for automated deployments. 

11. Set up an AWS Lightsail container environment for the initial backend deployment. 

12. Configure backend environment variables (.env) for local, staging, and production, including environment-specific Neon PostgreSQL connection settings. 

13. Integrate Amazon CloudWatch for basic FastAPI application logging. 

14. Create a health-check endpoint (/ping or /health) in FastAPI to verify server and database connectivity. 

## **Sprint 2: Authentication and Roles** 

**Goal:** Implement secure identity and access control. 

1. Provision an Amazon Cognito User Pool for user authentication and identity management. 

2. Configure three distinct user roles (Patient, Doctor, Admin) within Cognito or application logic. 

3. Implement backend JWT validation in FastAPI to verify Cognito tokens on incoming requests. 

4. Build a Role-Based Access Control (RBAC) middleware in FastAPI to protect specific routes based on user roles. 

5. Create the users table schema in PostgreSQL (id, cognito_sub, role, status). 

6. Develop the patient registration and login API endpoints. 

7. Develop the doctor and admin login API endpoints. 

8. Build the frontend Patient sign-up and sign-in components. 

9. Build the frontend Doctor and Admin login components. 

10. Implement frontend route guards to restrict unauthorized access to protected dashboard pages. 

11. Build resource-level authorization helpers in FastAPI to ensure users can only access records matching their ID or authorized scope. 

12. Create API endpoints to fetch the current authenticated user's profile. 

## **Sprint 3: Clinical / Business System** 

**Goal:** Build the core consultation platform. 

1. Create PostgreSQL schema migrations for patients (using UUIDs and public client_id) and doctors tables. 

2. Create PostgreSQL schema migrations for consultations, appointments, and consultation_notes tables. 

3. Develop FastAPI endpoints for creating and updating patient profiles. 

4. Develop FastAPI endpoints to handle the consultation lifecycle (create, update status, complete). 

5. Implement the recommended state machine logic for appointments (e.g., APPOINTMENT_BOOKED -> MEETING_SCHEDULED -> CONSULTATION_COMPLETED). 

6. Build the Patient Dashboard UI, including profile management and consultation history. 

7. Build the Book Consultation UI flow for patients (capturing reason, description, etc.). 

8. Build the Doctor Dashboard UI (showing waiting/scheduled/completed consultations). 

9. Build the Doctor's Client Search and Patient Detail page UI. 

10. Develop FastAPI endpoints for doctors to add consultation notes (diagnosis, ayurvedic assessment, medicines, advice). 

11. Implement the API endpoint for doctors to schedule a meeting and input a Zoom link. 

12. Connect frontend forms to the corresponding FastAPI endpoints and handle loading/error states. 

## **Sprint 4: Documents and Notifications** 

**Goal:** Build secure document storage and operational notifications. 

1. Create PostgreSQL schema migrations for reports, patient_documents, and notifications tables. 

2. Develop a FastAPI endpoint to verify upload permissions and generate pre-signed S3 upload URLs. 

3. Build the frontend UI for patients and doctors to select files and upload them directly to S3 using the pre-signed URLs. 

4. Develop a FastAPI endpoint to save document metadata (object key, document type, patient ID) to PostgreSQL after a successful S3 upload. 

5. Develop a FastAPI endpoint to generate short-lived, pre-signed download URLs for secure document retrieval. 

6. Set up an Amazon SQS queue to handle asynchronous background jobs. 

7. Configure Amazon SES (Simple Email Service) for sending transactional emails. 

8. Create a background worker script to listen to the SQS queue and send emails via SES. 

9. Integrate an SQS event trigger in the FastAPI appointment scheduling endpoint to queue a "Meeting Scheduled" email. 

10. Integrate an SQS event trigger in the consultation booking endpoint to queue a "Booking Confirmation" email. 

11. Integrate an SQS event trigger when a doctor uploads a report to notify the patient. 

12. Build the frontend UI for doctors to upload prescription PDFs and reports to a specific consultation. 

## **Sprint 5: Document Intelligence and RAG** 

**Goal:** Build the document processing pipeline. 

1. Enable and validate the pgvector extension in the Neon PostgreSQL database. 

2. Create a dedicated SQS queue for the asynchronous document processing pipeline. 

3. Build a Document Processing Worker service in Python to poll the document queue. 

4. Integrate Amazon Textract into the worker to extract text from scanned documents and PDFs. 

5. Implement a document normalization and chunking strategy (splitting extracted text into manageable chunks). 

6. Attach required security metadata (e.g., patient_id, consultation_id) to every document chunk. 

7. Integrate a configurable embedding provider to convert text chunks into vector embeddings. 

8. Store the resulting chunk vectors and metadata into PostgreSQL using pgvector. 

9. Implement the database failure path logic (logging errors, retrying processing, dead-letter queue routing). 

10. Update the patient_documents table status to AVAILABLE_FOR_RAG only upon successful pipeline completion. 

11. Develop a FastAPI endpoint to allow doctors to securely search/filter document metadata. 

12. Write a base retrieval function that strictly enforces WHERE patient_id = authorized_patient_id during vector search. 

## **Sprint 6: AI Assistant and Tool Orchestration** 

**Goal:** Build the doctor AI assistant. 

1. Build the frontend AI Chat Interface component for the doctor dashboard. 

2. Create the FastAPI AI endpoint (/api/v1/ai/chat) to receive doctor prompts. 

3. Set up the AI Orchestrator graph logic (e.g., LangGraph-style routing) in the backend. 

4. Develop the **SQL Tool** : Write safe, read-only queries for structured PostgreSQL data (e.g., fetching appointment status or patient counts). 

5. Develop the **Patient Context Tool** : Create logic to compile a holistic view of a patient (profile, past consultations) based on client_id. 

6. Develop the **RAG Tool** : Connect the previously built pgvector retrieval function to fetch semantically relevant, patient-scoped chunks. 

7. Develop the **Analytics Tool** : Create PostgreSQL aggregation queries for monthly metrics and trends. 

8. Implement the Intent Router to analyze the doctor's question and select the appropriate tool(s). 

9. Integrate Amazon Bedrock to serve as the foundational Large Language Model (LLM) for synthesizing evidence. 

10. Configure and integrate Amazon Bedrock Guardrails to enforce AI safety, prevent hallucination, and block medical diagnosing. 

11. Implement multi-step orchestration so the AI can combine outputs from the SQL tool and RAG tool before calling Bedrock. 

12. Format the final grounded response and return it to the frontend AI chat UI. 

## **Sprint 7: Admin, Analytics, Reliability and Security** 

**Goal:** Make the platform production-oriented. 

1. Build the Admin Dashboard UI in the React frontend. 

2. Develop FastAPI endpoints for user and doctor management (e.g., blocking/unblocking users). 

3. Develop FastAPI endpoints for system configuration (e.g., toggling booking ON/OFF, setting holidays). 

4. Build an interface and backend logic to manage and update SES email templates. 

5. Create a System Analytics API endpoint calculating total consultations, active patients, and platform usage metrics. 

6. Build the frontend Analytics page to visualize data from the Analytics Tool and API. 

7. Implement comprehensive database Audit Logs for sensitive actions across the platform. 

8. Configure advanced Amazon CloudWatch alarms (e.g., FastAPI 5xx rate, SQS queue depth, Bedrock errors). 

9. Implement a rate-limiting strategy on public-facing FastAPI endpoints. 

10. Set up dead-letter queue (DLQ) visibility and retry mechanisms in the Admin panel for failed document processing. 

11. Review and lock down S3 bucket policies to ensure they are strictly private. 

12. Validate that Neon PostgreSQL backup and recovery configuration is active and documented. 

## **Sprint 8: Testing, Deployment and Production Hardening** 

**Goal:** Prepare the system for real users. 

1. Write automated unit tests for core FastAPI business logic and models. 

2. Write integration tests verifying that API routes correctly interact with the PostgreSQL database. 

3. Implement strict authorization tests ensuring cross-patient data access is rejected (Patient Isolation). 

4. Write security tests to confirm S3 upload/download URLs are short-lived and enforce permissions. 

5. Conduct RAG evaluation tests to ensure vector retrieval respects patient and consultation boundaries. 

6. Perform Prompt Injection tests on the AI orchestrator to ensure document content cannot override system instructions. 

7. Run simulated load tests to verify Lightsail/Neon PostgreSQL performance under concurrent user sessions. 

8. Perform comprehensive UI testing to ensure the React frontend is fully mobile responsive. 

9. Finalize the production environment configuration (Vite environment variables, FastAPI .env secrets). 

10. Execute the final CI/CD pipeline via GitHub and AWS Amplify to deploy the production frontend. 

11. Deploy the final FastAPI Docker container and background workers to the production Lightsail/ECS environment. 

12. Build operational runbook documentation detailing backup restoration and error handling procedures. 

13. Complete a final end-to-end verification of the 4 main workflows (Booking, Scheduling, Reporting, AI Query). 

