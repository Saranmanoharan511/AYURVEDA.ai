"""
Load Testing Configuration for Ayurveda-AI Backend

This file defines load tests using Locust to simulate user traffic.
These tests are designed to measure performance under load for:
- API endpoints
- Database queries
- AI orchestration
- Document operations

Note: These tests are designed to run against a local or staging environment.
They should NOT be run against production without proper authorization.

Usage:
    locust -f locustfile.py --host=http://localhost:8000

Or in headless mode:
    locust -f locustfile.py --headless --host=http://localhost:8000 --users=100 --spawn-rate=10 --run-time=5m
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import random
import uuid
from datetime import datetime, timedelta


class AyurvedaUser(HttpUser):
    """
    Simulates a typical Ayurveda-AI user.
    
    This user performs various operations like:
    - Health checks
    - Patient data retrieval
    - Consultation queries
    - AI chat interactions
    - Document operations
    """
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Called when a user starts."""
        # Perform initial setup
        self.client.get("/api/v1/health")
    
    @task(10)
    def health_check(self):
        """Perform health check (high frequency)."""
        self.client.get("/api/v1/health")
    
    @task(5)
    def ai_health_check(self):
        """Check AI service health."""
        self.client.get("/api/v1/ai/health")
    
    @task(3)
    def get_patients(self):
        """Retrieve patient list (doctor/admin operation)."""
        # This would require authentication in real scenario
        # For load testing, we measure endpoint response time
        self.client.get("/api/v1/clinical/patients")
    
    @task(2)
    def get_consultations(self):
        """Retrieve consultation list."""
        self.client.get("/api/v1/clinical/consultations")
    
    @task(2)
    def get_appointments(self):
        """Retrieve appointment list."""
        self.client.get("/api/v1/clinical/appointments")
    
    @task(1)
    def ai_chat_query(self):
        """Simulate AI chat query."""
        query = random.choice([
            "How many patients do I have?",
            "Show me today's consultations",
            "What was the previous diagnosis?",
            "Summarize the consultation notes",
            "What medicines were prescribed?"
        ])
        
        self.client.post(
            "/api/v1/ai/chat",
            json={
                "message": query,
                "patient_id": str(uuid.uuid4()),
                "consultation_id": str(uuid.uuid4())
            }
        )
    
    @task(1)
    def get_analytics(self):
        """Retrieve analytics data."""
        self.client.get("/api/v1/analytics/monthly-consultations")
    
    @task(1)
    def get_reports(self):
        """Retrieve reports list."""
        self.client.get("/api/v1/documents/reports")


class DoctorUser(HttpUser):
    """
    Simulates a doctor user.
    
    This user performs doctor-specific operations:
    - Patient management
    - Consultation management
    - Report generation
    - AI assistance
    """
    
    wait_time = between(2, 8)
    
    @task(5)
    def get_my_patients(self):
        """Get doctor's assigned patients."""
        self.client.get("/api/v1/clinical/doctors/me/patients")
    
    @task(4)
    def get_my_consultations(self):
        """Get doctor's consultations."""
        self.client.get("/api/v1/clinical/doctors/me/consultations")
    
    @task(3)
    def create_consultation(self):
        """Create a new consultation."""
        self.client.post(
            "/api/v1/clinical/consultations",
            json={
                "patient_id": str(uuid.uuid4()),
                "reason": "Skin allergy",
                "description": "Patient has skin rash"
            }
        )
    
    @task(2)
    def update_consultation_status(self):
        """Update consultation status."""
        consultation_id = str(uuid.uuid4())
        self.client.patch(
            f"/api/v1/clinical/consultations/{consultation_id}/status",
            json={"status": "CONSULTATION_COMPLETED"}
        )
    
    @task(2)
    def add_consultation_notes(self):
        """Add consultation notes."""
        consultation_id = str(uuid.uuid4())
        self.client.post(
            f"/api/v1/clinical/consultations/{consultation_id}/notes",
            json={
                "diagnosis": "Skin allergy",
                "ayurvedic_assessment": "Vata imbalance",
                "medicines": "Ashwagandha",
                "lifestyle_advice": "Avoid spicy food"
            }
        )
    
    @task(1)
    def request_upload_url(self):
        """Request document upload URL."""
        self.client.post(
            "/api/v1/documents/upload-url",
            json={
                "filename": f"report_{uuid.uuid4()}.pdf",
                "content_type": "application/pdf",
                "document_type": "medical_report"
            }
        )


class PatientUser(HttpUser):
    """
    Simulates a patient user.
    
    This user performs patient-specific operations:
    - View own profile
    - View consultations
    - View reports
    - AI chat
    """
    
    wait_time = between(3, 10)
    
    @task(5)
    def get_my_profile(self):
        """Get patient profile."""
        self.client.get("/api/v1/clinical/patients/me")
    
    @task(4)
    def get_my_consultations(self):
        """Get patient's consultations."""
        self.client.get("/api/v1/clinical/patients/me/consultations")
    
    @task(3)
    def get_my_appointments(self):
        """Get patient's appointments."""
        self.client.get("/api/v1/clinical/patients/me/appointments")
    
    @task(3)
    def get_my_reports(self):
        """Get patient's reports."""
        self.client.get("/api/v1/clinical/patients/me/reports")
    
    @task(2)
    def request_download_url(self):
        """Request document download URL."""
        self.client.post(
            "/api/v1/documents/download-url",
            json={
                "object_key": f"patients/{uuid.uuid4()}/documents/report.pdf"
            }
        )
    
    @task(2)
    def ai_chat_query(self):
        """Ask AI assistant."""
        query = random.choice([
            "What was my previous diagnosis?",
            "Show me my consultation history",
            "What medicines were prescribed?",
            "When is my next appointment?"
        ])
        
        self.client.post(
            "/api/v1/ai/chat",
            json={
                "message": query,
                "patient_id": str(uuid.uuid4()),
                "consultation_id": str(uuid.uuid4())
            }
        )


class AdminUser(HttpUser):
    """
    Simulates an admin user.
    
    This user performs admin-specific operations:
    - User management
    - System configuration
    - Analytics
    - Audit logs
    """
    
    wait_time = between(5, 15)
    
    @task(3)
    def get_all_users(self):
        """Get all users."""
        self.client.get("/api/v1/admin/users")
    
    @task(2)
    def get_all_doctors(self):
        """Get all doctors."""
        self.client.get("/api/v1/admin/doctors")
    
    @task(2)
    def get_system_analytics(self):
        """Get system analytics."""
        self.client.get("/api/v1/analytics/system")
    
    @task(1)
    def get_audit_logs(self):
        """Get audit logs."""
        self.client.get("/api/v1/admin/audit-logs")
    
    @task(1)
    def get_system_config(self):
        """Get system configuration."""
        self.client.get("/api/v1/admin/config")


# Event handlers for custom reporting

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Custom event handler for request events.
    Can be used for custom logging or metrics.
    """
    if exception:
        print(f"Request failed: {name} - {exception}")
    else:
        print(f"Request succeeded: {name} - {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the load test starts."""
    print("=" * 50)
    print("Load Test Starting")
    print("=" * 50)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print(f"Spawn Rate: {environment.runner.spawn_rate if hasattr(environment.runner, 'spawn_rate') else 'N/A'}")
    print("=" * 50)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the load test stops."""
    print("=" * 50)
    print("Load Test Completed")
    print("=" * 50)
    
    if isinstance(environment.runner, MasterRunner):
        print("Master runner statistics:")
    else:
        print("Statistics:")
        print(f"Total requests: {environment.stats.total.num_requests}")
        print(f"Total failures: {environment.stats.total.num_failures}")
        print(f"Failure rate: {environment.stats.total.fail_ratio * 100:.2f}%")
        print(f"Median response time: {environment.stats.total.median_response_time}ms")
        print(f"95th percentile: {environment.stats.total.get_response_time_percentile(0.95)}ms")
        print(f"99th percentile: {environment.stats.total.get_response_time_percentile(0.99)}ms")
    print("=" * 50)


# Load test scenarios

def run_light_load_test():
    """
    Run a light load test for development.
    
    10 users, spawn rate 1 per second, run for 2 minutes.
    """
    import subprocess
    subprocess.run([
        "locust",
        "-f", __file__,
        "--headless",
        "--host=http://localhost:8000",
        "--users=10",
        "--spawn-rate=1",
        "--run-time=2m"
    ])


def run_medium_load_test():
    """
    Run a medium load test for staging.
    
    50 users, spawn rate 5 per second, run for 5 minutes.
    """
    import subprocess
    subprocess.run([
        "locust",
        "-f", __file__,
        "--headless",
        "--host=http://localhost:8000",
        "--users=50",
        "--spawn-rate=5",
        "--run-time=5m"
    ])


def run_heavy_load_test():
    """
    Run a heavy load test for production simulation.
    
    200 users, spawn rate 20 per second, run for 10 minutes.
    """
    import subprocess
    subprocess.run([
        "locust",
        "-f", __file__,
        "--headless",
        "--host=http://localhost:8000",
        "--users=200",
        "--spawn-rate=20",
        "--run-time=10m"
    ])


if __name__ == "__main__":
    print("Ayurveda-AI Load Testing Configuration")
    print("=" * 50)
    print("Available test scenarios:")
    print("1. Light load test: 10 users, 2 minutes")
    print("2. Medium load test: 50 users, 5 minutes")
    print("3. Heavy load test: 200 users, 10 minutes")
    print("=" * 50)
    print("\nTo run interactively:")
    print("  locust -f locustfile.py --host=http://localhost:8000")
    print("\nTo run headless:")
    print("  locust -f locustfile.py --headless --host=http://localhost:8000 --users=10 --spawn-rate=1 --run-time=2m")
