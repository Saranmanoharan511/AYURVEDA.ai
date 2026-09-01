"""
Analytics Tool Service

PostgreSQL aggregation queries for monthly metrics and trends.
This tool provides business intelligence and analytics capabilities.
"""

import time
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, and_, case, literal_column
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.consultation import Consultation
from app.models.patient import Patient
from app.models.consultation_note import ConsultationNote
from app.schemas.ai import AnalyticsToolRequest, AnalyticsToolResponse


class AnalyticsTool:
    """
    Analytics Tool for business intelligence and metrics.
    
    This tool calculates various analytics metrics from structured
    PostgreSQL data to help the doctor understand practice trends.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_metrics(self, request: AnalyticsToolRequest) -> AnalyticsToolResponse:
        """
        Calculate analytics metrics based on the request type.
        
        Args:
            request: AnalyticsToolRequest with metric type and parameters
            
        Returns:
            AnalyticsToolResponse with calculated metrics
        """
        start_time = time.time()
        
        try:
            if request.metric_type == "monthly_consultations":
                results, summary = self._get_monthly_consultations(request)
            elif request.metric_type == "common_conditions":
                results, summary = self._get_common_conditions(request)
            elif request.metric_type == "treatment_trends":
                results, summary = self._get_treatment_trends(request)
            elif request.metric_type == "returning_patients":
                results, summary = self._get_returning_patients(request)
            elif request.metric_type == "city_distribution":
                results, summary = self._get_city_distribution(request)
            elif request.metric_type == "follow_up_counts":
                results, summary = self._get_follow_up_counts(request)
            else:
                raise ValueError(f"Unknown metric type: {request.metric_type}")
            
            calculation_time = (time.time() - start_time) * 1000
            
            return AnalyticsToolResponse(
                metric_type=request.metric_type,
                results=results,
                summary=summary,
                calculation_time_ms=calculation_time
            )
            
        except Exception as e:
            calculation_time = (time.time() - start_time) * 1000
            raise Exception(f"Analytics Tool calculation failed: {str(e)}")
    
    def _get_monthly_consultations(self, request: AnalyticsToolRequest) -> tuple:
        """Get monthly consultation statistics."""
        months_back = request.date_range.get('months_back', 6) if request.date_range else 6
        
        query = select(
            func.date_trunc('month', Consultation.created_at).label('month'),
            func.count(Consultation.id).label('total_consultations'),
            func.count(
                case(
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
        
        formatted_results = [
            {
                "month": str(row.month),
                "total_consultations": row.total_consultations,
                "completed_consultations": row.completed_consultations,
                "completion_rate": round(row.completed_consultations / row.total_consultations * 100, 2) if row.total_consultations > 0 else 0
            }
            for row in results
        ]
        
        summary = {
            "total_consultations": sum(r['total_consultations'] for r in formatted_results),
            "total_completed": sum(r['completed_consultations'] for r in formatted_results),
            "average_completion_rate": round(
                sum(r['completion_rate'] for r in formatted_results) / len(formatted_results), 2
            ) if formatted_results else 0
        }
        
        return formatted_results, summary
    
    def _get_common_conditions(self, request: AnalyticsToolRequest) -> tuple:
        """Get most common consultation reasons/conditions."""
        query = select(
            Consultation.reason,
            func.count(Consultation.id).label('count')
        )
        
        if request.doctor_id:
            query = query.where(Consultation.doctor_id == request.doctor_id)
        
        if request.date_range:
            start_date = request.date_range.get('start_date')
            end_date = request.date_range.get('end_date')
            if start_date:
                query = query.where(Consultation.created_at >= datetime.fromisoformat(start_date))
            if end_date:
                query = query.where(Consultation.created_at <= datetime.fromisoformat(end_date))
        
        query = query.group_by(Consultation.reason).order_by(
            func.count(Consultation.id).desc()
        ).limit(request.limit)
        
        results = self.db.execute(query).all()
        
        formatted_results = [
            {
                "condition": row.reason,
                "count": row.count
            }
            for row in results
        ]
        
        summary = {
            "total_conditions": len(formatted_results),
            "top_condition": formatted_results[0]['condition'] if formatted_results else None,
            "top_condition_count": formatted_results[0]['count'] if formatted_results else 0
        }
        
        return formatted_results, summary
    
    def _get_treatment_trends(self, request: AnalyticsToolRequest) -> tuple:
        """Get treatment trends from consultation notes."""
        query = select(
            func.date_trunc('month', ConsultationNote.created_at).label('month'),
            func.count(ConsultationNote.id).label('total_notes')
        )
        
        if request.doctor_id:
            query = query.where(ConsultationNote.doctor_id == request.doctor_id)
        
        if request.date_range:
            start_date = request.date_range.get('start_date')
            end_date = request.date_range.get('end_date')
            if start_date:
                query = query.where(ConsultationNote.created_at >= datetime.fromisoformat(start_date))
            if end_date:
                query = query.where(ConsultationNote.created_at <= datetime.fromisoformat(end_date))
        
        query = query.group_by(
            func.date_trunc('month', ConsultationNote.created_at)
        ).order_by(
            func.date_trunc('month', ConsultationNote.created_at)
        )
        
        results = self.db.execute(query).all()
        
        formatted_results = [
            {
                "month": str(row.month),
                "notes_count": row.total_notes
            }
            for row in results
        ]
        
        summary = {
            "total_notes": sum(r['notes_count'] for r in formatted_results),
            "average_notes_per_month": round(
                sum(r['notes_count'] for r in formatted_results) / len(formatted_results), 2
            ) if formatted_results else 0
        }
        
        return formatted_results, summary
    
    def _get_returning_patients(self, request: AnalyticsToolRequest) -> tuple:
        """Get returning patient statistics."""
        # Patients with more than 1 consultation
        subquery = select(
            Consultation.patient_id,
            func.count(Consultation.id).label('consultation_count')
        ).group_by(Consultation.patient_id).having(
            func.count(Consultation.id) > 1
        ).subquery()
        
        query = select(
            Patient.client_id,
            Patient.full_name,
            subquery.c.consultation_count
        ).join(
            subquery, Patient.id == subquery.c.patient_id
        )
        
        if request.doctor_id:
            query = query.join(
                Consultation, Patient.id == Consultation.patient_id
            ).where(Consultation.doctor_id == request.doctor_id)
        
        query = query.order_by(subquery.c.consultation_count.desc()).limit(request.limit)
        
        results = self.db.execute(query).all()
        
        formatted_results = [
            {
                "client_id": row.client_id,
                "patient_name": row.full_name,
                "consultation_count": row.consultation_count
            }
            for row in results
        ]
        
        summary = {
            "total_returning_patients": len(formatted_results),
            "highest_consultation_count": formatted_results[0]['consultation_count'] if formatted_results else 0
        }
        
        return formatted_results, summary
    
    def _get_city_distribution(self, request: AnalyticsToolRequest) -> tuple:
        """Get patient distribution by city."""
        query = select(
            Patient.city,
            func.count(Patient.id).label('patient_count')
        )
        
        if request.doctor_id:
            query = query.join(
                Consultation, Patient.id == Consultation.patient_id
            ).where(Consultation.doctor_id == request.doctor_id)
        
        query = query.where(Patient.city.isnot(None)).group_by(Patient.city).order_by(
            func.count(Patient.id).desc()
        ).limit(request.limit)
        
        results = self.db.execute(query).all()
        
        formatted_results = [
            {
                "city": row.city,
                "patient_count": row.patient_count
            }
            for row in results
        ]
        
        summary = {
            "total_cities": len(formatted_results),
            "top_city": formatted_results[0]['city'] if formatted_results else None,
            "top_city_count": formatted_results[0]['patient_count'] if formatted_results else 0
        }
        
        return formatted_results, summary
    
    def _get_follow_up_counts(self, request: AnalyticsToolRequest) -> tuple:
        """Get follow-up instruction statistics."""
        query = select(
            func.date_trunc('month', ConsultationNote.created_at).label('month'),
            func.count(ConsultationNote.id).label('total_notes'),
            func.count(
                case(
                    (ConsultationNote.follow_up_instructions.isnot(None), 1),
                    else_=0
                )
            ).label('notes_with_follow_up')
        )
        
        if request.doctor_id:
            query = query.where(ConsultationNote.doctor_id == request.doctor_id)
        
        if request.date_range:
            start_date = request.date_range.get('start_date')
            end_date = request.date_range.get('end_date')
            if start_date:
                query = query.where(ConsultationNote.created_at >= datetime.fromisoformat(start_date))
            if end_date:
                query = query.where(ConsultationNote.created_at <= datetime.fromisoformat(end_date))
        
        query = query.group_by(
            func.date_trunc('month', ConsultationNote.created_at)
        ).order_by(
            func.date_trunc('month', ConsultationNote.created_at)
        )
        
        results = self.db.execute(query).all()
        
        formatted_results = [
            {
                "month": str(row.month),
                "total_notes": row.total_notes,
                "notes_with_follow_up": row.notes_with_follow_up,
                "follow_up_rate": round(row.notes_with_follow_up / row.total_notes * 100, 2) if row.total_notes > 0 else 0
            }
            for row in results
        ]
        
        summary = {
            "total_notes": sum(r['total_notes'] for r in formatted_results),
            "total_with_follow_up": sum(r['notes_with_follow_up'] for r in formatted_results),
            "average_follow_up_rate": round(
                sum(r['follow_up_rate'] for r in formatted_results) / len(formatted_results), 2
            ) if formatted_results else 0
        }
        
        return formatted_results, summary
    
    def format_metrics_for_ai(self, response: AnalyticsToolResponse) -> str:
        """
        Format analytics metrics as a readable string for AI consumption.
        
        Args:
            response: AnalyticsToolResponse
            
        Returns:
            Formatted metrics string
        """
        lines = [f"Analytics: {response.metric_type}\n"]
        
        if response.summary:
            lines.append("Summary:")
            for key, value in response.summary.items():
                lines.append(f"  {key}: {value}")
            lines.append("")
        
        if response.results:
            lines.append("Results:")
            for i, result in enumerate(response.results[:10], 1):
                lines.append(f"  {i}. {result}")
            if len(response.results) > 10:
                lines.append(f"  ... and {len(response.results) - 10} more results")
        
        return "\n".join(lines)
