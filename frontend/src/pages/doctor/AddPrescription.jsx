import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../services/api';

function AddPrescription() {
  const { consultationId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [consultationDetails, setConsultationDetails] = useState(null);
  const [prescriptions, setPrescriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchConsultationDetails();
    fetchExistingPrescriptions();
  }, [consultationId]);

  const fetchConsultationDetails = async () => {
    try {
      const response = await apiClient.get(`/api/v1/clinical/consultations/${consultationId}`);
      setConsultationDetails(response.data);
    } catch (err) {
      setError('Failed to load consultation details');
      console.error('Error fetching consultation details:', err);
    }
  };

  const fetchExistingPrescriptions = async () => {
    try {
      const response = await apiClient.get(`/api/v1/clinical/consultations/${consultationId}/prescriptions`);
      setPrescriptions(response.data);
      setLoading(false);
    } catch (err) {
      // If no prescriptions exist, that's fine
      setPrescriptions([]);
      setLoading(false);
    }
  };

  const addPrescription = () => {
    setPrescriptions([
      ...prescriptions,
      {
        id: null,
        name: '',
        morning_dosage: 0,
        afternoon_dosage: 0,
        night_dosage: 0,
        food_timing: 'before_food',
        notes: ''
      }
    ]);
  };

  const updatePrescription = (index, field, value) => {
    const updatedPrescriptions = [...prescriptions];
    updatedPrescriptions[index][field] = value;
    setPrescriptions(updatedPrescriptions);
  };

  const removePrescription = async (index) => {
    const prescription = prescriptions[index];
    if (prescription.id) {
      // If it's an existing prescription, delete it from backend
      try {
        await apiClient.delete(`/api/v1/clinical/prescriptions/${prescription.id}`);
      } catch (err) {
        console.error('Error deleting prescription:', err);
        alert('Failed to delete prescription');
        return;
      }
    }
    
    // Remove from local state
    const updatedPrescriptions = prescriptions.filter((_, i) => i !== index);
    setPrescriptions(updatedPrescriptions);
  };

  const savePrescription = async (index) => {
    const prescription = prescriptions[index];
    setSaving(true);

    try {
      if (prescription.id) {
        // Update existing prescription
        await apiClient.put(`/api/v1/clinical/prescriptions/${prescription.id}`, {
          name: prescription.name,
          morning_dosage: prescription.morning_dosage,
          afternoon_dosage: prescription.afternoon_dosage,
          night_dosage: prescription.night_dosage,
          food_timing: prescription.food_timing,
          notes: prescription.notes
        });
      } else {
        // Create new prescription
        const response = await apiClient.post(`/api/v1/clinical/consultations/${consultationId}/prescriptions`, {
          name: prescription.name,
          morning_dosage: prescription.morning_dosage,
          afternoon_dosage: prescription.afternoon_dosage,
          night_dosage: prescription.night_dosage,
          food_timing: prescription.food_timing,
          notes: prescription.notes
        });
        
        // Update the prescription with the returned ID
        const updatedPrescriptions = [...prescriptions];
        updatedPrescriptions[index] = { ...prescription, id: response.data.id };
        setPrescriptions(updatedPrescriptions);
      }
      alert('Prescription saved successfully');
    } catch (err) {
      alert('Failed to save prescription');
      console.error('Error saving prescription:', err);
    } finally {
      setSaving(false);
    }
  };

  const generatePrescriptionPDF = async () => {
    if (prescriptions.length === 0) {
      alert('Please add at least one prescription before generating PDF');
      return;
    }

    // Save all unsaved prescriptions first
    const unsavedPrescriptions = prescriptions.filter(p => !p.id);
    if (unsavedPrescriptions.length > 0) {
      alert('Please save all prescriptions before generating PDF');
      return;
    }

    setSaving(true);
    try {
      await apiClient.post(`/api/v1/clinical/consultations/${consultationId}/prescriptions/generate-pdf`);
      alert('Prescription PDF generated successfully');
      navigate('/doctor/dashboard');
    } catch (err) {
      alert('Failed to generate prescription PDF');
      console.error('Error generating PDF:', err);
    } finally {
      setSaving(false);
    }
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
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-3xl font-bold text-blue-800">Add Prescription</h1>
            <button
              onClick={() => navigate('/doctor/dashboard')}
              className="text-gray-600 hover:text-gray-800"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Consultation Details */}
          {consultationDetails && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h2 className="text-lg font-semibold text-blue-800 mb-4">Consultation Information</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Consultation ID</p>
                  <p className="font-medium">{consultationDetails.id}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Consultation Date</p>
                  <p className="font-medium">{formatDate(consultationDetails.created_at)}</p>
                </div>
                {consultationDetails.patient && (
                  <>
                    <div>
                      <p className="text-sm text-gray-600">Patient Name</p>
                      <p className="font-medium">{consultationDetails.patient.full_name}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Patient Email</p>
                      <p className="font-medium">{consultationDetails.patient.email}</p>
                    </div>
                  </>
                )}
                {consultationDetails.doctor && (
                  <>
                    <div>
                      <p className="text-sm text-gray-600">Doctor Name</p>
                      <p className="font-medium">{consultationDetails.doctor.name}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Doctor Qualifications</p>
                      <p className="font-medium">{consultationDetails.doctor.qualifications || 'N/A'}</p>
                    </div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Prescription List */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-blue-800">Prescriptions</h2>
            <button
              onClick={addPrescription}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition font-medium"
            >
              + Add Prescription
            </button>
          </div>

          {prescriptions.length === 0 ? (
            <p className="text-gray-600 text-center py-8">No prescriptions added yet. Click "Add Prescription" to start.</p>
          ) : (
            <div className="space-y-6">
              {prescriptions.map((prescription, index) => (
                <div key={index} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="font-semibold text-gray-800">Prescription #{index + 1}</h3>
                    <button
                      onClick={() => removePrescription(index)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Remove
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Medicine Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={prescription.name}
                        onChange={(e) => updatePrescription(index, 'name', e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Morning Dosage</label>
                      <select
                        value={prescription.morning_dosage}
                        onChange={(e) => updatePrescription(index, 'morning_dosage', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value={0}>0</option>
                        <option value={1}>1</option>
                        <option value={2}>2</option>
                        <option value={3}>3</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Afternoon Dosage</label>
                      <select
                        value={prescription.afternoon_dosage}
                        onChange={(e) => updatePrescription(index, 'afternoon_dosage', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value={0}>0</option>
                        <option value={1}>1</option>
                        <option value={2}>2</option>
                        <option value={3}>3</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Night Dosage</label>
                      <select
                        value={prescription.night_dosage}
                        onChange={(e) => updatePrescription(index, 'night_dosage', parseInt(e.target.value))}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value={0}>0</option>
                        <option value={1}>1</option>
                        <option value={2}>2</option>
                        <option value={3}>3</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Food Timing</label>
                      <select
                        value={prescription.food_timing}
                        onChange={(e) => updatePrescription(index, 'food_timing', e.target.value)}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="before_food">Before Food</option>
                        <option value="after_food">After Food</option>
                      </select>
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                      <textarea
                        value={prescription.notes}
                        onChange={(e) => updatePrescription(index, 'notes', e.target.value)}
                        rows={2}
                        className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Additional notes for this prescription..."
                      />
                    </div>
                  </div>

                  <div className="mt-4">
                    <button
                      onClick={() => savePrescription(index)}
                      disabled={saving}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition text-sm disabled:bg-gray-400"
                    >
                      {prescription.id ? 'Update' : 'Save'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Generate PDF Button */}
        {prescriptions.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <button
              onClick={generatePrescriptionPDF}
              disabled={saving}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white px-6 py-3 rounded-lg transition font-medium disabled:bg-gray-400"
            >
              {saving ? 'Generating...' : 'Generate Prescription PDF'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default AddPrescription;
