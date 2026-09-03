import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../services/api';

function DoctorDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [consultations, setConsultations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [showNotesModal, setShowNotesModal] = useState(false);
  const [scheduleData, setScheduleData] = useState({});
  const [notesData, setNotesData] = useState({});
  const [showConsultationModal, setShowConsultationModal] = useState(false);
  const [consultationDetails, setConsultationDetails] = useState(null);
  const [activeTab, setActiveTab] = useState('reports');
  const [reports, setReports] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [patientUploads, setPatientUploads] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);

  useEffect(() => {
    fetchConsultations();
  }, [filter]);

  const fetchConsultations = async () => {
    try {
      setLoading(true);
      const statusFilter = filter === 'all' ? undefined : filter;
      const response = await apiClient.get('/api/v1/clinical/doctors/me/consultations', {
        params: statusFilter ? { status_filter: statusFilter } : {}
      });
      setConsultations(response.data);
    } catch (err) {
      setError('Failed to load consultations');
      console.error('Error fetching consultations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleScheduleMeeting = (consultation) => {
    setSelectedConsultation(consultation);
    setScheduleData({
      scheduled_date: '',
      scheduled_time: '',
      timezone: 'UTC',
      zoom_meeting_url: ''
    });
    setShowScheduleModal(true);
  };

  const handleScheduleSubmit = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post(`/api/v1/clinical/consultations/${selectedConsultation.id}/schedule-meeting`, scheduleData);
      alert('Meeting scheduled successfully!');
      setShowScheduleModal(false);
      fetchConsultations();
    } catch (err) {
      alert('Failed to schedule meeting');
      console.error('Error scheduling meeting:', err);
    }
  };

  const handleAddNotes = (consultation) => {
    setSelectedConsultation(consultation);
    setNotesData({
      diagnosis: '',
      ayurvedic_assessment: '',
      medicines: '',
      lifestyle_advice: '',
      diet_plan: '',
      follow_up_instructions: ''
    });
    setShowNotesModal(true);
  };

  const handleNotesSubmit = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post(`/api/v1/clinical/consultations/${selectedConsultation.id}/notes`, notesData);
      alert('Consultation notes saved successfully!');
      setShowNotesModal(false);
      fetchConsultations();
    } catch (err) {
      alert('Failed to save notes');
      console.error('Error saving notes:', err);
    }
  };

  const handleConsultationClick = async (consultation) => {
    setSelectedConsultation(consultation);
    setShowConsultationModal(true);
    setActiveTab('reports');
    await fetchConsultationDocuments(consultation.id);
  };

  const fetchConsultationDocuments = async (consultationId) => {
    try {
      setLoadingDocuments(true);
      const [reportsResponse, prescriptionsResponse, patientUploadsResponse] = await Promise.all([
        apiClient.get(`/api/v1/clinical/consultations/${consultationId}/reports`),
        apiClient.get(`/api/v1/clinical/consultations/${consultationId}/prescription-documents`),
        apiClient.get(`/api/v1/documents/consultation/${consultationId}/patient-uploads`)
      ]);
      setReports(reportsResponse.data);
      setPrescriptions(prescriptionsResponse.data);
      setPatientUploads(patientUploadsResponse.data);
    } catch (err) {
      console.error('Error fetching consultation documents:', err);
      alert('Failed to load documents');
    } finally {
      setLoadingDocuments(false);
    }
  };

  const handleUploadReport = (consultation) => {
    // Navigate to upload report page with consultation ID and patient ID
    navigate(`/doctor/upload-report/${consultation.id}/${consultation.patient_id}`);
  };

  const handleAddPrescription = (consultation) => {
    // Navigate to add prescription page with consultation ID
    navigate(`/doctor/add-prescription/${consultation.id}`);
  };

  const handleSendDocuments = async (consultation) => {
    try {
      const response = await apiClient.post(`/api/v1/clinical/consultations/${consultation.id}/send-documents`);
      alert(`Documents sent successfully! ${response.data.reports_count} reports and ${response.data.prescriptions_count} prescriptions attached.`);
      setShowConsultationModal(false);
    } catch (err) {
      alert('Failed to send documents: ' + (err.response?.data?.detail || err.message));
      console.error('Error sending documents:', err);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'APPOINTMENT_BOOKED': 'bg-yellow-100 text-yellow-800',
      'WAITING_FOR_MEETING_SCHEDULE': 'bg-orange-100 text-orange-800',
      'MEETING_SCHEDULED': 'bg-blue-100 text-blue-800',
      'WAITING_FOR_CONSULTATION': 'bg-purple-100 text-purple-800',
      'CONSULTATION_COMPLETED': 'bg-green-100 text-green-800',
      'WAITING_FOR_DOCTOR_REPORT': 'bg-indigo-100 text-indigo-800',
      'REPORT_UPLOADED': 'bg-teal-100 text-teal-800',
      'REPORT_SENT': 'bg-cyan-100 text-cyan-800',
      'CONSULTATION_CLOSED': 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getFilteredConsultations = () => {
    if (filter === 'all') return consultations;
    return consultations.filter(c => c.consultation_status === filter);
  };

  const waitingCount = consultations.filter(c => c.consultation_status === 'APPOINTMENT_BOOKED' || c.consultation_status === 'WAITING_FOR_MEETING_SCHEDULE').length;
  const scheduledCount = consultations.filter(c => c.consultation_status === 'MEETING_SCHEDULED' || c.consultation_status === 'WAITING_FOR_CONSULTATION').length;
  const completedCount = consultations.filter(c => c.consultation_status === 'CONSULTATION_COMPLETED' || c.consultation_status === 'CONSULTATION_CLOSED').length;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-violet-100 flex items-center justify-center">
        <div className="text-blue-800">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-violet-100 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 text-red-600">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-violet-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-blue-800 mb-2">Doctor Dashboard</h1>
              <p className="text-gray-600">Manage your consultations and patients</p>
            </div>
            <button
              onClick={() => navigate('/doctor/ai-chat')}
              className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white px-6 py-3 rounded-lg transition font-medium shadow-md"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span>AI Chat</span>
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-orange-800 mb-2">Waiting for Schedule</h3>
            <p className="text-4xl font-bold text-orange-600">{waitingCount}</p>
          </div>
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-2">Scheduled</h3>
            <p className="text-4xl font-bold text-blue-600">{scheduledCount}</p>
          </div>
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-green-800 mb-2">Completed</h3>
            <p className="text-4xl font-bold text-green-600">{completedCount}</p>
          </div>
        </div>

        {/* Consultations List */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-blue-800">Consultations</h2>
            <div className="flex space-x-2">
              <button
                onClick={() => setFilter('all')}
                className={`px-4 py-2 rounded-lg transition ${filter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
              >
                All
              </button>
              <button
                onClick={() => setFilter('APPOINTMENT_BOOKED')}
                className={`px-4 py-2 rounded-lg transition ${filter === 'APPOINTMENT_BOOKED' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
              >
                Waiting
              </button>
              <button
                onClick={() => setFilter('MEETING_SCHEDULED')}
                className={`px-4 py-2 rounded-lg transition ${filter === 'MEETING_SCHEDULED' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
              >
                Scheduled
              </button>
              <button
                onClick={() => setFilter('CONSULTATION_COMPLETED')}
                className={`px-4 py-2 rounded-lg transition ${filter === 'CONSULTATION_COMPLETED' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
              >
                Completed
              </button>
            </div>
          </div>

          {getFilteredConsultations().length === 0 ? (
            <p className="text-gray-600 text-center py-8">No consultations found.</p>
          ) : (
            <div className="space-y-4">
              {getFilteredConsultations().map((consultation) => (
                <div 
                  key={consultation.id} 
                  className="border rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                  onClick={() => handleConsultationClick(consultation)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-800">{consultation.reason}</h3>
                      <p className="text-sm text-gray-600">
                        Booked on {formatDate(consultation.created_at)}
                      </p>
                      {consultation.description && (
                        <p className="text-sm text-gray-600 mt-1">{consultation.description}</p>
                      )}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(consultation.consultation_status)}`}>
                      {consultation.consultation_status.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="flex space-x-2 mt-4" onClick={(e) => e.stopPropagation()}>
                    {(consultation.consultation_status === 'APPOINTMENT_BOOKED' || consultation.consultation_status === 'WAITING_FOR_MEETING_SCHEDULE') && (
                      <button
                        onClick={() => handleScheduleMeeting(consultation)}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm"
                      >
                        Schedule Meeting
                      </button>
                    )}
                    {(consultation.consultation_status === 'CONSULTATION_COMPLETED' || consultation.consultation_status === 'WAITING_FOR_DOCTOR_REPORT') && (
                      <button
                        onClick={() => handleAddNotes(consultation)}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm"
                      >
                        Add Notes
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Schedule Meeting Modal */}
        {showScheduleModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold text-blue-800 mb-6">Schedule Meeting</h2>
              <form onSubmit={handleScheduleSubmit}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                    <input
                      type="date"
                      value={scheduleData.scheduled_date}
                      onChange={(e) => setScheduleData({ ...scheduleData, scheduled_date: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Time</label>
                    <input
                      type="time"
                      value={scheduleData.scheduled_time}
                      onChange={(e) => setScheduleData({ ...scheduleData, scheduled_time: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
                    <select
                      value={scheduleData.timezone}
                      onChange={(e) => setScheduleData({ ...scheduleData, timezone: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="UTC">UTC</option>
                      <option value="America/New_York">Eastern Time</option>
                      <option value="America/Chicago">Central Time</option>
                      <option value="America/Denver">Mountain Time</option>
                      <option value="America/Los_Angeles">Pacific Time</option>
                      <option value="Asia/Kolkata">India Standard Time</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Zoom Meeting URL</label>
                    <input
                      type="url"
                      value={scheduleData.zoom_meeting_url}
                      onChange={(e) => setScheduleData({ ...scheduleData, zoom_meeting_url: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="https://zoom.us/j/..."
                      required
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-4 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowScheduleModal(false)}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-50 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                  >
                    Schedule
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Add Notes Modal */}
        {showNotesModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold text-green-800 mb-6">Add Consultation Notes</h2>
              <form onSubmit={handleNotesSubmit}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Diagnosis</label>
                    <textarea
                      value={notesData.diagnosis}
                      onChange={(e) => setNotesData({ ...notesData, diagnosis: e.target.value })}
                      rows={3}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Ayurvedic Assessment</label>
                    <textarea
                      value={notesData.ayurvedic_assessment}
                      onChange={(e) => setNotesData({ ...notesData, ayurvedic_assessment: e.target.value })}
                      rows={3}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Medicines</label>
                    <textarea
                      value={notesData.medicines}
                      onChange={(e) => setNotesData({ ...notesData, medicines: e.target.value })}
                      rows={3}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Lifestyle Advice</label>
                    <textarea
                      value={notesData.lifestyle_advice}
                      onChange={(e) => setNotesData({ ...notesData, lifestyle_advice: e.target.value })}
                      rows={2}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Diet Plan</label>
                    <textarea
                      value={notesData.diet_plan}
                      onChange={(e) => setNotesData({ ...notesData, diet_plan: e.target.value })}
                      rows={2}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Follow-up Instructions</label>
                    <textarea
                      value={notesData.follow_up_instructions}
                      onChange={(e) => setNotesData({ ...notesData, follow_up_instructions: e.target.value })}
                      rows={2}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-4 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowNotesModal(false)}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-50 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                  >
                    Save Notes
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Consultation Details Modal */}
        {showConsultationModal && selectedConsultation && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-blue-800">Consultation Details</h2>
                <button
                  onClick={() => setShowConsultationModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Consultation Info */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Consultation ID</p>
                    <p className="font-medium">{selectedConsultation.id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Status</p>
                    <p className="font-medium">{selectedConsultation.consultation_status.replace(/_/g, ' ')}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Reason</p>
                    <p className="font-medium">{selectedConsultation.reason}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Booked On</p>
                    <p className="font-medium">{formatDate(selectedConsultation.created_at)}</p>
                  </div>
                </div>
                {selectedConsultation.description && (
                  <div className="mt-4">
                    <p className="text-sm text-gray-600">Description</p>
                    <p className="font-medium">{selectedConsultation.description}</p>
                  </div>
                )}
              </div>

              {/* Doctor Action Buttons */}
              <div className="flex space-x-4 mb-6">
                <button
                  onClick={() => handleUploadReport(selectedConsultation)}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-lg transition font-medium"
                >
                  Upload Report
                </button>
                <button
                  onClick={() => handleAddPrescription(selectedConsultation)}
                  className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-3 rounded-lg transition font-medium"
                >
                  Add Prescription
                </button>
                <button
                  onClick={() => handleSendDocuments(selectedConsultation)}
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white px-4 py-3 rounded-lg transition font-medium"
                >
                  Send Documents
                </button>
              </div>

              {/* Tab Navigation */}
              <div className="flex space-x-4 mb-6 border-b">
                <button
                  onClick={() => setActiveTab('reports')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'reports'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  Reports
                </button>
                <button
                  onClick={() => setActiveTab('prescriptions')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'prescriptions'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  Prescriptions
                </button>
                <button
                  onClick={() => setActiveTab('patient-uploads')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'patient-uploads'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  Patient Uploads
                </button>
              </div>

              {/* Tab Content */}
              {loadingDocuments ? (
                <div className="text-center py-8">
                  <p className="text-gray-600">Loading documents...</p>
                </div>
              ) : (
                <>
                  {activeTab === 'reports' && (
                    <div>
                      {reports.length === 0 ? (
                        <p className="text-gray-600 text-center py-8">No reports uploaded yet.</p>
                      ) : (
                        <div className="space-y-3">
                          {reports.map((report) => (
                            <div key={report.id} className="border rounded-lg p-4 flex justify-between items-center">
                              <div>
                                <p className="font-medium">{report.original_filename}</p>
                                <p className="text-sm text-gray-600">{report.report_type}</p>
                              </div>
                              {report.download_url && (
                                <a
                                  href={report.download_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition text-sm"
                                >
                                  Download
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'prescriptions' && (
                    <div>
                      {prescriptions.length === 0 ? (
                        <p className="text-gray-600 text-center py-8">No prescriptions generated yet.</p>
                      ) : (
                        <div className="space-y-3">
                          {prescriptions.map((doc) => (
                            <div key={doc.id} className="border rounded-lg p-4 flex justify-between items-center">
                              <div>
                                <p className="font-medium">{doc.original_filename}</p>
                                <p className="text-sm text-gray-600">Generated on {formatDate(doc.generated_at)}</p>
                              </div>
                              <a
                                href={doc.download_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition text-sm"
                              >
                                Download
                              </a>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'patient-uploads' && (
                    <div>
                      {patientUploads.length === 0 ? (
                        <p className="text-gray-600 text-center py-8">No patient uploaded documents yet.</p>
                      ) : (
                        <div className="space-y-3">
                          {patientUploads.map((upload) => (
                            <div key={upload.id} className="border rounded-lg p-4 flex justify-between items-center">
                              <div>
                                <p className="font-medium">{upload.original_filename}</p>
                                <p className="text-sm text-gray-600">{upload.document_type}</p>
                              </div>
                              {upload.download_url && (
                                <a
                                  href={upload.download_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition text-sm"
                                >
                                  Download
                                </a>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default DoctorDashboard;
