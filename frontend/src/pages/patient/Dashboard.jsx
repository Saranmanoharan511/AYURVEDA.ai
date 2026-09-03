import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../services/api';

function PatientDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [consultations, setConsultations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [profileData, setProfileData] = useState({});
  const [showConsultationModal, setShowConsultationModal] = useState(false);
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [consultationDetails, setConsultationDetails] = useState(null);
  const [activeTab, setActiveTab] = useState('reports');
  const [reports, setReports] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [patientUploads, setPatientUploads] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);

  useEffect(() => {
    fetchPatientData();
  }, []);

  const fetchPatientData = async () => {
    try {
      setLoading(true);
      // Fetch patient profile
      const patientResponse = await apiClient.get('/api/v1/clinical/patients/me');
      setPatient(patientResponse.data);
      setProfileData(patientResponse.data);

      // Fetch consultations
      const consultationsResponse = await apiClient.get('/api/v1/clinical/patients/me/consultations');
      setConsultations(consultationsResponse.data);
    } catch (err) {
      setError('Failed to load patient data');
      console.error('Error fetching patient data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    try {
      await apiClient.put('/api/v1/clinical/patients/me', profileData);
      setPatient(profileData);
      setShowProfileModal(false);
      alert('Profile updated successfully');
    } catch (err) {
      alert('Failed to update profile');
      console.error('Error updating profile:', err);
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-teal-50 to-cyan-100 flex items-center justify-center">
        <div className="text-teal-800">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-teal-50 to-cyan-100 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 text-red-600">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 to-cyan-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-teal-800">
                Welcome, {patient?.full_name || 'Patient'}
              </h1>
              <p className="text-gray-600 mt-1">Client ID: {patient?.client_id || 'N/A'}</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => navigate('/patient/upload-document')}
                className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg transition"
              >
                Upload Document
              </button>
              <button
                onClick={() => setShowProfileModal(true)}
                className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg transition"
              >
                Edit Profile
              </button>
            </div>
          </div>
        </div>

        {/* Profile Card */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-teal-800 mb-4">Profile Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Full Name</p>
              <p className="font-medium">{patient?.full_name || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Email</p>
              <p className="font-medium">{patient?.email || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Phone</p>
              <p className="font-medium">{patient?.phone || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Date of Birth</p>
              <p className="font-medium">{formatDate(patient?.date_of_birth)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Gender</p>
              <p className="font-medium">{patient?.gender || 'N/A'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Location</p>
              <p className="font-medium">{patient?.city && patient?.state ? `${patient.city}, ${patient.state}` : 'N/A'}</p>
            </div>
          </div>
        </div>

        {/* Consultations */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-teal-800">Consultation History</h2>
            <button
              onClick={() => navigate('/patient/book-consultation')}
              className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg transition font-medium"
            >
              + Book Consultation
            </button>
          </div>
          {consultations.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600 mb-4">No consultations yet.</p>
              <button
                onClick={() => navigate('/patient/book-consultation')}
                className="bg-teal-600 hover:bg-teal-700 text-white px-6 py-3 rounded-lg transition font-medium"
              >
                Book Your First Consultation
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {consultations.map((consultation) => (
                <div 
                  key={consultation.id} 
                  className="border rounded-lg p-4 hover:shadow-md transition cursor-pointer"
                  onClick={() => handleConsultationClick(consultation)}
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-semibold text-gray-800">{consultation.reason}</h3>
                      <p className="text-sm text-gray-600">
                        Booked on {formatDate(consultation.created_at)}
                      </p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(consultation.consultation_status)}`}>
                      {consultation.consultation_status.replace(/_/g, ' ')}
                    </span>
                  </div>
                  {consultation.description && (
                    <p className="text-sm text-gray-600 mt-2">{consultation.description}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Profile Modal */}
        {showProfileModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-md mx-4">
              <h2 className="text-2xl font-bold text-teal-800 mb-6">Edit Profile</h2>
              <form onSubmit={handleProfileUpdate}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                    <input
                      type="text"
                      value={profileData.full_name || ''}
                      onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                    <input
                      type="email"
                      value={profileData.email || ''}
                      onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                    <input
                      type="tel"
                      value={profileData.phone || ''}
                      onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
                    <input
                      type="date"
                      value={profileData.date_of_birth || ''}
                      onChange={(e) => setProfileData({ ...profileData, date_of_birth: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                    <select
                      value={profileData.gender || ''}
                      onChange={(e) => setProfileData({ ...profileData, gender: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    >
                      <option value="">Select Gender</option>
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                    <input
                      type="text"
                      value={profileData.city || ''}
                      onChange={(e) => setProfileData({ ...profileData, city: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                    <input
                      type="text"
                      value={profileData.state || ''}
                      onChange={(e) => setProfileData({ ...profileData, state: e.target.value })}
                      className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-4 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowProfileModal(false)}
                    className="px-4 py-2 border rounded-lg hover:bg-gray-50 transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition"
                  >
                    Save Changes
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
                <h2 className="text-2xl font-bold text-teal-800">Consultation Details</h2>
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

              {/* Tab Navigation */}
              <div className="flex space-x-4 mb-6 border-b">
                <button
                  onClick={() => setActiveTab('reports')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'reports'
                      ? 'text-teal-600 border-b-2 border-teal-600'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  Reports
                </button>
                <button
                  onClick={() => setActiveTab('prescriptions')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'prescriptions'
                      ? 'text-teal-600 border-b-2 border-teal-600'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  Prescriptions
                </button>
                <button
                  onClick={() => setActiveTab('patient-uploads')}
                  className={`px-4 py-2 font-medium ${
                    activeTab === 'patient-uploads'
                      ? 'text-teal-600 border-b-2 border-teal-600'
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
                                  className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg transition text-sm"
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
                                className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg transition text-sm"
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
                                  className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg transition text-sm"
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

export default PatientDashboard;
