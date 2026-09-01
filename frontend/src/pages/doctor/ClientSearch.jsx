import { useState } from 'react';
import apiClient from '../../services/api';

function ClientSearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [showPatientDetail, setShowPatientDetail] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);

    try {
      // For now, we'll search by client_id or name
      // In a real implementation, this would be a dedicated search endpoint
      const response = await apiClient.get('/api/v1/clinical/patients');
      const allPatients = response.data;
      
      // Filter patients based on search query
      const filteredPatients = allPatients.filter(patient =>
        patient.client_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        patient.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        patient.email.toLowerCase().includes(searchQuery.toLowerCase())
      );
      
      setPatients(filteredPatients);
    } catch (err) {
      setError('Failed to search patients');
      console.error('Error searching patients:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewPatient = async (patient) => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/api/v1/clinical/patients/${patient.id}/consultations`);
      setSelectedPatient({
        ...patient,
        consultations: response.data.consultations || []
      });
      setShowPatientDetail(true);
    } catch (err) {
      setError('Failed to load patient details');
      console.error('Error loading patient details:', err);
    } finally {
      setLoading(false);
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-violet-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h1 className="text-3xl font-bold text-blue-800 mb-2">Client Search</h1>
          <p className="text-gray-600">Search for patients by name, client ID, or email</p>
        </div>

        {/* Search Form */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <form onSubmit={handleSearch} className="flex space-x-4">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Search by name, client ID, or email..."
            />
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Search Results */}
        {patients.length > 0 && !showPatientDetail && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold text-blue-800 mb-4">Search Results ({patients.length})</h2>
            <div className="space-y-4">
              {patients.map((patient) => (
                <div key={patient.id} className="border rounded-lg p-4 hover:shadow-md transition">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-800">{patient.full_name}</h3>
                      <p className="text-sm text-gray-600">Client ID: {patient.client_id}</p>
                      <p className="text-sm text-gray-600">Email: {patient.email}</p>
                      <p className="text-sm text-gray-600">
                        {patient.city && patient.state ? `${patient.city}, ${patient.state}` : 'Location not specified'}
                      </p>
                    </div>
                    <button
                      onClick={() => handleViewPatient(patient)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Patient Detail Modal */}
        {showPatientDetail && selectedPatient && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-4xl mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-blue-800">Patient Details</h2>
                <button
                  onClick={() => setShowPatientDetail(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>

              {/* Patient Information */}
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Personal Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Client ID</p>
                    <p className="font-medium">{selectedPatient.client_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Full Name</p>
                    <p className="font-medium">{selectedPatient.full_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Email</p>
                    <p className="font-medium">{selectedPatient.email}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Phone</p>
                    <p className="font-medium">{selectedPatient.phone || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Date of Birth</p>
                    <p className="font-medium">{formatDate(selectedPatient.date_of_birth)}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Gender</p>
                    <p className="font-medium">{selectedPatient.gender || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Location</p>
                    <p className="font-medium">
                      {selectedPatient.city && selectedPatient.state 
                        ? `${selectedPatient.city}, ${selectedPatient.state}` 
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Consultation History */}
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Consultation History</h3>
                {selectedPatient.consultations && selectedPatient.consultations.length > 0 ? (
                  <div className="space-y-4">
                    {selectedPatient.consultations.map((consultation) => (
                      <div key={consultation.id} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h4 className="font-semibold text-gray-800">{consultation.reason}</h4>
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
                ) : (
                  <p className="text-gray-600">No consultation history available.</p>
                )}
              </div>

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setShowPatientDetail(false)}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50 transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ClientSearch;
