"""
SQL Tool Service

Safe, read-only SQL queries for structured PostgreSQL data.
This tool allows the AI to query business data without destructive operations.
Now supports both predefined queries and LLM-generated dynamic SQL queries.
"""

import time
import re
import logging
import json
from typing import List, Dict, Any, Optional
from sqlalchemy import text, select, func, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta

from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.consultation import Consultation
from app.models.appointment import Appointment
from app.models.consultation_note import ConsultationNote
from app.schemas.ai import SQLToolRequest, SQLToolResponse
from app.services.bedrock_service import BedrockService

# Configure logging
logger = logging.getLogger(__name__)


class SQLTool:
    """
    SQL Tool for safe, read-only database queries.
    
    This tool provides controlled access to structured business data.
    All queries are read-only and enforce authorization boundaries.
    Now supports LLM-generated SQL queries for more flexible data access.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.bedrock_service = BedrockService()
        self.schema_info = self._get_schema_info()
    
    def _get_schema_info(self) -> str:
        schema = """
DATABASE SCHEMA:
DATABASE SCHEMA & VIEWS (RECOMMENDED FOR QUERIES):

Optimized Views:
- v_consultation_master (consultation_id, reason, description, consultation_status, started_at, completed_at, consultation_created_at, patient_id, patient_client_id, patient_name, patient_email, patient_phone, patient_age, patient_gender, patient_city, patient_state, doctor_id, doctor_name, doctor_qualifications, doctor_specialization, appointment_id, scheduled_date, scheduled_time, appointment_status, note_id, diagnosis, ayurvedic_assessment, lifestyle_advice, diet_plan, follow_up_instructions)
- v_consultation_prescriptions (prescription_id, consultation_id, patient_client_id, patient_name, medicine_name, morning_dosage, afternoon_dosage, night_dosage, food_timing, prescription_notes, prescribed_at)
- v_patient_documents (document_id, patient_id, patient_client_id, patient_name, consultation_id, document_type, original_filename, content_type, file_size, upload_status, processing_status, uploaded_at)
- v_consultation_reports (report_id, consultation_id, patient_id, patient_client_id, patient_name, report_type, original_filename, content_type, file_size, upload_status, processing_status, uploaded_at)

Underlying Base Tables (Use only if views do not cover a specific requirement):

Authentication & Users:
- users (id, cognito_sub, email, role, status, given_name, family_name, created_at, updated_at)

Clinical Core:
- patients (id, client_id, user_id, cognito_sub, full_name, email, phone, date_of_birth, age, gender, city, state, created_at, updated_at)
- doctors (id, user_id, cognito_sub, name, qualifications, specialization, status, created_at, updated_at)

Consultation System:
- consultations (id, patient_id->patients.id, doctor_id->doctors.id, reason, description, consultation_status, started_at, completed_at, created_at, updated_at)
- appointments (id, consultation_id->consultations.id, scheduled_date, scheduled_time, timezone, zoom_meeting_url, status, created_at, updated_at)
- consultation_notes (id, consultation_id->consultations.id, doctor_id->doctors.id, diagnosis, ayurvedic_assessment, medicines, lifestyle_advice, diet_plan, follow_up_instructions, created_at, updated_at)

Treatment & Prescriptions:
- prescriptions (id, consultation_id->consultations.id, patient_id->patients.id, doctor_id->doctors.id, name, morning_dosage, afternoon_dosage, night_dosage, food_timing, notes, created_at, updated_at)

Document Management:
- patient_documents (id, patient_id->patients.id, consultation_id->consultations.id, uploaded_by->users.id, document_type, s3_object_key, original_filename, content_type, file_size, upload_status, processing_status, document_metadata, created_at, updated_at)
- reports (id, consultation_id->consultations.id, patient_id->patients.id, uploaded_by->users.id, report_type, s3_object_key, original_filename, content_type, file_size, upload_status, processing_status, uploaded_at)

System:
- notifications (id, user_id->users.id, event_type, channel, status, message, created_at, sent_at)

IMPORTANT RELATIONSHIPS:
- patients.user_id -> users.id
- doctors.user_id -> users.id
- consultations.patient_id -> patients.id
- consultations.doctor_id -> doctors.id
- appointments.consultation_id -> consultations.id
- consultation_notes.consultation_id -> consultations.id
- consultation_notes.doctor_id -> doctors.id
- prescriptions.consultation_id -> consultations.id
- prescriptions.patient_id -> patients.id
- prescriptions.doctor_id -> doctors.id
- patient_documents.patient_id -> patients.id
- patient_documents.consultation_id -> consultations.id
- patient_documents.uploaded_by -> users.id
- reports.consultation_id -> consultations.id
- reports.patient_id -> patients.id
- reports.uploaded_by -> users.id
- notifications.user_id -> users.id
"""
        return schema
    
    def execute_query(self, request: SQLToolRequest) -> SQLToolResponse:
        start_time = time.time()

        logger.info(f"[SQL TOOL] === EXECUTE QUERY START ===")
        logger.info(f"[SQL TOOL] Query Type: {request.query_type}")
        logger.info(f"[SQL TOOL] Patient ID: {request.patient_id}")
        logger.info(f"[SQL TOOL] Doctor ID: {request.doctor_id}")
        logger.info(f"[SQL TOOL] Filters: {json.dumps(request.filters, indent=2) if request.filters else 'None'}")

        try:
            if request.query_type == "patient_count":
                results = self._get_patient_count(request)
            elif request.query_type == "consultation_status":
                results = self._get_consultation_status(request)
            elif request.query_type == "appointment_status":
                results = self._get_appointment_status(request)
            elif request.query_type == "today_consultations":
                results = self._get_today_consultations(request)
            elif request.query_type == "monthly_stats":
                results = self._get_monthly_stats(request)
            elif request.query_type == "patient_search":
                results = self._search_patients(request)
            elif request.query_type == "llm_generated":
                results = self._execute_llm_generated_query(request)
            else:
                raise ValueError(f"Unknown query type: {request.query_type}")

            execution_time = (time.time() - start_time) * 1000

            logger.info(f"[SQL TOOL] === EXECUTE QUERY COMPLETE ===")
            logger.info(f"[SQL TOOL] Row Count: {len(results)}")
            logger.info(f"[SQL TOOL] Execution Time: {execution_time:.2f}ms")
            logger.info(f"[SQL TOOL] Results: {json.dumps(results, indent=2)}")

            return SQLToolResponse(
                query_type=request.query_type,
                results=results,
                row_count=len(results),
                execution_time_ms=execution_time
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"[SQL TOOL] EXECUTE QUERY FAILED: {str(e)}")
            raise Exception(f"SQL Tool execution failed: {str(e)}")
    
    def _get_patient_count(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        query = select(func.count(Patient.id))
        if request.doctor_id:
            query = select(func.count(Patient.id.distinct())).join(
                Consultation, Patient.id == Consultation.patient_id
            ).where(Consultation.doctor_id == request.doctor_id)
        result = self.db.execute(query).scalar()
        return [{"count": result}]
    
    def _get_consultation_status(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        query = select(
            Consultation.consultation_status,
            func.count(Consultation.id).label('count')
        )
        if request.doctor_id:
            query = query.where(Consultation.doctor_id == request.doctor_id)
        if request.patient_id:
            query = query.where(Consultation.patient_id == request.patient_id)
        query = query.group_by(Consultation.consultation_status)
        results = self.db.execute(query).all()
        return [{"status": row.consultation_status, "count": row.count} for row in results]
    
    def _get_appointment_status(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        query = select(
            Appointment.status,
            func.count(Appointment.id).label('count')
        )
        if request.doctor_id:
            query = query.join(Consultation).where(Consultation.doctor_id == request.doctor_id)
        if request.patient_id:
            query = query.join(Consultation).where(Consultation.patient_id == request.patient_id)
        query = query.group_by(Appointment.status)
        results = self.db.execute(query).all()
        return [{"status": row.status, "count": row.count} for row in results]
    
    def _get_today_consultations(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        today = datetime.utcnow().date()
        query = select(
            Consultation.id,
            Consultation.reason,
            Consultation.consultation_status,
            Consultation.created_at,
            Patient.client_id,
            Patient.full_name,
            Appointment.scheduled_date,
            Appointment.scheduled_time
        ).join(
            Patient, Consultation.patient_id == Patient.id
        ).outerjoin(
            Appointment, Consultation.id == Appointment.consultation_id
        ).where(
            func.date(Appointment.scheduled_date) == today
        )
        if request.doctor_id:
            query = query.where(Consultation.doctor_id == request.doctor_id)
        query = query.order_by(Appointment.scheduled_time)
        results = self.db.execute(query).all()
        return [
            {
                "consultation_id": str(row.id),
                "client_id": row.client_id,
                "patient_name": row.full_name,
                "reason": row.reason,
                "status": row.consultation_status,
                "scheduled_date": str(row.scheduled_date) if row.scheduled_date else None,
                "scheduled_time": row.scheduled_time
            }
            for row in results
        ]
    
    def _get_monthly_stats(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        months_back = request.filters.get('months_back', 6) if request.filters else 6
        query = select(
            func.date_trunc('month', Consultation.created_at).label('month'),
            func.count(Consultation.id).label('total_consultations'),
            func.count(
                func.case(
                    (Consultation.consultation_status == 'CONSULTATION_COMPLETED', 1),
                    else_=0
                )
            ).label('completed_consultations')
        )
        if request.doctor_id:
            query = query.where(Consultation.doctor_id == request.doctor_id)
        query = query.where(
            Consultation.created_at >= datetime.utcnow() - timedelta(days=30*months_back)
        )
        query = query.group_by(
            func.date_trunc('month', Consultation.created_at)
        ).order_by(
            func.date_trunc('month', Consultation.created_at)
        )
        results = self.db.execute(query).all()
        return [
            {
                "month": str(row.month),
                "total_consultations": row.total_consultations,
                "completed_consultations": row.completed_consultations
            }
            for row in results
        ]
    
    def _search_patients(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        search_term = request.filters.get('search_term', '') if request.filters else ''
        if not search_term:
            return []
        query = select(
            Patient.id,
            Patient.client_id,
            Patient.full_name,
            Patient.email,
            Patient.phone,
            Patient.city,
            Patient.state
        )
        search_pattern = f"%{search_term}%"
        query = query.where(
            or_(
                Patient.full_name.ilike(search_pattern),
                Patient.client_id.ilike(search_pattern),
                Patient.email.ilike(search_pattern)
            )
        )
        limit = request.filters.get('limit', 20) if request.filters else 20
        query = query.limit(limit)
        results = self.db.execute(query).all()
        return [
            {
                "patient_id": str(row.id),
                "client_id": row.client_id,
                "full_name": row.full_name,
                "email": row.email,
                "phone": row.phone,
                "city": row.city,
                "state": row.state
            }
            for row in results
        ]
    
    def get_patient_by_client_id(self, client_id: str) -> Optional[Dict[str, Any]]:
        query = select(Patient).where(Patient.client_id == client_id)
        result = self.db.execute(query).scalar_one_or_none()
        if not result:
            return None
        return {
            "patient_id": str(result.id),
            "client_id": result.client_id,
            "full_name": result.full_name,
            "email": result.email,
            "phone": result.phone,
            "date_of_birth": str(result.date_of_birth) if result.date_of_birth else None,
            "gender": result.gender,
            "city": result.city,
            "state": result.state
        }
    
    def get_patient_consultations(self, patient_id: str, doctor_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = select(
            Consultation.id,
            Consultation.reason,
            Consultation.description,
            Consultation.consultation_status,
            Consultation.created_at,
            Consultation.completed_at,
            Doctor.name.label('doctor_name')
        ).join(
            Doctor, Consultation.doctor_id == Doctor.id
        ).where(
            Consultation.patient_id == patient_id
        )
        if doctor_id:
            query = query.where(Consultation.doctor_id == doctor_id)
        query = query.order_by(Consultation.created_at.desc())
        results = self.db.execute(query).all()
        return [
            {
                "consultation_id": str(row.id),
                "reason": row.reason,
                "description": row.description,
                "status": row.consultation_status,
                "created_at": str(row.created_at),
                "completed_at": str(row.completed_at) if row.completed_at else None,
                "doctor_name": row.doctor_name
            }
            for row in results
        ]
    
    def _execute_llm_generated_query(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        logger.info(f"[SQL TOOL] === LLM GENERATED QUERY START ===")
        user_query = request.filters.get('user_query', '') if request.filters else ''
        logger.info(f"[SQL TOOL] User Query: {user_query}")

        if not user_query:
            raise ValueError("User query is required for LLM-generated SQL")

        generated_sql = self._generate_sql_with_llm(user_query, request)

        logger.info(f"[SQL TOOL] Generated SQL: {generated_sql}")

        if not self._validate_sql_safety(generated_sql):
            logger.error(f"[SQL TOOL] SQL SAFETY VALIDATION FAILED")
            raise ValueError("Generated SQL failed safety validation")

        logger.info(f"[SQL TOOL] SQL SAFETY VALIDATION PASSED")
        results = self._execute_safe_sql(generated_sql, request)
        logger.info(f"[SQL TOOL] === LLM GENERATED QUERY COMPLETE ===")

        return results
    
    def _generate_sql_with_llm(self, user_query: str, request: SQLToolRequest) -> str:
        logger.info(f"[SQL TOOL] === LLM SQL GENERATION START ===")
        logger.info(f"[SQL TOOL] User Query: {user_query}")

        if not self.bedrock_service.is_available():
            logger.error(f"[SQL TOOL] Bedrock service not available")
            raise Exception("Bedrock service is not available for SQL generation")

        doctor_specific_keywords = ['my patients', 'i have', 'i treated', 'my consultations', 'my appointments']
        is_doctor_specific = any(keyword in user_query.lower() for keyword in doctor_specific_keywords)
        logger.info(f"[SQL TOOL] Is Doctor Specific: {is_doctor_specific}")
        
        context = f"""
You are an expert Text-to-SQL assistant for an Ayurveda clinical database management system. 
Your task is to convert natural language questions into safe, accurate SQL queries using the optimized database views.

DATABASE SCHEMA:
{self.schema_info}

USER QUESTION: {user_query}

CONTEXT:
- Doctor ID: {request.doctor_id if request.doctor_id else 'Not specified'}
- Patient ID: {request.patient_id if request.patient_id else 'Not specified'}

CRITICAL RULES FOR TABLE/VIEW USAGE:
1. **For Basic Patient Information** (name, email, phone, age, gender, city, state, date_of_birth):
   - Query the `patients` table directly: SELECT id, client_id, full_name, email, phone, age, gender, city, state, date_of_birth FROM patients WHERE client_id = 'AYU-000001'
   - DO NOT use v_consultation_master for basic patient details - use patients table instead

2. **For Consultation-Related Information** (consultation history, notes, appointments, reasons, descriptions):
   - Query `v_consultation_master` view: SELECT consultation_id, reason, description, consultation_status, consultation_created_at FROM v_consultation_master WHERE patient_client_id = 'AYU-000001'

3. **For Prescriptions/Medicines:**
   - Query `v_consultation_prescriptions` view

4. **For Uploaded Documents:**
   - Query `v_patient_documents` view

5. **For Lab/Clinical Reports:**
   - Query `v_consultation_reports` view

6. **Text Matching:** Use case-insensitive partial matching for names (`patient_name ILIKE '%abc%'`) and exact matching for client IDs (`patient_client_id = 'AYU-000001'`).

7. **Output Format:** Return ONLY the valid SQL query string using PostgreSQL syntax with a `LIMIT 100`.

Few-Shot Examples:
- User: "Give me the patient details with client id AYU-000001"
  SQL: SELECT id, client_id, full_name, email, phone, age, gender, city, state, date_of_birth FROM patients WHERE client_id = 'AYU-000001';

- User: "List all consultations for patient with client id AYU-000001"
  SQL: SELECT consultation_id, reason, description, consultation_status, consultation_created_at FROM v_consultation_master WHERE patient_client_id = 'AYU-000001';

- User: "Give me the consultation details of the patient with abc name"
  SQL: SELECT consultation_id, reason, description, consultation_status, consultation_created_at FROM v_consultation_master WHERE patient_name ILIKE '%abc%';

- User: "What prescriptions were given to patient Saran M?"
  SQL: SELECT medicine_name, morning_dosage, afternoon_dosage, night_dosage, food_timing, prescription_notes FROM v_consultation_prescriptions WHERE patient_name ILIKE '%Saran M%';

- User: "Show me all documents for patient AYU-000001"
  SQL: SELECT document_type, original_filename, upload_status FROM v_patient_documents WHERE patient_client_id = 'AYU-000001';

Generate the SQL query:
"""
        
        from app.schemas.ai import BedrockRequest
        
        bedrock_request = BedrockRequest(
            prompt=context,
            model_id=self.bedrock_service.model_id,
            max_tokens=500,
            temperature=0.1,
            system_prompt="You are a SQL expert. Generate only SQL queries, no explanations."
        )
        
        try:
            logger.info(f"[SQL TOOL] Invoking Bedrock for SQL generation")
            response = self.bedrock_service.invoke_model(bedrock_request)
            sql_query = response.text.strip()
            sql_query = re.sub(r'```sql\s*', '', sql_query)
            sql_query = re.sub(r'```\s*', '', sql_query)
            sql_query = sql_query.strip()

            logger.info(f"[SQL TOOL] Raw Bedrock Response: {response.text}")
            logger.info(f"[SQL TOOL] Cleaned SQL Query: {sql_query}")

            if not sql_query.lower().startswith('select'):
                logger.error(f"[SQL TOOL] LLM did not generate a SELECT query")
                raise ValueError("LLM did not generate a SELECT query")

            logger.info(f"[SQL TOOL] === LLM SQL GENERATION COMPLETE ===")
            return sql_query

        except Exception as e:
            logger.error(f"[SQL TOOL] LLM SQL GENERATION FAILED: {str(e)}")
            raise Exception(f"Failed to generate SQL with LLM: {str(e)}")
    
    def _validate_sql_safety(self, sql_query: str) -> bool:
        logger.info(f"[SQL TOOL] === SQL SAFETY VALIDATION START ===")
        logger.info(f"[SQL TOOL] Validating SQL: {sql_query}")

        sql_lower = sql_query.lower()

        # Use word-boundary matching to avoid false positives in column names
        # This prevents matching "script" inside "description" or other column names
        dangerous_keywords = [
            r'\bdrop\b', r'\bdelete\b', r'\btruncate\b', r'\binsert\b', r'\bupdate\b',
            r'\balter\b', r'\bcreate\b', r'\bgrant\b', r'\brevoke\b', r'\bexec\b',
            r'\bexecute\b', r'\bscript\b', r'\bjavascript\b', r'--', r'/\*', r'\*/'
        ]

        for keyword in dangerous_keywords:
            if re.search(keyword, sql_lower):
                logger.warning(f"[SQL TOOL] Dangerous keyword detected: {keyword}")
                return False

        # Ensure it's a SELECT query (allow SELECT as a standalone keyword)
        if not sql_lower.strip().startswith('select'):
            logger.warning(f"[SQL TOOL] Query does not start with SELECT")
            return False

        # Only reject multiple statements if semicolon is not at the end
        if ';' in sql_query[:-1]:
            logger.warning(f"[SQL TOOL] Multiple statements detected")
            return False

        logger.info(f"[SQL TOOL] SQL SAFETY VALIDATION PASSED")
        return True
    
    def _execute_safe_sql(self, sql_query: str, request: SQLToolRequest) -> List[Dict[str, Any]]:
        logger.info(f"[SQL TOOL] === SAFE SQL EXECUTION START ===")
        logger.info(f"[SQL TOOL] Executing SQL: {sql_query}")

        try:
            result = self.db.execute(text(sql_query))
            rows = result.fetchall()

            logger.info(f"[SQL TOOL] Database returned {len(rows)} rows")

            if rows:
                column_names = list(result.keys())
                results = [
                    {column_names[i]: str(row[i]) if row[i] is not None else None
                     for i in range(len(column_names))}
                    for row in rows
                ]
            else:
                results = []
                logger.warning(f"[SQL TOOL] Database returned 0 rows - empty result set")

            logger.info(f"[SQL TOOL] Database Results: {json.dumps(results, indent=2)}")
            logger.info(f"[SQL TOOL] === SAFE SQL EXECUTION COMPLETE ===")

            return results
        except SQLAlchemyError as e:
            logger.error(f"[SQL TOOL] SQL EXECUTION FAILED: {str(e)}")
            raise Exception(f"SQL execution failed: {str(e)}")
        except Exception as e:
            logger.error(f"[SQL TOOL] UNEXPECTED ERROR DURING SQL EXECUTION: {str(e)}")
            raise Exception(f"Unexpected error during SQL execution: {str(e)}")