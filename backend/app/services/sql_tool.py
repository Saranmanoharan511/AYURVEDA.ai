"""
SQL Tool Service

Safe, read-only SQL queries for structured PostgreSQL data.
This tool allows the AI to query business data without destructive operations.
Now supports both predefined queries and LLM-generated dynamic SQL queries.
"""

import time
import re
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
        
        # Database schema information for LLM context
        self.schema_info = self._get_schema_info()
    
    def _get_schema_info(self) -> str:
        """
        Get database schema information for LLM context.
        
        Returns:
            String representation of database schema
        """
        schema = """
DATABASE SCHEMA:

Table: patients
- id (UUID, primary key)
- client_id (String, e.g., 'AYU-000001')
- user_id (UUID, foreign key to users)
- cognito_sub (String)
- full_name (String)
- date_of_birth (Date)
- age (Integer)
- gender (String)
- phone (String)
- email (String)
- city (String)
- state (String)
- created_at (DateTime)
- updated_at (DateTime)

Table: doctors
- id (UUID, primary key)
- user_id (UUID, foreign key to users)
- cognito_sub (String)
- name (String)
- qualifications (Text)
- specialization (String)
- status (String)
- created_at (DateTime)
- updated_at (DateTime)

Table: consultations
- id (UUID, primary key)
- patient_id (UUID, foreign key to patients)
- doctor_id (UUID, foreign key to doctors)
- reason (String)
- description (Text)
- consultation_status (String) - values: 'APPOINTMENT_BOOKED', 'WAITING_FOR_MEETING_SCHEDULE', 'MEETING_SCHEDULED', 'WAITING_FOR_CONSULTATION', 'CONSULTATION_COMPLETED', 'WAITING_FOR_DOCTOR_REPORT', 'REPORT_UPLOADED', 'REPORT_SENT', 'CONSULTATION_CLOSED'
- started_at (DateTime)
- completed_at (DateTime)
- created_at (DateTime)
- updated_at (DateTime)

Table: appointments
- id (UUID, primary key)
- consultation_id (UUID, foreign key to consultations)
- scheduled_date (Date)
- scheduled_time (Time)
- timezone (String)
- zoom_meeting_url (String)
- status (String)
- created_at (DateTime)
- updated_at (DateTime)

Table: consultation_notes
- id (UUID, primary key)
- consultation_id (UUID, foreign key to consultations)
- doctor_notes (Text)
- patient_summary (Text)
- created_at (DateTime)
- updated_at (DateTime)

IMPORTANT RELATIONSHIPS:
- patients.user_id -> users.id
- doctors.user_id -> users.id
- consultations.patient_id -> patients.id
- consultations.doctor_id -> doctors.id
- appointments.consultation_id -> consultations.id
- consultation_notes.consultation_id -> consultations.id
"""
        return schema
    
    def execute_query(self, request: SQLToolRequest) -> SQLToolResponse:
        """
        Execute a safe SQL query based on the request type.
        
        Args:
            request: SQLToolRequest with query type and parameters
            
        Returns:
            SQLToolResponse with query results
        """
        start_time = time.time()
        
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
                # New LLM-generated SQL query
                results = self._execute_llm_generated_query(request)
            else:
                raise ValueError(f"Unknown query type: {request.query_type}")
            
            execution_time = (time.time() - start_time) * 1000
            
            return SQLToolResponse(
                query_type=request.query_type,
                results=results,
                row_count=len(results),
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            raise Exception(f"SQL Tool execution failed: {str(e)}")
    
    def _get_patient_count(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        """Get patient count with optional filters."""
        query = select(func.count(Patient.id))
        
        if request.doctor_id:
            # Count patients that have consultations with this doctor
            query = select(func.count(Patient.id.distinct())).join(
                Consultation, Patient.id == Consultation.patient_id
            ).where(Consultation.doctor_id == request.doctor_id)
        
        result = self.db.execute(query).scalar()
        return [{"count": result}]
    
    def _get_consultation_status(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        """Get consultation status breakdown."""
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
        return [
            {
                "status": row.consultation_status,
                "count": row.count
            }
            for row in results
        ]
    
    def _get_appointment_status(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        """Get appointment status breakdown."""
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
        return [
            {
                "status": row.status,
                "count": row.count
            }
            for row in results
        ]
    
    def _get_today_consultations(self, request: SQLToolRequest) -> List[Dict[str, Any]]:
        """Get consultations scheduled for today."""
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
        """Get monthly consultation statistics."""
        # Default to last 6 months
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
        """Search for patients by name, client_id, or email."""
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
        
        # Search by name, client_id, or email
        search_pattern = f"%{search_term}%"
        query = query.where(
            or_(
                Patient.full_name.ilike(search_pattern),
                Patient.client_id.ilike(search_pattern),
                Patient.email.ilike(search_pattern)
            )
        )
        
        # Limit results
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
        """
        Get patient information by client ID.
        
        Args:
            client_id: Public client ID (e.g., AYU-000001)
            
        Returns:
            Patient information dictionary or None
        """
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
        """
        Get consultation history for a patient.
        
        Args:
            patient_id: Patient internal ID
            doctor_id: Optional doctor ID for authorization
            
        Returns:
            List of consultation dictionaries
        """
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
        """
        Execute an LLM-generated SQL query with safety validation.
        
        Args:
            request: SQLToolRequest with user query in filters
            
        Returns:
            List of dictionaries with query results
        """
        user_query = request.filters.get('user_query', '') if request.filters else ''
        
        if not user_query:
            raise ValueError("User query is required for LLM-generated SQL")
        
        # Generate SQL using LLM
        generated_sql = self._generate_sql_with_llm(user_query, request)
        
        # Validate the generated SQL for safety
        if not self._validate_sql_safety(generated_sql):
            raise ValueError("Generated SQL failed safety validation")
        
        # Execute the validated SQL
        return self._execute_safe_sql(generated_sql, request)
    
    def _generate_sql_with_llm(self, user_query: str, request: SQLToolRequest) -> str:
        """
        Generate SQL query using LLM based on user question.
        
        Args:
            user_query: Natural language question from user
            request: SQLToolRequest with context
            
        Returns:
            Generated SQL query string
        """
        if not self.bedrock_service.is_available():
            raise Exception("Bedrock service is not available for SQL generation")
        
        # Build context for the LLM
        context = f"""
You are a SQL expert for an Ayurveda medical database. Generate a SQL query to answer the user's question.

DATABASE SCHEMA:
{self.schema_info}

USER QUESTION: {user_query}

CONTEXT:
- Doctor ID: {request.doctor_id if request.doctor_id else 'Not specified'}
- Patient ID: {request.patient_id if request.patient_id else 'Not specified'}

IMPORTANT RULES:
1. Generate ONLY SELECT queries - no INSERT, UPDATE, DELETE, DROP, TRUNCATE, etc.
2. Always include appropriate WHERE clauses for authorization:
   - If doctor_id is provided, filter by that doctor_id
   - If patient_id is provided, filter by that patient_id
3. Use proper JOIN syntax when accessing related tables
4. Return only the SQL query, no explanations
5. Use PostgreSQL syntax
6. Limit results to avoid excessive data (use LIMIT 100)
7. Handle dates properly (use proper date functions)
8. Use proper column names from the schema above

Generate the SQL query:
"""
        
        from app.schemas.ai import BedrockRequest
        
        bedrock_request = BedrockRequest(
            prompt=context,
            model_id=self.bedrock_service.model_id,
            max_tokens=500,
            temperature=0.1,  # Low temperature for consistent SQL generation
            system_prompt="You are a SQL expert. Generate only SQL queries, no explanations."
        )
        
        try:
            response = self.bedrock_service.invoke_model(bedrock_request)
            
            # Extract SQL from response
            sql_query = response.text.strip()
            
            # Clean up the SQL - remove markdown code blocks if present
            sql_query = re.sub(r'```sql\s*', '', sql_query)
            sql_query = re.sub(r'```\s*', '', sql_query)
            sql_query = sql_query.strip()
            
            if not sql_query.lower().startswith('select'):
                raise ValueError("LLM did not generate a SELECT query")
            
            return sql_query
            
        except Exception as e:
            raise Exception(f"Failed to generate SQL with LLM: {str(e)}")
    
    def _validate_sql_safety(self, sql_query: str) -> bool:
        """
        Validate that the SQL query is safe to execute.
        
        Args:
            sql_query: SQL query string to validate
            
        Returns:
            True if safe, False otherwise
        """
        sql_lower = sql_query.lower()
        
        # Block dangerous keywords
        dangerous_keywords = [
            'drop', 'delete', 'truncate', 'insert', 'update', 
            'alter', 'create', 'grant', 'revoke', 'exec',
            'execute', 'script', 'javascript', '--', '/*', '*/'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_lower:
                return False
        
        # Must start with SELECT
        if not sql_lower.strip().startswith('select'):
            return False
        
        # Check for multiple statements (semicolon separation)
        if ';' in sql_query[:-1]:  # Allow single trailing semicolon
            return False
        
        # Check for function calls that might be dangerous
        dangerous_functions = [
            'eval(', 'exec(', 'system(', 'shell('
        ]
        
        for func in dangerous_functions:
            if func in sql_lower:
                return False
        
        return True
    
    def _execute_safe_sql(self, sql_query: str, request: SQLToolRequest) -> List[Dict[str, Any]]:
        """
        Execute a validated SQL query safely.
        
        Args:
            sql_query: Validated SQL query string
            request: SQLToolRequest with context
            
        Returns:
            List of dictionaries with query results
        """
        try:
            # Execute the query using SQLAlchemy text() for safety
            result = self.db.execute(text(sql_query))
            
            # Fetch all results
            rows = result.fetchall()
            
            # Get column names from result
            if rows:
                column_names = list(result.keys())
                results = [
                    {column_names[i]: str(row[i]) if row[i] is not None else None 
                     for i in range(len(column_names))}
                    for row in rows
                ]
            else:
                results = []
            
            return results
            
        except SQLAlchemyError as e:
            raise Exception(f"SQL execution failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error during SQL execution: {str(e)}")
